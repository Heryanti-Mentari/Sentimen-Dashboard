"""
export_pdf.py — Generator laporan PDF untuk Dashboard Sentimen JKT48
=====================================================================
Perbaikan dari versi sebelumnya:
  - Kode level modul dipindah ke fungsi generate_pdf() agar bisa di-import
    tanpa langsung menjalankan proses (sebelumnya berbahaya jika di-import)
  - Font Unicode (DejaVu) menggantikan Arial agar karakter non-Latin aman
  - Validasi keberadaan file gambar sebelum di-embed (tidak crash)
  - Baca statistik langsung dari hasil.csv dan tampilkan di PDF
  - Header & footer per halaman (nomor halaman)
  - Semua path pakai pathlib.Path (lintas OS)
  - Logging menggantikan print
  - Return True/False sehingga pemanggil tahu berhasil/gagal
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from fpdf import FPDF

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Path ──────────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
STATIC_DIR  = BASE_DIR / "static"
DATA_DIR    = BASE_DIR / "data"
HASIL_CSV   = DATA_DIR / "hasil.csv"
OUTPUT_PDF  = BASE_DIR / "laporan.pdf"

# ── PDF Class ─────────────────────────────────────────────────────────────────

class LaporanPDF(FPDF):
    """FPDF dengan header, footer, dan helper styling yang konsisten."""

    def __init__(self, generated_at: str):
        super().__init__()
        self.generated_at = generated_at
        self._setup_fonts()

    def _setup_fonts(self):
        """
        Coba daftarkan DejaVu (Unicode) jika tersedia.
        Fallback ke Helvetica (built-in) agar tetap berjalan meski font tidak ada.
        """
        dejavu_path = STATIC_DIR / "fonts"
        regular = dejavu_path / "DejaVuSans.ttf"
        bold    = dejavu_path / "DejaVuSans-Bold.ttf"

        if regular.exists() and bold.exists():
            self.add_font("DejaVu", "",  str(regular), uni=True)
            self.add_font("DejaVu", "B", str(bold),    uni=True)
            self._font_family = "DejaVu"
            logger.info("Font DejaVu dimuat.")
        else:
            self._font_family = "Helvetica"
            logger.warning(
                "Font DejaVu tidak ditemukan di %s — pakai Helvetica. "
                "Karakter non-Latin mungkin tidak tampil benar.",
                dejavu_path,
            )

    # ── FPDF overrides ────────────────────────────────────────────────────────

    def header(self):
        # Garis atas
        self.set_draw_color(232, 68, 90)   # merah JKT48
        self.set_line_width(1.0)
        self.line(10, 8, 200, 8)

        self.set_font(self._font_family, "B", 15)
        self.set_text_color(30, 30, 40)
        self.set_y(12)
        self.cell(0, 8, "Laporan Analisis Sentimen Fanbase JKT48", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_font(self._font_family, "", 9)
        self.set_text_color(140, 140, 160)
        self.cell(0, 6, f"Dibuat: {self.generated_at}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(220, 220, 230)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font(self._font_family, "", 8)
        self.set_text_color(160, 160, 175)
        self.cell(0, 8,
                  f"Halaman {self.page_no()}/{{nb}} - Dashboard Sentimen JKT48",
                  align="C")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def section_title(self, title: str):
        self.set_font(self._font_family, "B", 13)
        self.set_text_color(232, 68, 90)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        # Garis bawah tipis
        x, y = self.get_x(), self.get_y()
        self.set_draw_color(232, 68, 90)
        self.set_line_width(0.4)
        self.line(10, y, 200, y)
        self.ln(5)
        self.set_text_color(30, 30, 40)

    def body_text(self, text: str, line_height: float = 6):
        self.set_font(self._font_family, "", 10)
        self.set_text_color(50, 50, 60)
        self.multi_cell(0, line_height, text)
        self.ln(3)

    def stat_row(self, label: str, value: str, color: tuple = (50, 50, 60)):
        """Satu baris statistik dengan label kiri dan nilai kanan."""
        self.set_font(self._font_family, "", 10)
        self.set_text_color(100, 100, 120)
        self.cell(80, 7, label)
        self.set_font(self._font_family, "B", 10)
        self.set_text_color(*color)
        self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 30, 40)

    def safe_image(self, image_path: Path, w: float = 180, label: str = ""):
        """Tambahkan gambar jika file ada; tampilkan placeholder jika tidak."""
        if image_path.exists():
            try:
                self.image(str(image_path), w=w)
                self.ln(6)
                return
            except Exception as exc:
                logger.warning("Gagal embed gambar %s: %s", image_path, exc)

        # Placeholder teks jika gambar tidak ada
        self.set_font(self._font_family, "", 9)
        self.set_text_color(180, 180, 190)
        placeholder = f"[Gambar tidak tersedia: {image_path.name}]"
        if label:
            placeholder = f"[{label} - file tidak ditemukan: {image_path.name}]"
        self.cell(0, 8, placeholder, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_text_color(30, 30, 40)
        logger.warning("File gambar tidak ditemukan: %s", image_path)


# ── Fungsi utama ──────────────────────────────────────────────────────────────

def generate_pdf() -> bool:
    """
    Buat laporan PDF dan simpan ke OUTPUT_PDF.
    Kembalikan True jika berhasil, False jika gagal.
    """
    generated_at = datetime.now().strftime("%d %B %Y, %H:%M WIB")

    # ── Baca statistik dari CSV ────────────────────────────────────────────
    stats = {"positif": 0, "netral": 0, "negatif": 0, "total": 0}
    platform_counts: dict[str, int] = {}

    if HASIL_CSV.exists():
        try:
            df = pd.read_csv(HASIL_CSV)
            if "sentimen" in df.columns:
                df["sentimen"] = df["sentimen"].str.lower().str.strip()
                stats["positif"] = int((df["sentimen"] == "positif").sum())
                stats["netral"]  = int((df["sentimen"] == "netral").sum())
                stats["negatif"] = int((df["sentimen"] == "negatif").sum())
                stats["total"]   = len(df)
            if "platform" in df.columns:
                platform_counts = df["platform"].value_counts().to_dict()
        except Exception as exc:
            logger.warning("Gagal membaca CSV untuk statistik: %s", exc)
    else:
        logger.warning("CSV tidak ditemukan, statistik akan kosong.")

    pct = lambda n: f"{(n / stats['total'] * 100):.1f}%" if stats["total"] > 0 else "-"

    # ── Buat PDF ──────────────────────────────────────────────────────────
    try:
        pdf = LaporanPDF(generated_at)
        pdf.alias_nb_pages()   # aktifkan {nb} untuk total halaman di footer
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        # ── 1. Ringkasan statistik ─────────────────────────────────────
        pdf.section_title("1. Ringkasan Statistik Sentimen")

        pdf.stat_row("Total komentar dianalisis :", str(stats["total"]))
        pdf.stat_row("Sentimen Positif :",
                     f"{stats['positif']} komentar  ({pct(stats['positif'])})",
                     color=(20, 160, 110))
        pdf.stat_row("Sentimen Netral  :",
                     f"{stats['netral']} komentar  ({pct(stats['netral'])})",
                     color=(180, 140, 0))
        pdf.stat_row("Sentimen Negatif :",
                     f"{stats['negatif']} komentar  ({pct(stats['negatif'])})",
                     color=(200, 60, 60))

        if platform_counts:
            pdf.ln(2)
            for platform, count in platform_counts.items():
                pdf.stat_row(f"  Platform - {platform} :", str(count))

        pdf.ln(4)

        # ── 2. Visualisasi pie & bar chart ────────────────────────────
        pdf.section_title("2. Visualisasi Proporsi & Jumlah Sentimen")

        # Tampilkan pie dan bar berdampingan jika memungkinkan
        pie_path = STATIC_DIR / "pieChart.png"
        bar_path = STATIC_DIR / "barChart.png"

        if pie_path.exists() and bar_path.exists():
            try:
                x_start = pdf.get_x()
                y_start = pdf.get_y()
                pdf.image(str(pie_path), x=12,  y=y_start, w=88)
                pdf.image(str(bar_path), x=108, y=y_start, w=88)
                pdf.ln(72)
            except Exception as exc:
                logger.warning("Gagal embed chart berdampingan: %s", exc)
                pdf.safe_image(pie_path, w=88, label="Pie Chart")
                pdf.safe_image(bar_path, w=88, label="Bar Chart")
        else:
            pdf.safe_image(pie_path, w=88, label="Pie Chart")
            pdf.safe_image(bar_path, w=88, label="Bar Chart")

        # ── 3. Tren harian ────────────────────────────────────────────
        pdf.add_page()
        pdf.section_title("3. Tren Sentimen Harian")
        pdf.safe_image(STATIC_DIR / "trend.png", label="Grafik Tren")

        # ── 4. Word cloud ──────────────────────────────────────────────
        pdf.section_title("4. Word Cloud Komentar Fanbase")
        pdf.safe_image(STATIC_DIR / "wordcloud.png", label="Word Cloud")

        # ── 5. Disclaimer etika ────────────────────────────────────────
        pdf.add_page()
        pdf.section_title("5. Pernyataan Etika & Privasi")
        pdf.body_text(
            "Data yang digunakan dalam laporan ini bersumber dari postingan publik di "
            "media sosial (Twitter/X dan Instagram) dan telah melalui proses anonimisasi "
            "penuh. Tidak ada informasi identitas personal (nama akun, foto profil, atau "
            "data pribadi lainnya) yang disimpan maupun ditampilkan dalam sistem ini.\n\n"
            "Analisis sentimen dilakukan secara otomatis menggunakan model machine learning "
            "dan bersifat indikatif. Hasil klasifikasi dapat mengandung ketidakakuratan "
            "dan tidak dimaksudkan sebagai representasi resmi opini publik.\n\n"
            "Sistem ini dikembangkan sesuai prinsip etika riset digital dan pedoman "
            "perlindungan data pribadi yang berlaku."
        )

        # ── Simpan ────────────────────────────────────────────────────
        pdf.output(str(OUTPUT_PDF))
        logger.info("✅ PDF berhasil dibuat: %s", OUTPUT_PDF)
        return True

    except Exception as exc:
        logger.error("Gagal membuat PDF: %s", exc, exc_info=True)
        return False


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    success = generate_pdf()
    raise SystemExit(0 if success else 1)