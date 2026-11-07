# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

python evaluate.py
Belum berlabel (tidak dievaluasi): ast_error.sql

Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')


Evaluasi dilakukan terhadap empat file SQL, yaitu audit.sql, campuran_error.sql, laporan_penjualan.sql, dan pemeliharaan.sql, dengan total 27 data acuan (triple) berdasarkan data/ground_truth.csv.

Hasil evaluasi menunjukkan bahwa parser memperoleh nilai Precision 1.00, Recall 1.00, dan F1 1.00. Hal ini menunjukkan bahwa seluruh hasil ekstraksi parser sesuai dengan data acuan yang telah ditentukan.

Sebagai pembanding, metode regex memperoleh Precision 0.65, Recall 0.81, dan F1 0.72. Hasil tersebut menunjukkan bahwa metode regex masih menghasilkan sejumlah temuan yang keliru (false positive) serta melewatkan beberapa operasi CRUD (false negative).

Berdasarkan hasil tersebut, parser memiliki tingkat ketepatan ekstraksi yang lebih baik dibandingkan metode regex pada dataset pengujian yang digunakan.


## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1. Kasus 1: Kesalahan membedakan operasi DELETE dan SELECT
- SQL: DELETE FROM sesi;
- Kesalahan regex: Regex menghasilkan dua operasi untuk tabel sesi, yaitu R dan D. Operasi R merupakan false positive karena tabel tersebut bukan dibaca, melainkan dihapus datanya.
- Mengapa parser benar: Pada implementasi regex, pola FROM selalu dianggap sebagai operasi R, termasuk ketika digunakan dalam statement DELETE FROM. Sementara itu, parser mengenali struktur statement berdasarkan grammar SQL sehingga dapat membedakan DELETE FROM sebagai operasi D, bukan R.

2. Kasus 2: Regex tidak dapat membedakan komentar dan string literal dari perintah SQL
-SQL:
-- DELETE FROM pelanggan (baris ini komentar, bukan perintah)
SELECT p.nama, SUM(o.total) AS omzet
FROM pelanggan p
JOIN pesanan o ON o.pelanggan_id = p.id
WHERE o.status = 'LUNAS' AND o.catatan <> 'FROM rahasia'
GROUP BY p.nama;
- Kesalahan regex: Regex membaca DELETE FROM pelanggan di dalam komentar sebagai perintah SQL dan menghasilkan false positive berupa operasi D dan R pada tabel pelanggan. Regex juga membaca teks FROM rahasia di dalam string literal sebagai referensi tabel sehingga menghasilkan false positive operasi R pada tabel rahasia. Selain itu, posisi awal statement dapat keliru karena regex mengambil keyword pertama yang ditemukan di dalam komentar.
- Mengapa parser benar: Lexer parser mengenali komentar sebagai bagian yang harus dilewati dan string literal sebagai satu token STRING. Teks SQL yang hanya muncul di dalam komentar atau string tidak dianggap sebagai perintah maupun referensi tabel.

3. Kasus 3: Regex gagal menangani komentar multiline
- SQL:
/* Skrip pemeliharaan data pelanggan.
   Catatan lama: UPDATE pelanggan_lama sudah tidak dipakai. */
SELECT c.id, c.nama, a.kota
FROM crm.pelanggan c
LEFT OUTER JOIN crm.alamat a ON a.pelanggan_id = c.id
WHERE c.nama = 'O''Brien' OR c.kota = 'Bandung' AND c.aktif = 1;
- Kesalahan regex: Regex membaca UPDATE pelanggan_lama di dalam komentar multiline sebagai perintah UPDATE sehingga menghasilkan false positive berupa operasi U pada tabel pelanggan_lama.
- Mengapa parser benar: Lexer parser dapat mengenali komentar multiline yang diawali /* dan diakhiri */, sehingga isi komentar tidak diproses sebagai token SQL. Parser hanya menganalisis statement SQL yang sebenarnya dan tidak menghasilkan operasi CRUD dari teks komentar.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

## 4. Pembagian kerja

Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
