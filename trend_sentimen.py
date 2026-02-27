import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # WAJIB sebelum import pyplot — aman di server tanpa display

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
OUTPUT     = STATIC_DIR / "trend.png"

SENTIMENT_ORDER  = ["positif", "netral", "negatif"]
SENTIMENT_COLORS = {
    "positif": "#34d399",
    "netral":  "#facc15",
    "negatif": "#f87171",
}

# Style global konsisten dengan generate_visual.py
plt.rcParams.update({
    "figure.facecolor": "#1a1d27",
    "axes.facecolor":   "#22263a",
    "axes.edgecolor":   "#2e3348",
    "axes.labelcolor":  "#8892b0",
    "axes.titlecolor":  "#f0f2f8",
    "xtick.color":      "#8892b0",
    "ytick.color":      "#8892b0",
    "grid.color":       "#2e3348",
    "grid.linestyle":   "--",
    "grid.alpha":       0.6,
    "legend.facecolor": "#22263a",
    "legend.edgecolor": "#2e3348",
    "legend.labelcolor":"#f0f2f8",
    "font.family":      "DejaVu Sans",
    "font.size":        10,
})

# ── Fungsi utama ──────────────────────────────────────────────────────────────

def run_trend() -> bool:
    """
    Buat grafik tren sentimen harian dan simpan ke static/trend.png.
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

    missing = {"tanggal", "sentimen"} - set(df.columns)
    if missing:
        logger.error("Kolom wajib tidak ditemukan: %s", missing)
        return False

    # 3. Normalisasi & filter hanya data berlabel valid
    df["sentimen"] = df["sentimen"].str.lower().str.strip()
    df["tanggal"]  = pd.to_datetime(df["tanggal"], errors="coerce")

    df = df[
        df["tanggal"].notna() &
        df["sentimen"].isin(SENTIMENT_ORDER)
    ]

    if df.empty:
        logger.warning("Tidak ada data berlabel dengan tanggal valid untuk dibuat tren.")
        return False

    # 4. Hitung jumlah per (tanggal, sentimen)
    trend = (
        df.groupby(["tanggal", "sentimen"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
        .sort_index()
    )

    # 5. Hitung total per hari (untuk anotasi)
    daily_total = trend.sum(axis=1)

    logger.info(
        "Rentang data: %s s/d %s (%d hari)",
        trend.index.min().date(),
        trend.index.max().date(),
        len(trend),
    )

    # 6. Plot
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 5.5))

    for sentiment in SENTIMENT_ORDER:
        if sentiment not in trend.columns or trend[sentiment].sum() == 0:
            continue

        color = SENTIMENT_COLORS[sentiment]
        ax.plot(
            trend.index,
            trend[sentiment],
            label=sentiment.capitalize(),
            color=color,
            linewidth=2.2,
            marker="o",
            markersize=4.5,
            zorder=3,
        )
        ax.fill_between(
            trend.index,
            trend[sentiment],
            alpha=0.10,
            color=color,
            zorder=2,
        )

    # Anotasi total komentar di hari dengan volume tertinggi
    if not daily_total.empty:
        peak_date = daily_total.idxmax()
        peak_val  = daily_total.max()
        ax.annotate(
            f"Puncak: {int(peak_val)} komentar",
            xy=(peak_date, peak_val),
            xytext=(10, 12),
            textcoords="offset points",
            color="#f0f2f8",
            fontsize=8.5,
            fontweight="bold",
            arrowprops={"arrowstyle": "->", "color": "#8892b0", "lw": 1.2},
        )

    # Format sumbu X
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=12))
    fig.autofmt_xdate(rotation=30, ha="right")

    # Format sumbu Y — hanya integer
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.set_ylim(bottom=0)

    ax.set_title("Tren Sentimen Harian — JKT48", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Tanggal", labelpad=8)
    ax.set_ylabel("Jumlah Komentar", labelpad=8)
    ax.legend(loc="upper left", framealpha=0.6)
    ax.grid(True, axis="y")

    # 7. Simpan
    try:
        fig.savefig(OUTPUT, dpi=150, bbox_inches="tight")
        logger.info("✅ Grafik tren disimpan ke %s", OUTPUT)
        return True
    except Exception as exc:
        logger.error("Gagal menyimpan grafik: %s", exc)
        return False
    finally:
        plt.close(fig)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    success = run_trend()
    raise SystemExit(0 if success else 1)