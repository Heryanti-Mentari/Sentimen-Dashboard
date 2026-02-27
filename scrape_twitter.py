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
        "JKT48 keren banget! Penampilan kemarin di konser bikin nangis haru 😭❤️",
        "Stage performance malam ini 10/10, tidak ada yang bisa menandingi energi mereka!",
        "Oshi saya berhasil masuk senbatsu untuk pertama kalinya! Bangga banget!!",
        "Koreografi lagu baru benar-benar segar dan berbeda dari biasanya, suka banget!",
        "Kolaborasi dengan brand lokal ini sungguh keren, proud of JKT48!",
        "Live streaming theater malam ini kualitasnya jauh lebih baik dari sebelumnya!",
        "Anniversary concert kemarin adalah yang terbaik sepanjang masa! Terima kasih JKT48 🎉",
        "Single baru ini beneran banger, langsung masuk playlist harian aku!",
        "Vokal member makin stabil dan kuat, improvement yang sangat terasa!",
    ],
    "netral": [
        "Jadwal senbatsu untuk single berikutnya belum diumumkan secara resmi.",
        "Theater JKT48 tutup sementara untuk renovasi selama dua minggu ke depan.",
        "Single baru sudah tersedia di semua platform streaming mulai hari ini.",
        "Line-up event anniversary JKT48 tahun ini sangat padat dan beragam.",
        "Member baru sudah mulai aktif di media sosial sejak pengumuman kemarin.",
        "Setlist malam ini tidak berbeda jauh dari show minggu lalu.",
        "Info tiket konser sudah bisa dicek di website resmi mulai besok.",
    ],
    "negatif": [
        "Tiket sold out dalam 5 menit, sistem pembeliannya benar-benar mengecewakan.",
        "Sound system di venue sangat buruk, suara member tidak terdengar jelas sama sekali.",
        "Kenapa harga tiket terus naik? Sudah tidak terjangkau untuk fans biasa seperti kami.",
        "Fansnya kadang toxic di Twitter, bikin nggak nyaman diskusi soal JKT48.",
        "Manajemen perlu lebih transparan soal keputusan-keputusan penting yang dibuat.",
        "Setiap kali nonton live selalu ada teknis yang bermasalah, kapan diperbaiki?",
        "Kecewa sama keputusan lineup senbatsu kali ini, rasanya tidak adil.",
    ],
    "": [  # tanpa label — untuk diklasifikasi oleh classify_sentimen.py
        "Baru pertama kali nonton JKT48 live, penasaran sama suasana langsung.",
        "Tadi lewat venue tempat konser JKT48, ramai juga ternyata.",
        "Lihat trending JKT48 di Twitter, jadi ikutan cari tahu lebih lanjut.",
        "Teman ngajak nonton handshake event minggu depan, masih mikir-mikir.",
        "Baru tahu JKT48 punya theater sendiri, unik juga konsepnya.",
    ],
}


def _random_date(days_back: int = 60) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


def _build_dummy_rows(n: int = 30) -> list[list]:
    """Buat N baris data dummy Twitter."""
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
            "Twitter",
            comment,
            random.randint(0, 1500),
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
    logger.info("Memulai scraping Twitter (mode dummy)...")

    rows     = _build_dummy_rows(n=30)
    df_new   = pd.DataFrame(rows, columns=["tanggal", "platform", "komentar", "likes", "sentimen"])
    existing = _load_existing()
    combined = _merge_and_dedup(existing, df_new)

    ok = _save(combined)
    if ok:
        new_count = len(combined) - len(existing)
        logger.info(
            "✅ Twitter dummy — %d tweet baru ditambahkan. Total: %d baris.",
            max(new_count, 0), len(combined),
        )
    return ok


if __name__ == "__main__":
    success = run_scraper()
    raise SystemExit(0 if success else 1)