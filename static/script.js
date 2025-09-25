document.addEventListener('DOMContentLoaded', function(){
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

  document.querySelectorAll('.order-btn').forEach(btn=>{
    btn.addEventListener('click', function(){
      const id = this.dataset.id;
      const nama = this.dataset.nama;
      const harga = this.dataset.harga;
      const stok = this.dataset.stok;
      modalNama.textContent = nama;
      modalHarga.textContent = parseFloat(harga).toLocaleString('id-ID');
      modalStok.textContent = stok;
      produk_id.value = id;
      produk_nama.value = nama;
      produk_harga.value = harga;
      qtyInput.value = 1;
      modal.style.display = 'flex';
    });
  });

  close.addEventListener('click', ()=> modal.style.display = 'none');
  window.addEventListener('click', (e)=> { if(e.target == modal) modal.style.display='none'; });

  formOrder.addEventListener('submit', function(e){
    e.preventDefault();
    const data = new FormData(formOrder);
    fetch('/add_to_cart', { method: 'POST', body: data })
      .then(res => res.json())
      .then(js => {
        if(js.status === 'ok'){
          cartCountSpan.textContent = js.cart_count;
          modal.style.display = 'none';
          alert('Berhasil ditambahkan ke keranjang');
        } else {
          alert('Gagal menambahkan');
        }
      })
      .catch(err=> alert('Terjadi error'));
  });

  // filter by kategori on click
  document.querySelectorAll('.kategori-btn').forEach(b=>{
    b.addEventListener('click', ()=>{
      const k = b.dataset.kategori;
      document.querySelectorAll('.card').forEach(card=>{
        if(card.dataset.kategori === k) card.style.display = 'block'; else card.style.display = 'none';
      });
    });
  });
});
