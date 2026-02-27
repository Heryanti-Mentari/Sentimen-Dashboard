import csv
import logging
import os
import subprocess
from functools import wraps
from pathlib import Path

import pandas as pd
from flask import (Flask, flash, redirect, render_template,
                   request, send_file, session, url_for)

# ── Konfigurasi ───────────────────────────────────────────────────────────────

app = Flask(__name__)

# SECRET_KEY wajib di-set via environment variable sebelum deploy.
# Contoh: export SECRET_KEY="ganti-dengan-string-acak-panjang"
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-ganti-sebelum-deploy")

# Kredensial admin — JANGAN hardcode di sini untuk produksi.
# Set environment variable: ADMIN_USER dan ADMIN_PASS
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

# Path data — semua file CSV berada di dalam folder ini
DATA_DIR = Path(__file__).parent / "data"
HASIL_CSV   = DATA_DIR / "hasil.csv"
LAPORAN_CSV = DATA_DIR / "laporan.csv"
LAPORAN_PDF = Path(__file__).parent / "laporan.pdf"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: redirect ke login jika belum autentikasi."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def load_csv() -> pd.DataFrame:
    """
    Baca hasil.csv dengan penanganan error yang jelas.
    Kembalikan DataFrame kosong jika file tidak ada / rusak.
    """
    if not HASIL_CSV.exists():
        logger.warning("File CSV tidak ditemukan: %s", HASIL_CSV)
        return pd.DataFrame(columns=["tanggal", "platform", "sentimen", "komentar", "likes"])

    try:
        df = pd.read_csv(HASIL_CSV)
        # Normalisasi kolom sentimen & platform ke huruf kecil agar filter konsisten
        if "sentimen" in df.columns:
            df["sentimen"] = df["sentimen"].str.lower().str.strip()
        if "platform" in df.columns:
            df["platform"] = df["platform"].str.strip()
        return df
    except Exception as exc:
        logger.error("Gagal membaca CSV: %s", exc)
        return pd.DataFrame(columns=["tanggal", "platform", "sentimen", "komentar", "likes"])

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    """Halaman login admin."""
    # Jika sudah login, langsung ke dashboard
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Validasi input tidak kosong
        if not username or not password:
            return render_template("login.html", error="Username dan password tidak boleh kosong.")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["logged_in"] = True
            session["username"] = username
            logger.info("Login berhasil: %s", username)
            return redirect(url_for("dashboard"))

        logger.warning("Login gagal untuk username: %s", username)
        return render_template("login.html", error="Login gagal. Username atau password salah.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Hapus session dan kembali ke login."""
    username = session.get("username", "unknown")
    session.clear()
    logger.info("Logout: %s", username)
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    """Halaman utama dashboard dengan filter platform & sentimen."""
    df = load_csv()

    platform_filter = request.args.get("platform", "all")
    sentimen_filter = request.args.get("sentimen", "all")

    # Terapkan filter hanya jika bukan 'all'
    if platform_filter != "all":
        df = df[df["platform"].str.lower() == platform_filter.lower()]
    if sentimen_filter != "all":
        df = df[df["sentimen"] == sentimen_filter.lower()]

    positif = int((df["sentimen"] == "positif").sum())
    netral  = int((df["sentimen"] == "netral").sum())
    negatif = int((df["sentimen"] == "negatif").sum())

    return render_template(
        "dashboard.html",
        positif=positif,
        netral=netral,
        negatif=negatif,
        platform_filter=platform_filter,
        sentimen_filter=sentimen_filter,
    )


@app.route("/detail")
@login_required
def detail():
    """Halaman tabel detail semua komentar."""
    df = load_csv()
    records = df.to_dict(orient="records")
    return render_template("detail.html", data=records)


@app.route("/export/csv")
@login_required
def export_csv():
    """Ekspor data sebagai file CSV."""
    df = load_csv()

    if df.empty:
        flash("Tidak ada data untuk diekspor.", "warning")
        return redirect(url_for("dashboard"))

    try:
        df.to_csv(LAPORAN_CSV, index=False, quoting=csv.QUOTE_ALL)
        logger.info("Ekspor CSV oleh: %s", session.get("username"))
        return send_file(
            str(LAPORAN_CSV),
            as_attachment=True,
            download_name="laporan_sentimen_jkt48.csv",
            mimetype="text/csv",
        )
    except Exception as exc:
        logger.error("Gagal ekspor CSV: %s", exc)
        flash("Gagal mengekspor CSV. Coba lagi.", "error")
        return redirect(url_for("dashboard"))


@app.route("/export/pdf")
@login_required
def export_pdf():
    """Ekspor laporan sebagai PDF."""
    # Jalankan script generator PDF secara terpisah (bukan import dinamis)
    try:
        result = subprocess.run(
            ["python", "export_pdf.py"],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.info("PDF berhasil di-generate: %s", result.stdout.strip())
    except subprocess.TimeoutExpired:
        logger.error("Timeout saat generate PDF")
        flash("Gagal membuat PDF: proses terlalu lama.", "error")
        return redirect(url_for("dashboard"))
    except subprocess.CalledProcessError as exc:
        logger.error("Error generate PDF: %s", exc.stderr)
        flash("Gagal membuat PDF. Lihat log untuk detail.", "error")
        return redirect(url_for("dashboard"))

    if not LAPORAN_PDF.exists():
        flash("File PDF tidak ditemukan setelah proses selesai.", "error")
        return redirect(url_for("dashboard"))

    logger.info("Ekspor PDF oleh: %s", session.get("username"))
    return send_file(
        str(LAPORAN_PDF),
        as_attachment=True,
        download_name="laporan_sentimen_jkt48.pdf",
        mimetype="application/pdf",
    )


@app.route("/update-data")
@login_required
def update_data():
    """Jalankan ulang seluruh pipeline pengumpulan & analisis data."""
    try:
        result = subprocess.run(
            ["python", "run_all.py"],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,          # maks 5 menit
        )
        logger.info("Update data berhasil oleh %s:\n%s",
                    session.get("username"), result.stdout)
        flash("✅ Data berhasil diperbarui.", "success")
    except subprocess.TimeoutExpired:
        logger.error("Update data timeout")
        flash("❌ Update data timeout (> 5 menit). Coba jalankan run_all.py manual.", "error")
    except subprocess.CalledProcessError as exc:
        logger.error("Update data gagal:\n%s", exc.stderr)
        flash(f"❌ Gagal update data: {exc.stderr[:300]}", "error")

    return redirect(url_for("dashboard"))


@app.route("/scrape", methods=["POST"])
@login_required
def scrape():
    """Ambil data baru dari platform yang dipilih."""
    platform = request.form.get("platform", "semua")

    # Whitelist platform yang valid
    ALLOWED_PLATFORMS = {"twitter", "instagram", "semua"}
    if platform not in ALLOWED_PLATFORMS:
        flash("Platform tidak valid.", "error")
        return redirect(url_for("dashboard"))

    script_map = {
        "twitter":   ["python", "scraper_twitter.py"],
        "instagram": ["python", "scraper_instagram.py"],
        "semua":     ["python", "run_all.py"],
    }

    try:
        result = subprocess.run(
            script_map[platform],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        logger.info("Scrape '%s' berhasil oleh %s", platform, session.get("username"))
        flash(f"✅ Data dari {platform.capitalize()} berhasil diambil.", "success")
    except subprocess.TimeoutExpired:
        flash(f"❌ Scraping {platform} timeout. Coba lagi.", "error")
    except subprocess.CalledProcessError as exc:
        logger.error("Scrape '%s' gagal: %s", platform, exc.stderr)
        flash(f"❌ Scraping gagal: {exc.stderr[:200]}", "error")

    return redirect(url_for("dashboard"))


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("Server error: %s", e)
    return render_template("500.html"), 500


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Debug mode hanya untuk development.
    # Di produksi: gunakan gunicorn / waitress, dan set DEBUG=False.
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)