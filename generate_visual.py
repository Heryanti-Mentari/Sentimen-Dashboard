import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os

def safe_save(filepath, save_func):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"⚠️ Gagal hapus {filepath}: {e}")
    save_func()

def run_generate_visual():
    # Pastikan folder static ada
    if not os.path.exists('static'):
        os.makedirs('static')

    # Baca data dari hasil.csv
    df = pd.read_csv('data/hasil.csv')

    # --- Word Cloud ---
    if df['komentar'].dropna().empty:
        print("⚠️ Kolom komentar kosong, WordCloud tidak dibuat")
    else:
        text = ' '.join(df['komentar'].astype(str))
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        safe_save('static/wordcloud.png', lambda: wordcloud.to_file('static/wordcloud.png'))
        print("✅ Word Cloud berhasil dibuat di static/wordcloud.png")

    # --- Grafik Tren Sentimen Harian ---
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    trend = df.groupby(['tanggal', 'sentimen']).size().unstack(fill_value=0)

    plt.figure(figsize=(10,5))
    for sentiment in ['positif', 'netral', 'negatif']:
        if sentiment in trend.columns:
            plt.plot(trend.index, trend[sentiment], label=sentiment.capitalize())

    plt.title('Tren Sentimen Harian')
    plt.xlabel('Tanggal')
    plt.ylabel('Jumlah Komentar')
    plt.legend()
    plt.tight_layout()
    safe_save('static/trend.png', lambda: plt.savefig('static/trend.png'))
    plt.close()
    print("✅ Grafik tren berhasil dibuat di static/trend.png")

    # --- Bar Chart Jumlah Sentimen ---
    sentiment_counts = df['sentimen'].value_counts()
    color_map = {'positif': '#34d399', 'netral': '#facc15', 'negatif': '#f87171'}
    colors = [color_map.get(s, '#999999') for s in sentiment_counts.index]

    plt.figure(figsize=(6,4))
    plt.bar(sentiment_counts.index, sentiment_counts.values, color=colors)
    plt.title('Jumlah Sentimen')
    plt.xlabel('Sentimen')
    plt.ylabel('Jumlah Komentar')
    plt.tight_layout()
    safe_save('static/barChart.png', lambda: plt.savefig('static/barChart.png'))
    plt.close()
    print("✅ Bar Chart berhasil dibuat di static/barChart.png")

    # --- Pie Chart Proporsi Sentimen ---
    plt.figure(figsize=(6,6))
    plt.pie(sentiment_counts.values, labels=sentiment_counts.index.str.capitalize(),
            colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Proporsi Sentimen')
    plt.tight_layout()
    safe_save('static/pieChart.png', lambda: plt.savefig('static/pieChart.png'))
    plt.close()
    print("✅ Pie Chart berhasil dibuat di static/pieChart.png")

if __name__ == "__main__":
    run_generate_visual()
