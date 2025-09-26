document.addEventListener('DOMContentLoaded', function () {
  // === popup modal elemen ===
  const modal = document.getElementById('modal');
  const close = document.getElementById('close');
  const modalNama = document.getElementById('modal-nama');
  const modalHarga = document.getElementById('modal-harga');
  const modalStok = document.getElementById('modal-stok');
  const produk_id = document.getElementById('produk_id');
  const produk_nama = document.getElementById('produk_nama');
  const produk_harga = document.getElementById('produk_harga');
  const qtyInput = document.getElementById('qty');
  const formOrder = document.getElementById('form-order');
  const cartCountSpan = document.getElementById('cart-count');

  // === klik tombol pesan ===
  document.querySelectorAll('.order-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      modal.style.display = 'flex'; // buka modal
      modalNama.textContent = this.dataset.nama;
      modalHarga.textContent = parseFloat(this.dataset.harga).toLocaleString('id-ID');
      modalStok.textContent = this.dataset.stok;
      produk_id.value = this.dataset.id;
      produk_nama.value = this.dataset.nama;
      produk_harga.value = this.dataset.harga;
      qtyInput.value = 1;
    });
  });

  // === tutup modal ===
  close.addEventListener('click', () => modal.style.display = 'none');
  window.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = 'none'; });

  // === submit form pesan ===
  formOrder.addEventListener('submit', function (e) {
    e.preventDefault();
    const data = new FormData(formOrder);
    fetch('/add_to_cart', { method: 'POST', body: data })
      .then(res => res.json())
      .then(js => {
        if (js.status === 'ok') {
          cartCountSpan.textContent = js.cart_count;
          modal.style.display = 'none';
          alert('✅ Berhasil ditambahkan ke keranjang');
        } else {
          alert('❌ Gagal menambahkan');
        }
      })
      .catch(err => alert('Error: ' + err));
  });

  // === filter kategori ===
  document.querySelectorAll('.kategori-btn').forEach(b => {
    b.addEventListener('click', () => {
      const k = b.dataset.kategori;
      document.querySelectorAll('.card').forEach(card => {
        if (k === "all" || card.dataset.kategori === k) {
          card.style.display = "block";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
});
