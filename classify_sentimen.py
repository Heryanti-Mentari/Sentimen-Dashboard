# classify_sentimen.py
import pandas as pd
import re
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import csv

def run_classifier():
    # 1. Baca file hasil.csv
    df = pd.read_csv('data/hasil.csv')

    # 2. Pisahkan data latih (yang sudah punya label) dan data uji (yang kosong)
    train_data = df[df['sentimen'].notna()]
    test_data = df[df['sentimen'].isna()]

    if len(train_data) == 0 or len(test_data) == 0:
        print("⚠️ Tidak ada data latih atau data uji yang tersedia.")
        return

    # 3. Bersihkan teks komentar
    def clean_text(text):
        text = str(text).lower()
        text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

    train_data.loc[:, 'komentar'] = train_data['komentar'].apply(clean_text)
    test_data.loc[:, 'komentar'] = test_data['komentar'].apply(clean_text)

    # 4. Pipeline klasifikasi
    model = Pipeline([
        ('vect', CountVectorizer()),
        ('nb', MultinomialNB())
    ])

    # 5. Latih dan prediksi
    model.fit(train_data['komentar'], train_data['sentimen'])
    predicted = model.predict(test_data['komentar'])

    # 6. Simpan hasil
    df.loc[df['sentimen'].isna(), 'sentimen'] = predicted
    df.to_csv('data/hasil.csv', index=False, quoting=csv.QUOTE_ALL)

    print("✅ Klasifikasi selesai. Kolom sentimen diperbarui.")

# Jika dijalankan langsung
if __name__ == "__main__":
    run_classifier()
