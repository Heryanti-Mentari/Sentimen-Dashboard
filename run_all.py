import argparse
import logging
import time
from datetime import datetime

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Import modul pipeline ─────────────────────────────────────────────────────
# Masing-masing diimport dalam try/except agar error "module not found"
# langsung jelas dan tidak menghentikan modul lain yang ada.

def _try_import(module_name: str):
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as exc:
        logger.warning("Modul '%s' tidak ditemukan: %s", module_name, exc)
        return None

# ── Step runner ───────────────────────────────────────────────────────────────

def run_step(label: str, func, critical: bool = True) -> bool:
    """
    Jalankan satu step pipeline.

    Parameter
    ---------
    label    : nama step untuk log
    func     : callable yang dipanggil (harus return True/False atau None)
    critical : jika True, pipeline harus berhenti ketika step ini gagal

    Return True jika step berhasil.
    """
    logger.info("━━ Mulai: %s ━━", label)
    t0 = time.perf_counter()

    try:
        result = func()
        # Fungsi yang return None dianggap berhasil (backward-compatible)
        success = result is not False
    except Exception as exc:
        logger.error("❌ %s gagal dengan exception: %s", label, exc, exc_info=True)
        success = False

    elapsed = time.perf_counter() - t0
    status  = "✅ Selesai" if success else "❌ Gagal"
    logger.info("%s: %s (%.1f detik)", status, label, elapsed)
    return success

# ── Pipeline utama ────────────────────────────────────────────────────────────

def main(
    skip_twitter:   bool = False,
    skip_instagram: bool = False,
    skip_classify:  bool = False,
    skip_visual:    bool = False,
) -> bool:
    """
    Jalankan pipeline lengkap.
    Kembalikan True jika semua step kritis berhasil.
    """
    start_time = time.perf_counter()
    started_at = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    logger.info("═══════════════════════════════════════")
    logger.info("  Pipeline JKT48 Sentiment — %s", started_at)
    logger.info("═══════════════════════════════════════")

    results: dict[str, bool | None] = {}

    # ── 1. Scraping Twitter ────────────────────────────────────────────────
    if not skip_twitter:
        mod = _try_import("scrape_twitter")
        if mod and hasattr(mod, "run_scraper"):
            # Scraper TIDAK critical — boleh gagal, data lama masih bisa dipakai
            results["scrape_twitter"] = run_step(
                "Scraping Twitter/X", mod.run_scraper, critical=False
            )
        else:
            logger.warning("Scraper Twitter tidak tersedia, step dilewati.")
            results["scrape_twitter"] = None
    else:
        logger.info("⏭ Skip: Scraping Twitter")
        results["scrape_twitter"] = None

    # ── 2. Scraping Instagram ──────────────────────────────────────────────
    if not skip_instagram:
        mod = _try_import("scrape_instagram")
        if mod and hasattr(mod, "run_scraper"):
            results["scrape_instagram"] = run_step(
                "Scraping Instagram", mod.run_scraper, critical=False
            )
        else:
            logger.warning("Scraper Instagram tidak tersedia, step dilewati.")
            results["scrape_instagram"] = None
    else:
        logger.info("⏭ Skip: Scraping Instagram")
        results["scrape_instagram"] = None

    # ── 3. Klasifikasi sentimen ────────────────────────────────────────────
    if not skip_classify:
        mod = _try_import("classify_sentimen")
        if mod and hasattr(mod, "run_classifier"):
            ok = run_step("Klasifikasi Sentimen", mod.run_classifier, critical=True)
            results["classify"] = ok
            if not ok:
                logger.error(
                    "Klasifikasi sentimen gagal. Pipeline dihentikan — "
                    "visualisasi tidak akan dijalankan."
                )
                _print_summary(results, start_time)
                return False
        else:
            logger.error("Modul classify_sentimen tidak tersedia. Pipeline dihentikan.")
            _print_summary(results, start_time)
            return False
    else:
        logger.info("⏭ Skip: Klasifikasi Sentimen")
        results["classify"] = None

    # ── 4. Generate visualisasi ────────────────────────────────────────────
    if not skip_visual:
        mod = _try_import("generate_visual")
        if mod and hasattr(mod, "run_generate_visual"):
            ok = run_step("Generate Visualisasi", mod.run_generate_visual, critical=True)
            results["visual"] = ok
            if not ok:
                logger.error("Generate visualisasi gagal.")
        else:
            logger.error("Modul generate_visual tidak tersedia.")
            results["visual"] = False
    else:
        logger.info("⏭ Skip: Generate Visualisasi")
        results["visual"] = None

    _print_summary(results, start_time)

    # Pipeline berhasil jika semua step yang dijalankan (bukan None) berhasil
    critical_results = [v for v in results.values() if v is not None]
    return all(critical_results)


def _print_summary(results: dict, start_time: float) -> None:
    """Cetak ringkasan hasil seluruh pipeline."""
    total = time.perf_counter() - start_time
    logger.info("═══════════════════════════════════════")
    logger.info("  Ringkasan Pipeline")
    logger.info("───────────────────────────────────────")

    labels = {
        "scrape_twitter":   "Scraping Twitter/X",
        "scrape_instagram": "Scraping Instagram",
        "classify":         "Klasifikasi Sentimen",
        "visual":           "Generate Visualisasi",
    }

    for key, label in labels.items():
        val = results.get(key)
        if val is None:
            icon = "⏭"
            status = "dilewati"
        elif val:
            icon = "✅"
            status = "berhasil"
        else:
            icon = "❌"
            status = "GAGAL"
        logger.info("  %s  %-26s %s", icon, label, status)

    logger.info("───────────────────────────────────────")
    logger.info("  Total waktu: %.1f detik", total)
    logger.info("═══════════════════════════════════════")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jalankan pipeline lengkap sentimen JKT48."
    )
    parser.add_argument(
        "--skip-twitter", action="store_true",
        help="Lewati step scraping Twitter/X"
    )
    parser.add_argument(
        "--skip-instagram", action="store_true",
        help="Lewati step scraping Instagram"
    )
    parser.add_argument(
        "--skip-scrape", action="store_true",
        help="Lewati semua scraping (shortcut --skip-twitter + --skip-instagram)"
    )
    parser.add_argument(
        "--skip-classify", action="store_true",
        help="Lewati klasifikasi sentimen"
    )
    parser.add_argument(
        "--only-visual", action="store_true",
        help="Hanya jalankan generate visualisasi (skip scrape & classify)"
    )
    return parser.parse_args()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = parse_args()

    success = main(
        skip_twitter   = args.skip_twitter or args.skip_scrape or args.only_visual,
        skip_instagram = args.skip_instagram or args.skip_scrape or args.only_visual,
        skip_classify  = args.skip_classify or args.only_visual,
        skip_visual    = False,
    )

    raise SystemExit(0 if success else 1)