import csv
import logging
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Path ──────────────────────────────────────────────────────────────────────

DATA_DIR  = Path(__file__).parent / "data"
HASIL_CSV = DATA_DIR / "hasil.csv"

# ── Data dummy ────────────────────────────────────────────────────────────────

DUMMY_COMMENTS = {
    "positif": [
        "Outfit JKT48 di event ini keren banget, suka sama konsepnya!",
        "Foto behind the scene selalu ditunggu-tunggu, terima kasih tim!",
        "Senang banget lihat member makin berkembang setiap penampilannya.",
        "JKT48 selalu bikin hari jadi lebih semangat, love you all! 💕",
        "Meet and greet tadi menyenangkan sekali, member-nya ramah dan hangat.",
        "Kualitas konten Instagram makin bagus, estetik dan informatif!",
        "Anniversary post-nya cantik banget, tim kreatif keren!",
        "Oshi masuk cover single baru, bangga banget sama pencapaiannya!",
    ],
    "netral": [
        "Kontennya informatif, tapi desain postingan bisa lebih baik lagi.",
        "Jadwal handshake event bulan depan masih dalam konfirmasi panitia.",
        "Member baru sudah mulai aktif di media sosial resmi mereka.",
        "Informasi harga merchandise belum ada update dari pihak manajemen.",
        "Setlist malam ini sama seperti show sebelumnya, tidak ada perubahan.",
        "Line-up anniversary tahun ini cukup padat dengan berbagai kegiatan.",
        "Streaming concert online tersedia bagi yang tidak bisa hadir langsung.",
    ],
    "negatif": [
        "Harga merchandise makin mahal, susah beli buat fans biasa.",
        "Respon CS-nya lambat banget, komplain dari kemarin belum dibalas.",
        "Foto yang diupload resolusinya kurang, harusnya bisa lebih tajam.",
        "Caption postingan sering ada typo, mohon lebih teliti sebelum upload.",
        "Merchandise yang dikirim rusak, packaging tidak aman sama sekali.",
        "Nggak suka sama konsep album ini, terlalu jauh dari identitas awal.",
    ],
    "": [  # tanpa label — untuk diklasifikasi oleh classify_sentimen.py
        "Baru pertama kali lihat konten JKT48 di Instagram, lumayan menarik.",
        "Sudah follow akun resminya dari lama tapi baru aktif interaksi.",
        "Penasaran sama program baru yang diteaser kemarin di stories.",
        "Caption-nya cukup relatable untuk fans yang sudah lama mengikuti.",
        "Foto groupnya kompak, chemistry member kelihatan banget.",
    ],
}


def _random_date(days_back: int = 60) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


def _build_dummy_rows(n: int = 30) -> list[list]:
    """Buat N baris data dummy Instagram."""
    rows = []
    all_sentimen = list(DUMMY_COMMENTS.keys())

    for _ in range(n):
        sentimen = random.choices(
            all_sentimen,
            weights=[4, 2, 2, 2],   # positif lebih dominan, sebagian tanpa label
            k=1
        )[0]
        comment = random.choice(DUMMY_COMMENTS[sentimen])
        rows.append([
            _random_date(),
            "Instagram",
            comment,
            random.randint(10, 900),
            sentimen,
        ])
    return rows


def _load_existing() -> pd.DataFrame:
    if HASIL_CSV.exists():
        try:
            return pd.read_csv(HASIL_CSV)
        except Exception as exc:
            logger.warning("Gagal membaca CSV lama: %s", exc)
    return pd.DataFrame(columns=["tanggal", "platform", "komentar", "likes", "sentimen"])


def _save(df: pd.DataFrame) -> bool:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(HASIL_CSV, index=False, quoting=csv.QUOTE_ALL, encoding="utf-8")
        return True
    except Exception as exc:
        logger.error("Gagal menyimpan CSV: %s", exc)
        return False


def _merge_and_dedup(existing: pd.DataFrame, new_rows: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([existing, new_rows], ignore_index=True)
    before   = len(combined)
    combined = combined.drop_duplicates(subset=["komentar"], keep="first")
    dupes    = before - len(combined)
    if dupes:
        logger.info("Dihapus %d duplikat komentar.", dupes)
    return combined


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def run_scraper() -> bool:
    logger.info("Memulai scraping Instagram (mode dummy)...")

    rows     = _build_dummy_rows(n=30)
    df_new   = pd.DataFrame(rows, columns=["tanggal", "platform", "komentar", "likes", "sentimen"])
    existing = _load_existing()
    combined = _merge_and_dedup(existing, df_new)

    ok = _save(combined)
    if ok:
        new_count = len(combined) - len(existing)
        logger.info(
            "✅ Instagram dummy — %d komentar baru ditambahkan. Total: %d baris.",
            max(new_count, 0), len(combined),
        )
    return ok


if __name__ == "__main__":
    success = run_scraper()
    raise SystemExit(0 if success else 1)