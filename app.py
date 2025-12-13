from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import subprocess
import os
import csv

app = Flask(__name__)

# ✅ Route Login dengan Validasi
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Login gagal. Username atau password salah.")
    return render_template('login.html')

# ✅ Route Dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    df = pd.read_csv('data/hasil.csv')

    platform = request.args.get('platform', 'all')
    sentimen = request.args.get('sentimen', 'all')

    if platform != 'all':
        df = df[df['platform'] == platform]
    if sentimen != 'all':
        df = df[df['sentimen'] == sentimen]

    positif = len(df[df['sentimen'] == 'positif'])
    netral = len(df[df['sentimen'] == 'netral'])
    negatif = len(df[df['sentimen'] == 'negatif'])

    return render_template('dashboard.html',
                           positif=positif, netral=netral, negatif=negatif)

# ✅ Route Detail Data
@app.route('/detail')
def detail():
    df = pd.read_csv('data/hasil.csv')
    return render_template('detail.html', data=df.to_dict(orient='records'))

# ✅ Route Ekspor CSV
@app.route('/export/csv')
def export_csv():
    df = pd.read_csv('data/hasil.csv')
    df.to_csv('data/laporan.csv', index=False, quoting=csv.QUOTE_ALL)
    return send_file('data/laporan.csv', as_attachment=True)

# ✅ Route Ekspor PDF
@app.route('/export/pdf')
def export_pdf():
    import export_pdf  # jalankan script pdf generator
    return send_file("laporan.pdf", as_attachment=True)

# ✅ Route Logout
@app.route('/logout')
def logout():
    return redirect('/')

# ✅ Route Jalankan Semua Proses (Update Data)
@app.route('/update-data')
def update_data():
    try:
        subprocess.run(["python", "run_all.py"], check=True)
        return redirect('/dashboard')
    except subprocess.CalledProcessError as e:
        return f"""
        ❌ Gagal update data.<br>
        <pre>{e}</pre>
        <br>Silakan jalankan <code>run_all.py</code> secara manual untuk melihat detail errornya.
        """

# ▶️ Jalankan Flask App
if __name__ == '__main__':
    app.run(debug=True)
