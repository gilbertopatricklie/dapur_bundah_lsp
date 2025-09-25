from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ganti_dengan_secret_key_yang_kuat"

# CONFIG DATABASE - sesuaikan dengan config XAMPP Anda
db_config = {
    'user': 'root',
    'password': '',    # biasanya kosong di XAMPP
    'host': '127.0.0.1',
    'database': 'restorandb',
    'auth_plugin': 'mysql_native_password'
}

def get_db():
    conn = mysql.connector.connect(**db_config)
    return conn

# ROUTE: halaman utama
@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM kategori_produk")
    kategori = cur.fetchall()

    # ambil produk grouped by kategori
    cur.execute("SELECT p.*, k.nama_kategori FROM produk p JOIN kategori_produk k ON p.kategori_id=k.kategori_id ORDER BY k.kategori_id")
    produk = cur.fetchall()

    conn.close()
    # cart stored in session
    cart = session.get('cart', {})
    cart_count = sum(item['qty'] for item in cart.values()) if cart else 0
    return render_template('index.html', kategori=kategori, produk=produk, cart_count=cart_count)

# ROUTE: tambah item ke cart (AJAX/POST)
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    produk_id = request.form.get('produk_id')
    nama = request.form.get('nama')
    harga = float(request.form.get('harga'))
    qty = int(request.form.get('qty', 1))

    cart = session.get('cart', {})

    if produk_id in cart:
        cart[produk_id]['qty'] += qty
    else:
        cart[produk_id] = {'nama': nama, 'harga': harga, 'qty': qty}

    session['cart'] = cart
    return jsonify({'status': 'ok', 'cart_count': sum(item['qty'] for item in cart.values())})

# ROUTE: lihat cart / billing page
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    total = sum(item['harga'] * item['qty'] for item in cart.values())
    return render_template('billing.html', cart=cart, total=total)

# ROUTE: checkout & simpan pesanan + transaksi
@app.route('/checkout', methods=['POST'])
def checkout():
    nama_pelanggan = request.form.get('nama_pelanggan') or "Guest"
    no_telp = request.form.get('no_telp', '')
    alamat = request.form.get('alamat', '')
    metode = request.form.get('metode_pembayaran', 'Tunai')
    cart = session.get('cart', {})
    if not cart:
        flash("Keranjang kosong", "warning")
        return redirect(url_for('index'))

    conn = get_db()
    cur = conn.cursor()
    # insert pelanggan
    cur.execute("INSERT INTO pelanggan (nama_pelanggan,no_telp,alamat) VALUES (%s,%s,%s)",
                (nama_pelanggan, no_telp, alamat))
    pelanggan_id = cur.lastrowid

    # insert pesanan
    cur.execute("INSERT INTO pesanan (pelanggan_id, status) VALUES (%s, %s)",
                (pelanggan_id, 'Selesai'))
    pesanan_id = cur.lastrowid

    total = 0.0
    # insert detail pesanan & update stok
    for pid, item in cart.items():
        subtotal = item['harga'] * item['qty']
        total += subtotal
        cur.execute("INSERT INTO detail_pesanan (pesanan_id, produk_id, jumlah, subtotal) VALUES (%s,%s,%s,%s)",
                    (pesanan_id, int(pid), item['qty'], subtotal))
        # kurangi stok
        cur.execute("UPDATE produk SET stok = stok - %s WHERE produk_id = %s", (item['qty'], int(pid)))

    # insert transaksi
    cur.execute("INSERT INTO transaksi (pesanan_id, metode_pembayaran, total) VALUES (%s,%s,%s)",
                (pesanan_id, metode, total))

    conn.commit()
    conn.close()

    # clear cart
    session['cart'] = {}
    flash("Pembayaran berhasil. Terima kasih!", "success")
    return redirect(url_for('index'))

# ROUTE: halaman login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cur.fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin['admin_id']
            session['admin_username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Login gagal. Cek username/password.", "danger")
    return render_template('login.html')

# ROUTE: inisialisasi admin (buat 1 admin) -- gunakan sekali, lalu hapus/disable
@app.route('/init-admin')
def init_admin():
    # hanya jika belum ada admin
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM admin")
    count = cur.fetchone()[0]
    if count == 0:
        pw = generate_password_hash("admin123")
        cur.execute("INSERT INTO admin (username,password) VALUES (%s,%s)", ("admin", pw))
        conn.commit()
        conn.close()
        return "Admin dibuat: username=admin password=admin123 (ganti segera)"
    conn.close()
    return "Admin sudah ada."

# ROUTE: dashboard admin
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    # produk
    cur.execute("SELECT p.*, k.nama_kategori FROM produk p JOIN kategori_produk k ON p.kategori_id=k.kategori_id")
    produk = cur.fetchall()
    # ringkasan laporan penjualan (sederhana): total pendapatan dan jumlah transaksi
    cur.execute("SELECT COUNT(*) as jumlah_transaksi, IFNULL(SUM(total),0) as total_pendapatan FROM transaksi")
    laporan_ringkas = cur.fetchone()
    conn.close()
    return render_template('dashboard.html', produk=produk, laporan=laporan_ringkas)

# ROUTE: update stok (admin)
@app.route('/update_stock', methods=['POST'])
def update_stock():
    if not session.get('admin_logged_in'):
        return jsonify({'status':'forbidden'}), 403
    produk_id = int(request.form['produk_id'])
    stok_baru = int(request.form['stok'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE produk SET stok=%s WHERE produk_id=%s", (stok_baru, produk_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# ROUTE: logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
