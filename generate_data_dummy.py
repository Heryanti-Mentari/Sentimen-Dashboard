import argparse
import csv
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Konstanta ─────────────────────────────────────────────────────────────────

DATA_DIR    = Path(__file__).parent / "data"
OUTPUT_CSV  = DATA_DIR / "hasil.csv"

PLATFORMS   = ["Twitter", "Instagram"]

# Komentar realistis per sentimen — lebih banyak variasi agar model lebih kaya
COMMENTS: dict[str, list[str]] = {
    "positif": [
        "JKT48 keren banget! Performnya selalu memukau setiap kali nonton.",
        "Suka banget sama lagu barunya, earworm seharian!",
        "Vokal mereka makin stabil dan kuat, improvement banget!",
        "Fans JKT48 paling solid, komunitas yang luar biasa.",
        "Aku bangga jadi fans JKT48 sejak debut, selalu konsisten kualitasnya.",
        "Koreografinya fresh banget, beda dari lagu-lagu sebelumnya.",
        "Semangat terus ya JKT48, kalian selalu bikin hari lebih cerah!",
        "Outfit handshake event kali ini estetik banget, tim stylist keren!",
        "Live streaming theater semalam kualitasnya jauh meningkat, terima kasih!",
        "Oshi aku masuk senbatsu untuk pertama kalinya, terharu banget nangis 😭❤️",
        "Anniversary concert kemarin best concert sepanjang masa, energi luar biasa!",
        "Kolaborasi brand JKT48 kali ini kece banget, proud banget!",
        "Meet and greet tadi menyenangkan sekali, member-nya ramah dan hangat.",
        "Single ke-30 beneran banger, langsung masuk playlist harian.",
        "JKT48 buktiin lagi kalau mereka layak ada di industri musik Indonesia!",
    ],
    "netral": [
        "Biasa aja sih menurut aku, nggak terlalu excited.",
        "Gak terlalu suka tapi gak benci juga, netral aja.",
        "Lagu itu lumayan, tapi bisa lebih baik menurut selera aku.",
        "Performance standar, sesuai ekspektasi yang sudah ada.",
        "Tonton karena penasaran, hasilnya ya begitu deh.",
        "Jadwal senbatsu untuk single berikutnya belum diumumkan resmi.",
        "Theater JKT48 tutup sementara untuk renovasi selama dua minggu.",
        "Single baru sudah tersedia di semua platform streaming hari ini.",
        "Foto behind the scene event sudah diupload ke akun resmi.",
        "Line-up anniversary tahun ini cukup padat dengan berbagai kegiatan.",
        "Member baru sudah mulai aktif di media sosial resmi mereka.",
        "Informasi harga merchandise belum ada update dari pihak manajemen.",
        "Jadwal handshake event bulan depan masih dalam konfirmasi panitia.",
        "Setlist malam ini sama seperti show sebelumnya, tidak ada perubahan.",
        "Streaming concert online tersedia bagi yang tidak bisa hadir langsung.",
    ],
    "negatif": [
        "Agak mengecewakan sih performnya, ekspektasi aku lebih tinggi dari ini.",
        "Lagu itu nggak catchy sama sekali, susah masuk ke telinga.",
        "Suara kurang stabil di bagian live, perlu lebih banyak latihan.",
        "Kualitas video MV-nya kurang oke untuk standar 2025 ini.",
        "Nggak suka sama konsep album ini, terlalu jauh dari identitas awal.",
        "Fansnya kadang toxic di Twitter, bikin nggak nyaman diskusi.",
        "Tiket sold out dalam 5 menit, sistem pembelian benar-benar mengecewakan.",
        "Harga tiket terus naik tiap tahun, sudah tidak terjangkau untuk fans biasa.",
        "Sound system di venue sangat buruk, suara member tidak terdengar jelas.",
        "Merchandise yang dikirim rusak, packaging tidak aman sama sekali.",
        "Respon customer service sangat lambat, sudah 3 hari belum ada balasan.",
        "Manajemen perlu lebih transparan soal keputusan-keputusan penting.",
        "Kurang greget tampilannya dibanding grup idol lain yang rilis bulan ini.",
        "Setiap kali nonton live selalu ada teknis yang bermasalah, kapan diperbaiki?",
        "Aku kecewa sama keputusan lineup senbatsu kali ini, tidak adil rasanya.",
    ],
}

# Distribusi sentimen default: 50% berlabel, 50% tanpa label (untuk diklasifikasi)
# Di antara yang berlabel: ~50% positif, ~30% netral, ~20% negatif
DEFAULT_LABELED_RATIO  = 0.55    # proporsi baris yang sudah punya label
DEFAULT_SENTIMENT_DIST = {"positif": 0.50, "netral": 0.30, "negatif": 0.20}

# ── Core functions ────────────────────────────────────────────────────────────

def random_date(start: datetime, end: datetime, rng: random.Random) -> str:
    """Hasilkan tanggal acak antara start dan end (format YYYY-MM-DD)."""
    delta_days = (end - start).days
    if delta_days <= 0:
        return start.strftime("%Y-%m-%d")
    return (start + timedelta(days=rng.randrange(delta_days))).strftime("%Y-%m-%d")


def generate_data(
    num: int = 150,
    start_date: datetime = datetime(2025, 5, 1),
    end_date: datetime   = datetime(2025, 7, 31),
    labeled_ratio: float = DEFAULT_LABELED_RATIO,
    sentiment_dist: dict[str, float] = DEFAULT_SENTIMENT_DIST,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Buat DataFrame data dummy sentimen JKT48.

    Parameter
    ---------
    num           : jumlah baris yang dihasilkan
    start_date    : tanggal terkecil untuk kolom tanggal
    end_date      : tanggal terbesar untuk kolom tanggal
    labeled_ratio : proporsi baris yang sudah memiliki label sentimen (0–1)
    sentiment_dist: distribusi antar label sentimen (harus berjumlah 1.0)
    seed          : seed untuk reproduktibilitas (None = acak)
    """
    rng = random.Random(seed)

    # Normalisasi distribusi agar total = 1
    total_dist = sum(sentiment_dist.values())
    norm_dist  = {k: v / total_dist for k, v in sentiment_dist.items()}
    labels     = list(norm_dist.keys())
    weights    = [norm_dist[l] for l in labels]

    rows = []
    for _ in range(num):
        platform = rng.choice(PLATFORMS)
        date     = random_date(start_date, end_date, rng)
        likes    = rng.randint(0, 1500)

        # Tentukan apakah baris ini punya label atau tidak
        has_label = rng.random() < labeled_ratio

        if has_label:
            sentiment = rng.choices(labels, weights=weights, k=1)[0]
            comment   = rng.choice(COMMENTS[sentiment])
        else:
            # Baris tanpa label: komentar diambil acak dari semua kelas
            all_comments = [c for lst in COMMENTS.values() for c in lst]
            comment   = rng.choice(all_comments)
            sentiment = None   # NaN di CSV — akan diklasifikasi oleh classify_sentimen.py

        rows.append({
            "tanggal":  date,
            "platform": platform,
            "komentar": comment,
            "likes":    likes,
            "sentimen": sentiment,   # None → NaN di DataFrame
        })

    df = pd.DataFrame(rows, columns=["tanggal", "platform", "komentar", "likes", "sentimen"])
    return df


def save_csv(df: pd.DataFrame, output_path: Path = OUTPUT_CSV) -> bool:
    """
    Simpan DataFrame ke CSV.
    Sentimen None/NaN disimpan sebagai string kosong agar mudah dibaca.
    Kembalikan True jika berhasil.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(
            output_path,
            index=False,
            quoting=csv.QUOTE_ALL,
            encoding="utf-8",
            na_rep="",     # NaN → string kosong di CSV
        )
        labeled   = df["sentimen"].notna().sum()
        unlabeled = df["sentimen"].isna().sum()
        logger.info(
            "✅ %s berhasil dibuat — %d baris total "
            "(%d berlabel, %d tanpa label untuk klasifikasi).",
            output_path, len(df), labeled, unlabeled,
        )
        logger.info(
            "   Distribusi label: %s",
            df["sentimen"].value_counts().to_dict(),
        )
        return True
    except Exception as exc:
        logger.error("Gagal menyimpan CSV: %s", exc)
        return False


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate data dummy sentimen JKT48."
    )
    parser.add_argument(
        "-n", "--num",
        type=int, default=150,
        help="Jumlah baris data yang dihasilkan (default: 150)",
    )
    parser.add_argument(
        "--start",
        type=str, default="2025-05-01",
        help="Tanggal mulai format YYYY-MM-DD (default: 2025-05-01)",
    )
    parser.add_argument(
        "--end",
        type=str, default="2025-07-31",
        help="Tanggal akhir format YYYY-MM-DD (default: 2025-07-31)",
    )
    parser.add_argument(
        "--labeled-ratio",
        type=float, default=DEFAULT_LABELED_RATIO,
        help="Proporsi baris yang sudah berlabel (0.0–1.0, default: 0.55)",
    )
    parser.add_argument(
        "--seed",
        type=int, default=42,
        help="Random seed untuk reproduktibilitas (default: 42)",
    )
    parser.add_argument(
        "--output",
        type=str, default=str(OUTPUT_CSV),
        help=f"Path output CSV (default: {OUTPUT_CSV})",
    )
    return parser.parse_args()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()

    try:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        end   = datetime.strptime(args.end,   "%Y-%m-%d")
    except ValueError as exc:
        logger.error("Format tanggal tidak valid: %s", exc)
        raise SystemExit(1)

    if start >= end:
        logger.error("Tanggal mulai harus sebelum tanggal akhir.")
        raise SystemExit(1)

    if not (0.0 < args.labeled_ratio <= 1.0):
        logger.error("--labeled-ratio harus antara 0.0 dan 1.0.")
        raise SystemExit(1)

    df = generate_data(
        num=args.num,
        start_date=start,
        end_date=end,
        labeled_ratio=args.labeled_ratio,
        seed=args.seed,
    )

    success = save_csv(df, Path(args.output))
    raise SystemExit(0 if success else 1)