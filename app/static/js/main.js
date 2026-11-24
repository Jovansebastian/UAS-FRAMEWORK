// Konfirmasi sebelum hapus (Delete)
document.querySelectorAll(".del-form").forEach(f => {
  f.addEventListener("submit", e => {
    if (!confirm("Yakin mau hapus data ini?")) e.preventDefault();
  });
});

// Tombol contoh cepat untuk isi form
document.querySelectorAll(".chip").forEach(c => {
  c.addEventListener("click", () => {
    document.getElementById("recency").value = c.dataset.r;
    document.getElementById("frequency").value = c.dataset.f;
    document.getElementById("monetary").value = c.dataset.m;
  });
});

// Hilangkan notifikasi otomatis
setTimeout(() => document.querySelectorAll(".alert").forEach(a => a.style.display = "none"), 6000);
