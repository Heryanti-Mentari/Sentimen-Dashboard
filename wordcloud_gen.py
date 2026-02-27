import argparse
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # WAJIB sebelum import pyplot — aman di server tanpa display

import matplotlib.pyplot as plt
from wordcloud import WordCloud

import pandas as pd

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Konstanta ─────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR   = BASE_DIR / "data"
HASIL_CSV  = DATA_DIR / "hasil.csv"
OUTPUT     = STATIC_DIR / "wordcloud.png"

VALID_SENTIMEN = {"positif", "netral", "negatif"}

# Stopwords Bahasa Indonesia — kata umum yang tidak informatif
ID_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "ada", "tidak", "adalah", "saya", "aku", "kamu", "mereka", "kita",
    "kami", "dia", "ya", "sih", "aja", "deh", "dong", "lah", "juga",
    "bisa", "lebih", "sangat", "banget", "tapi", "kalau", "sama",
    "sudah", "udah", "biar", "nih", "nggak", "gak", "ga", "jadi",
    "mau", "apa", "karena", "punya", "lagi", "kayak", "terus", "masih",
    "nya", "saja", "pun", "atau", "oleh", "pada", "dalam", "akan",
    "bukan", "belum", "jangan", "baik", "buat", "emang", "gimana",
    "dong", "yuk", "ayo", "wah", "wow", "oh", "ah", "eh", "si",
}

# ── Fungsi utama ──────────────────────────────────────────────────────────────

def run_wordcloud(sentimen_filter: str | None = None) -> bool:
    """
    Buat word cloud dan simpan ke static/wordcloud.png.

    Parameter
    ---------
    sentimen_filter : jika diisi ("positif"/"netral"/"negatif"),
                      hanya komentar dengan sentimen tersebut yang dipakai.
                      None berarti semua komentar dipakai.

    Kembalikan True jika berhasil.
    """

    # 1. Validasi file
    if not HASIL_CSV.exists():
        logger.error("File tidak ditemukan: %s", HASIL_CSV)
        return False

    # 2. Baca & validasi kolom
    try:
        df = pd.read_csv(HASIL_CSV)
    except Exception as exc:
        logger.error("Gagal membaca CSV: %s", exc)
        return False

    if "komentar" not in df.columns:
        logger.error("Kolom 'komentar' tidak ditemukan di CSV.")
        return False

    # 3. Filter per sentimen jika diminta
    if sentimen_filter:
        sentimen_filter = sentimen_filter.lower().strip()
        if sentimen_filter not in VALID_SENTIMEN:
            logger.error(
                "Sentimen tidak valid: '%s'. Pilihan: %s",
                sentimen_filter, VALID_SENTIMEN,
            )
            return False

        if "sentimen" not in df.columns:
            logger.error("Kolom 'sentimen' tidak ditemukan, tidak bisa filter.")
            return False

        df["sentimen"] = df["sentimen"].str.lower().str.strip()
        df = df[df["sentimen"] == sentimen_filter]
        logger.info("Filter aktif: sentimen = '%s' (%d baris)", sentimen_filter, len(df))

    # 4. Gabungkan teks komentar
    texts = df["komentar"].dropna().astype(str)
    texts = texts[texts.str.strip().str.len() > 0]   # hapus string kosong

    if texts.empty:
        logger.warning("Tidak ada teks komentar yang bisa diproses.")
        return False

    all_text = " ".join(texts)
    logger.info("Total karakter teks: %d dari %d komentar.", len(all_text), len(texts))

    # 5. Buat WordCloud
    try:
        wc = WordCloud(
            width=1000,
            height=480,
            background_color="#1a1d27",
            colormap="RdYlGn",
            stopwords=ID_STOPWORDS,
            max_words=120,
            collocations=False,
            prefer_horizontal=0.85,
        ).generate(all_text)
    except ValueError as exc:
        logger.error("Gagal membuat WordCloud (teks mungkin terlalu pendek): %s", exc)
        return False

    # 6. Simpan
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#1a1d27")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        label = f" — {sentimen_filter.capitalize()}" if sentimen_filter else ""
        ax.set_title(
            f"Word Cloud Komentar JKT48{label}",
            color="#f0f2f8", fontsize=12, fontweight="bold", pad=10,
        )

        fig.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        logger.info("✅ Word Cloud disimpan ke %s", OUTPUT)
        return True
    except Exception as exc:
        logger.error("Gagal menyimpan Word Cloud: %s", exc)
        return False
    finally:
        plt.close(fig)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate word cloud dari komentar sentimen JKT48."
    )
    parser.add_argument(
        "--sentimen",
        type=str,
        default=None,
        choices=["positif", "netral", "negatif"],
        help="Filter komentar berdasarkan sentimen tertentu (default: semua)",
    )
    return parser.parse_args()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args    = parse_args()
    success = run_wordcloud(sentimen_filter=args.sentimen)
    raise SystemExit(0 if success else 1)