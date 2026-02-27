import csv
import logging
import re
import shutil
import string
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Konstanta ─────────────────────────────────────────────────────────────────

DATA_DIR      = Path(__file__).parent / "data"
HASIL_CSV     = DATA_DIR / "hasil.csv"
BACKUP_CSV    = DATA_DIR / "hasil_backup.csv"

# Label sentimen yang diizinkan
VALID_LABELS  = {"positif", "netral", "negatif"}

# Kolom wajib ada di CSV
REQUIRED_COLS = {"komentar", "sentimen"}

# Jumlah minimum data latih agar model layak dipakai
MIN_TRAIN_ROWS = 10

# ── Preprocessing ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Bersihkan teks komentar dari noise umum media sosial.
    Urutan pembersihan penting — jangan diubah sembarangan.
    """
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|https\S+", " ", text, flags=re.MULTILINE)  # URL
    text = re.sub(r"@\w+", " ", text)          # mention (@username)
    text = re.sub(r"#\w+", " ", text)           # hashtag
    text = re.sub(r"\d+", " ", text)            # angka
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # karakter non-ASCII (emoji, dll)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()    # spasi ganda
    return text

# ── Fungsi utama ──────────────────────────────────────────────────────────────

def run_classifier() -> bool:
    """
    Jalankan pipeline klasifikasi sentimen.
    Kembalikan True jika berhasil, False jika gagal.
    """

    # 1. Pastikan file CSV ada
    if not HASIL_CSV.exists():
        logger.error("File tidak ditemukan: %s", HASIL_CSV)
        return False

    # 2. Baca CSV
    try:
        df = pd.read_csv(HASIL_CSV)
    except Exception as exc:
        logger.error("Gagal membaca CSV: %s", exc)
        return False

    # 3. Validasi kolom wajib
    missing_cols = REQUIRED_COLS - set(df.columns)
    if missing_cols:
        logger.error("Kolom wajib tidak ditemukan: %s", missing_cols)
        return False

    # 4. Normalisasi label sentimen yang sudah ada
    df["sentimen"] = df["sentimen"].str.lower().str.strip()

    # Tandai label yang tidak valid sebagai NaN (akan diklasifikasi ulang)
    invalid_mask = df["sentimen"].notna() & ~df["sentimen"].isin(VALID_LABELS)
    if invalid_mask.sum() > 0:
        logger.warning(
            "%d baris memiliki label sentimen tidak valid dan akan diklasifikasi ulang: %s",
            invalid_mask.sum(),
            df.loc[invalid_mask, "sentimen"].unique().tolist(),
        )
        df.loc[invalid_mask, "sentimen"] = None

    # 5. Pisahkan data latih dan data uji
    train_df = df[df["sentimen"].notna()].copy()
    test_df  = df[df["sentimen"].isna()].copy()

    logger.info("Data latih: %d baris | Data uji: %d baris", len(train_df), len(test_df))

    if len(train_df) < MIN_TRAIN_ROWS:
        logger.error(
            "Data latih terlalu sedikit (%d baris). Minimum %d baris diperlukan.",
            len(train_df), MIN_TRAIN_ROWS,
        )
        return False

    if len(test_df) == 0:
        logger.info("Tidak ada data uji — semua komentar sudah memiliki label.")
        return True

    # 6. Bersihkan teks
    train_df = train_df.assign(komentar=train_df["komentar"].apply(clean_text))
    test_df  = test_df.assign(komentar=test_df["komentar"].apply(clean_text))

    # Hapus baris dengan komentar kosong setelah cleaning
    train_df = train_df[train_df["komentar"].str.len() > 0]
    if len(train_df) == 0:
        logger.error("Semua teks latih kosong setelah preprocessing.")
        return False

    # 7. Bangun pipeline — TF-IDF lebih baik dari CountVectorizer untuk teks pendek
    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),     # unigram + bigram
            min_df=2,               # abaikan token yang sangat jarang
            max_df=0.95,            # abaikan token yang terlalu umum
            sublinear_tf=True,      # log normalization
        )),
        ("nb", MultinomialNB(alpha=0.5)),
    ])

    # 8. Evaluasi model dengan cross-validation (jika data cukup)
    n_classes = train_df["sentimen"].nunique()
    if len(train_df) >= 30 and n_classes >= 2:
        cv_folds = min(5, len(train_df) // n_classes)
        try:
            cv_scores = cross_val_score(
                model,
                train_df["komentar"],
                train_df["sentimen"],
                cv=cv_folds,
                scoring="accuracy",
            )
            logger.info(
                "Cross-validation (%d-fold) akurasi: %.2f%% ± %.2f%%",
                cv_folds,
                cv_scores.mean() * 100,
                cv_scores.std() * 100,
            )
        except Exception as exc:
            logger.warning("Cross-validation dilewati: %s", exc)
    else:
        logger.warning(
            "Data latih terlalu sedikit untuk cross-validation (%d baris, %d kelas).",
            len(train_df), n_classes,
        )

    # 9. Latih model dengan semua data latih
    model.fit(train_df["komentar"], train_df["sentimen"])

    # Cetak feature importance (top kata per kelas) untuk inspeksi
    _log_top_features(model)

    # 10. Prediksi data uji
    predicted = model.predict(test_df["komentar"])
    logger.info("Distribusi prediksi: %s", pd.Series(predicted).value_counts().to_dict())

    # 11. Backup CSV sebelum overwrite
    try:
        shutil.copy2(HASIL_CSV, BACKUP_CSV)
        logger.info("Backup disimpan ke: %s", BACKUP_CSV)
    except Exception as exc:
        logger.warning("Gagal membuat backup: %s", exc)

    # 12. Simpan hasil ke CSV
    df.loc[df["sentimen"].isna(), "sentimen"] = predicted
    try:
        df.to_csv(HASIL_CSV, index=False, quoting=csv.QUOTE_ALL)
        logger.info("✅ Klasifikasi selesai. %d komentar diberi label baru.", len(test_df))
    except Exception as exc:
        logger.error("Gagal menyimpan hasil ke CSV: %s", exc)
        # Coba restore backup
        if BACKUP_CSV.exists():
            shutil.copy2(BACKUP_CSV, HASIL_CSV)
            logger.info("CSV dikembalikan dari backup.")
        return False

    return True


def _log_top_features(model: Pipeline, top_n: int = 8) -> None:
    """Cetak kata-kata paling berpengaruh per kelas ke log (opsional, untuk debugging)."""
    try:
        vectorizer = model.named_steps["tfidf"]
        classifier = model.named_steps["nb"]
        feature_names = vectorizer.get_feature_names_out()

        logger.info("── Top %d fitur per kelas ──", top_n)
        for i, cls in enumerate(classifier.classes_):
            top_indices = classifier.feature_log_prob_[i].argsort()[-top_n:][::-1]
            top_words   = [feature_names[j] for j in top_indices]
            logger.info("  %-10s → %s", cls, ", ".join(top_words))
    except Exception:
        pass  # Fitur ini opsional, jangan sampai crash proses utama


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    success = run_classifier()
    raise SystemExit(0 if success else 1)