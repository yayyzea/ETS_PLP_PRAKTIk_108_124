# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.
```
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
```

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

1. Common Table Expression (CTE)
Contoh SQL:
```
WITH pelanggan_aktif AS (
    SELECT id FROM pelanggan WHERE aktif = 1
)
SELECT * FROM pelanggan_aktif;
```
- Keterbatasan: Tool belum mendukung CTE yang menggunakan keyword WITH.
- Dampak pada CRUD matrix: Operasi pembacaan (R) terhadap tabel sumber pelanggan maupun CTE pelanggan_aktif tidak dapat dianalisis dengan benar dan dapat menghasilkan parse error.
- Informasi yang dibutuhkan: Dukungan grammar untuk deklarasi nama CTE, subquery pembentuknya, dan penggunaan CTE sebagai sumber tabel.

2. UNION
Contoh SQL:
```
SELECT id FROM pelanggan
UNION
SELECT id FROM pesanan;
```
- Keterbatasan: Grammar parser belum mendukung penggabungan beberapa hasil SELECT menggunakan UNION.
- Dampak pada CRUD matrix: Pembacaan terhadap tabel pelanggan dan pesanan tidak dapat diproses sebagai satu statement secara benar. Statement dapat menghasilkan parse error sehingga hasil pembacaannya tidak dihitung.
- Informasi yang dibutuhkan: Dukungan grammar untuk UNION dan UNION ALL, termasuk aturan penggabungan beberapa SELECT dalam satu statement.

3. Data Definition Language (DDL)
Contoh SQL:
```
CREATE TABLE pelanggan (
    id INT,
    nama VARCHAR(100)
);
ALTER TABLE pelanggan ADD COLUMN aktif BOOLEAN;
DROP TABLE pelanggan;
```
- Keterbatasan: Tool hanya mendukung statement SELECT, INSERT, UPDATE, dan DELETE. Statement DDL seperti CREATE, ALTER, dan DROP belum termasuk dalam grammar maupun aturan operasi proyek.
- Dampak pada CRUD matrix: Perubahan struktur database tidak direpresentasikan dalam matriks karena belum tersedia kategori operasi khusus untuk DDL.
- Informasi yang dibutuhkan: Dukungan grammar untuk statement DDL serta perluasan aturan klasifikasi operasi agar perubahan struktur database dapat direpresentasikan.

4. Quoted Identifiers
Contoh SQL:
```
SELECT "customerName"
FROM "Customer";
```
- Keterbatasan: Parser belum mendukung identifier yang ditulis menggunakan tanda kutip.
- Dampak pada CRUD matrix: Nama tabel atau kolom yang menggunakan tanda kutip dapat menyebabkan parse error sehingga operasi pembacaan tidak tercatat.
- Informasi yang dibutuhkan: Dukungan lexer dan grammar untuk mengenali quoted identifiers serta aturan penanganan tanda kutip.

5. Views
Contoh SQL:
```
SELECT *
FROM v_penjualan;
```
- Keterbatasan: Tool tidak memiliki informasi skema database untuk mengetahui tabel-tabel yang mendasari sebuah view.
- Dampak pada CRUD matrix: Tool hanya dapat mencatat pembacaan terhadap v_penjualan, tetapi tidak dapat mengidentifikasi tabel sumber yang digunakan dalam definisi view tersebut.
- Informasi yang dibutuhkan: Informasi definisi view atau metadata skema database agar hubungan antara view dan tabel sumbernya dapat diketahui.



## 4. Pembagian Kerja

| Modul/Bagian | Zahra | Kayla |
|---|---|---|
| **Lexer** | Mengimplementasikan tokenisasi SQL, pengenalan keyword secara case-insensitive, serta penanganan komentar satu baris dan komentar blok beserta deteksi komentar yang tidak ditutup. | Mengimplementasikan pengenalan operator perbandingan, termasuk `<>`, serta penanganan string dengan escaped quote seperti `''`. |
| **Parser** | Mengimplementasikan parsing statement SELECT, INSERT, UPDATE, dan DELETE ke dalam AST, termasuk JOIN, subquery, INSERT ... SELECT, presedensi operator logika, serta LEFT JOIN dan LEFT OUTER JOIN. | Mengimplementasikan mekanisme error recovery agar parser dapat melanjutkan pemrosesan setelah menemukan statement yang mengalami kesalahan. |
| **Resolver** | Mengimplementasikan resolusi alias tabel dan referensi kolom berdasarkan scope, termasuk penanganan kolom ambigu, subquery pada FROM, serta pemeriksaan referensi kolom. | Mengimplementasikan dan memperbaiki scope lookup, shadowing, correlated subquery, serta pembersihan scope pada statement DELETE. |
| **Analyzer** | Melakukan pemeriksaan integrasi hasil analisis dengan tahapan Pipeline dan keluaran CLI. | Menangani klasifikasi operasi UPDATE yang melibatkan subquery. |
| **Ground Truth** | Menggunakan data acuan untuk memvalidasi hasil ekstraksi dan membandingkannya dengan keluaran program. | Menyusun dan memvalidasi data acuan untuk file `pemeliharaan.sql`. |
| **Pipeline dan CLI** | Memeriksa integrasi tahapan pemrosesan serta memperbaiki penanganan diagnostic, LexError, exit code, dan input file dengan nama yang sama. | Melakukan pengujian terhadap integrasi fitur yang telah diimplementasikan. |
| **Pengujian** | Menambahkan pengujian tambahan untuk Lexer, Parser, dan Resolver serta melakukan validasi hasil ekstraksi menggunakan file SQL sampel. | Menambahkan dan menjalankan pengujian untuk fitur yang menjadi tanggung jawabnya serta melakukan pengujian silang terhadap implementasi Anggota A. |

### Kolaborasi dan Integrasi

Kedua anggota melakukan integrasi dan pengujian silang terhadap fitur yang telah diimplementasikan. Setiap anggota bertanggung jawab terhadap bagian pekerjaan masing-masing, sedangkan anggota lainnya turut melakukan review dan pengujian untuk memastikan fitur berjalan sesuai spesifikasi.

Pengujian dilakukan melalui regression test, pengujian berbagai kasus SQL, dan pemeriksaan hasil ekstraksi terhadap ground truth. Kedua anggota juga menjalankan pengujian otomatis menggunakan pytest, mengevaluasi hasil parser dibandingkan metode regex, serta memeriksa keluaran CSV untuk memastikan hasil implementasi sesuai dengan spesifikasi.

Melalui proses tersebut, kedua anggota dapat memahami alur kerja keseluruhan sistem, mulai dari lexical analysis, parsing dan pembentukan AST, resolusi nama, hingga analisis operasi CRUD.
