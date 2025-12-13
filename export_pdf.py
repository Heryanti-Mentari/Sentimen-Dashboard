from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 16)
        self.cell(0, 10, "Laporan Analisis Sentimen Fanbase JKT48", ln=True, align="C")
        self.ln(10)

    def section_title(self, title):
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, title, ln=True)
        self.ln(4)

    def add_image(self, image_path, w=180):
        self.image(image_path, w=w)
        self.ln(10)

# Inisialisasi PDF
pdf = PDF()
pdf.add_page()

# Bagian Statistik
pdf.section_title("Statistik Visualisasi Sentimen")
pdf.add_image("static/pieChart.png", w=90)
pdf.add_image("static/barChart.png", w=90)

# Grafik Tren
pdf.section_title("Tren Sentimen Harian")
pdf.add_image("static/trend.png")

# Word Cloud
pdf.section_title("Word Cloud Komentar Fanbase")
pdf.add_image("static/wordcloud.png")

# Disclaimer Etika
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, "Data bersifat publik dan telah dianonimkan. Tidak ada identitas personal yang disimpan. Sistem ini dirancang sesuai prinsip etika profesi dan akurasi analitik.")

# Simpan PDF
pdf.output("laporan.pdf")
print("✅ PDF berhasil dibuat: laporan.pdf")
