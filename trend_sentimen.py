import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os

# Pastikan folder static ada
os.makedirs('static', exist_ok=True)

# 1. Baca data
df = pd.read_csv('data/hasil.csv')

# 2. Gabungkan semua komentar jadi satu string
all_text = ' '.join(df['komentar'].dropna().astype(str).tolist())

# 3. Buat WordCloud
wc = WordCloud(
    width=800, height=400,
    background_color='white',
    colormap='plasma',
    stopwords=None
).generate(all_text)

# 4. Simpan sebagai gambar
plt.figure(figsize=(10, 5))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.tight_layout()
plt.savefig('static/wordcloud.png', dpi=150)
plt.close()

print("✅ Word cloud disimpan ke static/wordcloud.png")
