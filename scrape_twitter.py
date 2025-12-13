# scrape_twitter.py

import snscrape.modules.twitter as sntwitter
import pandas as pd
import os
import csv

def run_scraper():
    # 🔍 Query pencarian: JKT48, bahasa Indonesia, sejak awal 2024
    query = "JKT48 lang:id since:2024-01-01"
    tweets = []
    limit = 100  # maksimal tweet yang ingin diambil

    print("🔍 Scraping tweet dari Twitter...")

    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if len(tweets) >= limit:
            break
        tweets.append([
            tweet.date.date(),     # tanggal
            "Twitter",             # platform
            tweet.content,         # isi tweet
            tweet.likeCount,       # like
            ""                     # kolom sentimen kosong (untuk klasifikasi)
        ])

    df_new = pd.DataFrame(tweets, columns=["tanggal", "platform", "komentar", "likes", "sentimen"])
    print(f"📄 Jumlah tweet baru diambil: {len(df_new)}")
    print(df_new.head(3))  # contoh isi tweet

    # 🔁 Gabungkan dengan data lama jika ada
    if os.path.exists("data/hasil.csv"):
        df_old = pd.read_csv("data/hasil.csv")
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["komentar"])
    else:
        df_combined = df_new

    # 💾 Simpan ke file dengan safe quoting
    df_combined.to_csv("data/hasil.csv", index=False, quoting=csv.QUOTE_ALL)

    print(f"✅ Scraping selesai. Total data sekarang: {len(df_combined)} baris.")

# ▶️ Jalankan saat file dipanggil langsung
if __name__ == "__main__":
    run_scraper()
