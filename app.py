from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "GILBERTGANTENG"

db_config = {
    'user': 'root',
    'password': '',    
    'host': '127.0.0.1',
    'database': 'restorandb',
    'auth_plugin': 'mysql_native_password'
}

def get_db():
    conn = mysql.connector.connect(**db_config)
    return conn


@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM kategori_produk")
    kategori = cur.fetchall()

    #buat ambil data per kategori
    cur.execute("SELECT p.*, k.nama_kategori FROM produk p JOIN kategori_produk k ON p.kategori_id=k.kategori_id ORDER BY k.kategori_id")
    produk = cur.fetchall()

    conn.close()
    
    cart = session.get('cart', {})
    cart_count = sum(item['qty'] for item in cart.values()) if cart else 0
    return render_template('index.html', kategori=kategori, produk=produk, cart_count=cart_count)


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


@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    total = sum(item['harga'] * item['qty'] for item in cart.values())
    return render_template('billing.html', cart=cart, total=total)


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
    # input pelanggan
    cur.execute("INSERT INTO pelanggan (nama_pelanggan,no_telp,alamat) VALUES (%s,%s,%s)",
                (nama_pelanggan, no_telp, alamat))
    pelanggan_id = cur.lastrowid

    # input pesanan
    cur.execute("INSERT INTO pesanan (pelanggan_id, status) VALUES (%s, %s)",
                (pelanggan_id, 'Selesai'))
    pesanan_id = cur.lastrowid

    total = 0.0
    # input detail pesanan & update stok
    for pid, item in cart.items():
        subtotal = item['harga'] * item['qty']
        total += subtotal
        cur.execute("INSERT INTO detail_pesanan (pesanan_id, produk_id, jumlah, subtotal) VALUES (%s,%s,%s,%s)",
                    (pesanan_id, int(pid), item['qty'], subtotal))
        # kurangi stok
        cur.execute("UPDATE produk SET stok = stok - %s WHERE produk_id = %s", (item['qty'], int(pid)))

    # input transaksi
    cur.execute("INSERT INTO transaksi (pesanan_id, metode_pembayaran, total) VALUES (%s,%s,%s)",
                (pesanan_id, metode, total))

    conn.commit()
    conn.close()

    # kosongin cart
    session['cart'] = {}
    flash("Pembayaran berhasil. Terima kasih!", "success")
    return redirect(url_for('index'))

# route login
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

# buat bikin admin
@app.route('/init-admin')
def init_admin():
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM admin")
    count = cur.fetchone()[0]
    if count == 0:
        pw = generate_password_hash("admin123")
        cur.execute("INSERT INTO admin (username,password) VALUES (%s,%s)", ("admin", pw))
        conn.commit()
        conn.close()
        return "Admin dibuat: username=admin password=admin123"
    conn.close()
    return "Admin sudah ada."

# route dashboard
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    # produk
    cur.execute("SELECT p.*, k.nama_kategori FROM produk p JOIN kategori_produk k ON p.kategori_id=k.kategori_id")
    produk = cur.fetchall()
    # ringkasan laporan penjualan
    cur.execute("SELECT COUNT(*) as jumlah_transaksi, IFNULL(SUM(total),0) as total_pendapatan FROM transaksi")
    laporan_ringkas = cur.fetchone()
    conn.close()
    return render_template('dashboard.html', produk=produk, laporan=laporan_ringkas)

# route update stok buat admin
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

# route logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
