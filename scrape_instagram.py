# scrape_instagram.py

import pandas as pd
from datetime import date
import csv
import os

def run_scraper():
    # Data dummy untuk testing
    data = [
        [date.today(), "Instagram", "Keren banget perform JKT48 hari ini!", 78, ""],
        [date.today(), "Instagram", "Biasa aja sih, kurang greget.", 34, ""],
    ]
    df_new = pd.DataFrame(data, columns=["tanggal", "platform", "komentar", "likes", "sentimen"])
    
    # Gabungkan dengan file hasil.csv jika ada
    if os.path.exists("data/hasil.csv"):
        existing = pd.read_csv("data/hasil.csv")
        df_combined = pd.concat([existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    # Simpan ke hasil.csv dengan kutipan agar aman
    df_combined.to_csv("data/hasil.csv", index=False, quoting=csv.QUOTE_ALL)
    print("✅ Data dummy dari Instagram ditambahkan ke data/hasil.csv")
