# generate_dummy_data.py
import csv
import random
from datetime import datetime, timedelta
import os

# Buat folder data jika belum ada
os.makedirs('data', exist_ok=True)

platforms = ['Twitter', 'Instagram']
sentiments = ['positif', 'netral', 'negatif']
comments = {
    'positif': [
        "JKT48 keren banget!", "Suka banget sama lagu barunya!", "Performance mereka selalu memukau.",
        "Fans JKT48 paling solid!", "Malam ini seru banget!", "Vocalsnya makin bagus.",
        "Aku bangga jadi fans mereka.", "JKT48 juara deh!", "Semangat terus ya JKT48!",
        "Cinta banget sama JKT48!"
    ],
    'netral': [
        "Biasa aja sih menurutku.", "Gak terlalu suka tapi gak benci juga.", 
        "Lagu itu biasa aja, ya.", "Performance standar aja.", "Netral aja deh.",
        "Lumayan tapi bisa lebih baik.", "Tonton karena penasaran.", "Kadang suka kadang nggak.",
        "Gak ada yang spesial.", "Santai aja lihatnya."
    ],
    'negatif': [
        "Agak mengecewakan sih perform-nya.", "Lagu itu nggak catchy.", "Suara kurang stabil.",
        "Kualitas video kurang bagus.", "Gak suka sama konsepnya.", "Kelebihan lip sync sih.",
        "Fansnya kadang toxic.", "Kurang greget tampilannya.", "Aku lebih suka grup lain.",
        "Setiap kali nonton selalu kurang puas."
    ]
}

def random_date(start, end):
    """Generate random date between start and end."""
    delta = end - start
    int_delta = delta.days
    random_day = random.randrange(int_delta)
    return start + timedelta(days=random_day)

def generate_data(num=100):
    rows = []
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 5, 19)

    for _ in range(num):
        platform = random.choice(platforms)
        sentiment = random.choice(sentiments + [None]*3)  # beberapa sentimen kosong untuk dianalisis
        if sentiment is not None:
            comment = random.choice(comments[sentiment])
        else:
            # komentar tanpa label sentimen untuk diuji
            comment = random.choice(comments['positif'] + comments['netral'] + comments['negatif'])
        likes = random.randint(0, 200)
        date = random_date(start_date, end_date).strftime('%Y-%m-%d')

        rows.append([date, platform, comment, likes, sentiment if sentiment else ''])

    return rows

def save_csv(filename, rows):
    header = ['tanggal', 'platform', 'komentar', 'likes', 'sentimen']
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"✅ File {filename} berhasil dibuat dengan {len(rows)} data.")

if __name__ == '__main__':
    data_rows = generate_data(100)
    save_csv('data/hasil.csv', data_rows)
