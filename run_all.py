import scrape_twitter
import scrape_instagram
import classify_sentimen
import generate_visual

def main():
    print("Mulai scraping Instagram...")
    scrape_instagram.run_scraper()

    print("Mulai scraping Twitter...")
    scrape_twitter.run_scraper()

    print("Mulai klasifikasi sentimen...")
    classify_sentimen.run_classifier()

    print("Mulai generate visualisasi...")
    generate_visual.run_generate_visual()

    print("Selesai semua proses.")

if __name__ == "__main__":
    main()
