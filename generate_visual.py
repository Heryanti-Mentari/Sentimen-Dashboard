import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # WAJIB sebelum import pyplot — agar aman di server tanpa display

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from wordcloud import WordCloud

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Konstanta ─────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
STATIC_DIR  = BASE_DIR / "static"
DATA_DIR    = BASE_DIR / "data"
HASIL_CSV   = DATA_DIR / "hasil.csv"

# Urutan & warna sentimen yang konsisten di semua chart
SENTIMENT_ORDER  = ["positif", "netral", "negatif"]
SENTIMENT_COLORS = {
    "positif": "#34d399",
    "netral":  "#facc15",
    "negatif": "#f87171",
}

# Stopwords Bahasa Indonesia — kata-kata ini diabaikan oleh WordCloud
ID_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "ada", "tidak", "adalah", "saya", "aku", "kamu", "mereka", "kita",
    "kami", "dia", "ya", "sih", "aja", "deh", "dong", "lah", "juga",
    "bisa", "lebih", "sangat", "banget", "tapi", "kalau", "sama",
    "sudah", "sudah", "udah", "biar", "nih", "nggak", "gak", "ga",
    "jadi", "mau", "apa", "karena", "punya", "lagi", "kayak", "terus",
    "masih", "nya", "saja", "pun", "atau", "oleh", "pada", "dalam",
    "akan", "bukan", "belum", "jangan", "baik", "buat", "emang",
}

# Matplotlib style global
plt.rcParams.update({
    "figure.facecolor":  "#1a1d27",
    "axes.facecolor":    "#22263a",
    "axes.edgecolor":    "#2e3348",
    "axes.labelcolor":   "#8892b0",
    "axes.titlecolor":   "#f0f2f8",
    "xtick.color":       "#8892b0",
    "ytick.color":       "#8892b0",
    "grid.color":        "#2e3348",
    "grid.linestyle":    "--",
    "grid.alpha":        0.6,
    "legend.facecolor":  "#22263a",
    "legend.edgecolor":  "#2e3348",
    "legend.labelcolor": "#f0f2f8",
    "font.family":       "DejaVu Sans",
    "font.size":         10,
})

# ── Helper ────────────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame | None:
    """Baca dan validasi hasil.csv. Return None jika gagal."""
    if not HASIL_CSV.exists():
        logger.error("File tidak ditemukan: %s", HASIL_CSV)
        return None

    try:
        df = pd.read_csv(HASIL_CSV)
    except Exception as exc:
        logger.error("Gagal membaca CSV: %s", exc)
        return None

    required = {"tanggal", "komentar", "sentimen"}
    missing  = required - set(df.columns)
    if missing:
        logger.error("Kolom wajib tidak ditemukan: %s", missing)
        return None

    # Normalisasi
    df["sentimen"] = df["sentimen"].str.lower().str.strip()
    df["tanggal"]  = pd.to_datetime(df["tanggal"], errors="coerce")

    rows_before = len(df)
    df = df[df["sentimen"].isin(SENTIMENT_ORDER)]  # filter hanya sentimen valid & berlabel
    dropped = rows_before - len(df)
    if dropped:
        logger.info("Melewati %d baris tanpa label / label tidak valid.", dropped)

    if df.empty:
        logger.warning("Tidak ada data berlabel setelah filtering.")
        return None

    return df


def _save(fig: plt.Figure, path: Path, label: str) -> bool:
    """Simpan figure ke path. Return True jika berhasil."""
    try:
        fig.savefig(path, dpi=150, bbox_inches="tight")
        logger.info("✅ %s → %s", label, path)
        return True
    except Exception as exc:
        logger.error("Gagal menyimpan %s: %s", label, exc)
        return False
    finally:
        plt.close(fig)


# ── Chart generators ──────────────────────────────────────────────────────────

def make_wordcloud(df: pd.DataFrame) -> bool:
    """Buat Word Cloud dari kolom komentar."""
    texts = df["komentar"].dropna().astype(str)
    if texts.empty:
        logger.warning("Kolom komentar kosong, WordCloud dilewati.")
        return False

    text = " ".join(texts)

    try:
        wc = WordCloud(
            width=1000,
            height=480,
            background_color="#1a1d27",
            colormap="RdYlGn",
            stopwords=ID_STOPWORDS,
            max_words=120,
            collocations=False,       # hindari duplikat bigram
            prefer_horizontal=0.85,
        ).generate(text)

        out = STATIC_DIR / "wordcloud.png"
        wc.to_file(str(out))
        logger.info("✅ Word Cloud → %s", out)
        return True
    except Exception as exc:
        logger.error("Gagal membuat Word Cloud: %s", exc)
        return False


def make_trend_chart(df: pd.DataFrame) -> bool:
    """Buat grafik tren sentimen harian (line chart)."""
    df_valid = df.dropna(subset=["tanggal"])
    if df_valid.empty:
        logger.warning("Tidak ada data tanggal valid, tren dilewati.")
        return False

    trend = (
        df_valid
        .groupby(["tanggal", "sentimen"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(11, 5))

    for sentiment in SENTIMENT_ORDER:
        if sentiment in trend.columns:
            ax.plot(
                trend.index,
                trend[sentiment],
                label=sentiment.capitalize(),
                color=SENTIMENT_COLORS[sentiment],
                linewidth=2.2,
                marker="o",
                markersize=4,
            )
            # Area fill transparan di bawah garis
            ax.fill_between(
                trend.index,
                trend[sentiment],
                alpha=0.08,
                color=SENTIMENT_COLORS[sentiment],
            )

    ax.set_title("Tren Sentimen Harian", fontsize=13, fontweight="bold", pad=14)
    ax.set_xlabel("Tanggal", labelpad=8)
    ax.set_ylabel("Jumlah Komentar", labelpad=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=35)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.legend(framealpha=0.6)
    ax.grid(True, axis="y")

    return _save(fig, STATIC_DIR / "trend.png", "Grafik Tren")


def make_bar_chart(df: pd.DataFrame) -> bool:
    """Buat bar chart jumlah komentar per sentimen."""
    counts = (
        df["sentimen"]
        .value_counts()
        .reindex(SENTIMENT_ORDER, fill_value=0)
    )
    colors = [SENTIMENT_COLORS[s] for s in counts.index]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        [s.capitalize() for s in counts.index],
        counts.values,
        color=colors,
        width=0.55,
        zorder=3,
    )

    # Label angka di atas setiap bar
    for bar, val in zip(bars, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(val),
            ha="center", va="bottom",
            color="#f0f2f8", fontsize=10, fontweight="bold",
        )

    ax.set_title("Jumlah Sentimen", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Sentimen", labelpad=8)
    ax.set_ylabel("Jumlah Komentar", labelpad=8)
    ax.set_ylim(0, counts.max() * 1.18)
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.grid(True, axis="y", zorder=0)

    return _save(fig, STATIC_DIR / "barChart.png", "Bar Chart")


def make_pie_chart(df: pd.DataFrame) -> bool:
    """Buat pie chart proporsi sentimen."""
    counts = (
        df["sentimen"]
        .value_counts()
        .reindex(SENTIMENT_ORDER, fill_value=0)
    )
    # Hapus slice bernilai 0 agar pie tidak punya irisan kosong
    counts = counts[counts > 0]
    if counts.empty:
        logger.warning("Semua sentimen bernilai 0, Pie Chart dilewati.")
        return False

    colors = [SENTIMENT_COLORS[s] for s in counts.index]

    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=[s.capitalize() for s in counts.index],
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.78,
        wedgeprops={"linewidth": 1.5, "edgecolor": "#1a1d27"},
    )

    for at in autotexts:
        at.set_color("#1a1d27")
        at.set_fontweight("bold")
        at.set_fontsize(10)

    for t in texts:
        t.set_color("#f0f2f8")
        t.set_fontsize(10)

    ax.set_title("Proporsi Sentimen", fontsize=13, fontweight="bold", pad=14)

    return _save(fig, STATIC_DIR / "pieChart.png", "Pie Chart")


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def run_generate_visual() -> dict[str, bool]:
    """
    Jalankan semua generator visual.
    Kembalikan dict status per chart:
      {"wordcloud": True, "trend": True, "bar": True, "pie": False, ...}
    """
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    if df is None:
        return {k: False for k in ("wordcloud", "trend", "bar", "pie")}

    logger.info("Data dimuat: %d baris berlabel dari %s.", len(df), HASIL_CSV)

    results = {
        "wordcloud": make_wordcloud(df),
        "trend":     make_trend_chart(df),
        "bar":       make_bar_chart(df),
        "pie":       make_pie_chart(df),
    }

    success = sum(results.values())
    total   = len(results)
    logger.info("Visual selesai: %d/%d berhasil. Detail: %s", success, total, results)
    return results


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_generate_visual()
    raise SystemExit(0 if all(results.values()) else 1)