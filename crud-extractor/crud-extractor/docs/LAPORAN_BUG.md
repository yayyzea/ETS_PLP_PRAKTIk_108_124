# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Kesalahan parser dalam melanjutkan statement setelah syntax error

**Ditemukan oleh:** Kayla · **Diperbaiki oleh:** Kayla

**Gejala.** Input, output yang didapat, dan output yang diharapkan menurut SPESIFIKASI.md
(sebutkan bagiannya).

Input:
SELECT FROM pelanggan;
SELECT * FROM produk;

Output aktual sebelum perbaikan:
Parser menemukan kesalahan sintaks pada statement pertama dan tidak melanjutkan pemrosesan statement kedua. Akibatnya, statement kedua yang berisi akses tabel produk tidak berhasil diproses.

Output yang diharapkan menurut spesifikasi:
Parser harus melaporkan satu kesalahan pada statement pertama, kemudian melakukan pemulihan (error recovery) dengan membuang token sampai dan termasuk titik koma (;) berikutnya. Setelah itu, parser harus melanjutkan pemrosesan statement berikutnya sehingga tabel produk tetap dapat dikenali.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT FROM a;
SELECT * FROM b;
```

**Akar masalah.** Mengapa kode lama salah? Konsep apa yang dilanggar?
Mekanisme pemulihan kesalahan parser belum melakukan sinkronisasi pada pemisah statement dengan benar. Akibatnya, parser tidak dapat melanjutkan proses parsing setelah menemukan statement yang rusak.

Dalam konsep Crafting Interpreters, kondisi ini berkaitan dengan panic-mode error recovery, yaitu mekanisme pemulihan parser dengan mencari titik sinkronisasi agar proses parsing dapat dilanjutkan. 

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
- Mekanisme sinkronisasi parser diperbaiki agar proses parsing dapat dilanjutkan setelah menemukan pemisah statement berupa titik koma (;).
- File yang diperbaiki: crud/parser.py
- Alternatif yang dipertimbangkan: Parser dapat menghentikan seluruh proses ketika menemukan kesalahan sintaks. Namun, pendekatan tersebut tidak digunakan karena spesifikasi mengharuskan parser tetap memproses statement valid setelah statement yang mengalami kesalahan.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
- Nama test:
test_regresi_parser_melanjutkan_setelah_statement_error
- Pengujian memastikan bahwa statement valid setelah statement yang mengalami kesalahan tetap diproses.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menganalisis penyebab parser berhenti setelah menemukan kesalahan sintaks dan menjelaskan konsep panic-mode error recovery dari Crafting Interpreters. AI juga memberikan arahan mengenai mekanisme sinkronisasi parser.

---

## Bug 2: Operator <> tidak dikenali sebagai satu token

**Ditemukan oleh:** Kayla · **Diperbaiki oleh:** Kayla

**Gejala.** 
Input:
SELECT FROM pelanggan
WHERE id <> 10;

Output aktual sebelum perbaikan:
Lexer belum mengenali operator <> sebagai satu token operator yang utuh. Akibatnya, operator tersebut tidak diproses sesuai bentuk token yang ditentukan dalam spesifikasi.

Output yang diharapkan menurut spesifikasi:
Lexer harus mengenali <> sebagai satu token bertipe OP, bukan memisahkannya menjadi dua token < dan >.

Contoh representasi nilai token yang diharapkan:
["SELECT", "*", "FROM", "pelanggan",
 "WHERE", "id", "<>", "10", ";"]



**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT * FROM a WHERE id <> 1;
```

**Akar masalah.** Mengapa kode lama salah? Pengenalan operator pada lexer belum menangani operator dua karakter <> dengan benar. Lexer perlu memeriksa kemungkinan operator yang lebih panjang sebelum menetapkan token operator yang lebih pendek.

Dalam konsep Crafting Interpreters, hal ini berkaitan dengan proses pemindaian token dan pemilihan karakter yang membentuk token secara tepat.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
- Pengenalan operator pada lexer diperbaiki agar <> dikenali sebagai satu token bertipe OP.
- File yang diperbaiki: crud/lexer.py
- Alternatif yang dipertimbangkan: Memperlakukan < dan > sebagai dua token terpisah tidak digunakan karena akan bertentangan dengan aturan operator SQL dan ketentuan maximal munch dalam spesifikasi.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
- Nama test:
test_operator_tidak_sama_dengan
- Pengujian memastikan bahwa operator <> dikenali sebagai satu token.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menjelaskan penyebab operator <> tidak dikenali sebagai satu token serta konsep maximal munch. AI juga membantu meninjau pendekatan perbaikan dan menyusun skenario pengujian untuk memastikan operator tersebut terbaca secara utuh.

---

## Bug 3: Penanganan string dengan tanda kutip dan karakter khusus

**Ditemukan oleh:** Kayla · **Diperbaiki oleh:** Kayla

**Gejala.** 
Input:
INSERT INTO pelanggan (nama)
VALUES ('O' 'Brien');

Output aktual sebelum perbaikan:
Lexer belum menangani dua tanda kutip tunggal berurutan ('') di dalam string dengan benar. Akibatnya, tanda kutip yang seharusnya menjadi bagian dari nilai string dapat salah dikenali sebagai penutup string.

Output yang diharapkan menurut spesifikasi:
Lexer harus mengenali seluruh 'O''Brien' sebagai satu token bertipe STRING dengan nilai:
O'Brien

Selain itu, lexer juga harus menangani string kosong, karakter operator dan tanda baca di dalam string, serta menghasilkan LexError apabila string tidak memiliki tanda kutip penutup.

Referensi spesifikasi: SPESIFIKASI.md, Bagian 2.4 — String.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
INSERT INTO a (nama) VALUES ('O''Brien');
```

**Akar masalah.** Mengapa kode lama salah? Proses pemindaian string belum membedakan tanda kutip penutup dengan dua tanda kutip berurutan yang merepresentasikan satu karakter kutip di dalam string.

Dalam konsep Crafting Interpreters, scanner harus membaca karakter secara berurutan dan menentukan apakah karakter tersebut merupakan bagian dari nilai token atau penanda akhir token.

**Perbaikan.** File dan fungsi yang diubah, serta alasannya. Sebutkan juga perbaikan
alternatif yang kalian pertimbangkan dan alasan tidak memilihnya.
- Logika pemindaian string pada fungsi _string diperbaiki untuk menangani:
    - Escaped quote ('') sebagai satu karakter kutip di dalam string.
    - String kosong.
    - Operator dan tanda baca yang berada di dalam string.
    - String yang tidak memiliki tanda kutip penutup dengan menghasilkan LexError.
- File yang diperbaiki: crud/lexer.py
- Fungsi yang diperbaiki: _string
- Alternatif yang dipertimbangkan: Mengakhiri string setiap kali menemukan tanda kutip tunggal tidak dapat digunakan karena pendekatan tersebut tidak dapat membedakan tanda kutip penutup dan tanda kutip yang di-escape. Oleh karena itu, proses pemindaian perlu memeriksa karakter berikutnya ketika menemukan tanda kutip tunggal.

**Test regresi.** Nama test di `tests/test_tambahan.py` yang gagal sebelum perbaikan dan lulus
sesudahnya.
- Nama test:
    - test_string_escaped_quote
    - test_string_multiple_escaped_quotes
    - test_string_kosong
    - test_string_operator_dan_tanda_baca
    - test_string_tidak_ditutup
- Pengujian tersebut memastikan berbagai kondisi string dapat diproses sesuai ketentuan spesifikasi.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?
AI membantu menjelaskan aturan penulisan string SQL, khususnya penggunaan dua tanda kutip tunggal untuk merepresentasikan tanda kutip di dalam string. AI juga membantu menganalisis kemungkinan kesalahan pada proses pemindaian karakter dan menyusun skenario pengujian untuk escaped quote, string kosong, karakter khusus, serta string yang tidak ditutup.

---

## Bug 4: Parser Tidak Mengenali Sintaks LEFT OUTER JOIN

**Ditemukan oleh:** Zahra · **Diperbaiki oleh:** Zahra 

**Gejala.**
Ketika parser menerima query yang menggunakan sintaks `LEFT OUTER JOIN`, parser menghasilkan kesalahan sintaks karena tidak dapat mengenali keyword `OUTER` setelah `LEFT`.
Contoh input:
```sql
SELECT p.id
FROM pelanggan p
LEFT OUTER JOIN alamat a ON a.pelanggan_id = p.id;
```
Output yang didapat sebelum perbaikan adalah kesalahan parsing karena parser mengharapkan keyword `JOIN` secara langsung setelah `LEFT`.  
Berdasarkan SPESIFIKASI.md bagian 3 (Grammar), sintaks JOIN memperbolehkan penggunaan `LEFT` dengan keyword `OUTER` sebagai bagian opsional.
Output yang diharapkan adalah parser berhasil memproses query menjadi satu statement tanpa menghasilkan kesalahan sintaks.

**Reproduksi minimal.**
```sql
SELECT * FROM pelanggan
LEFT OUTER JOIN alamat ON pelanggan.id = alamat.id;
```

**Akar masalah.**
Kesalahan terjadi karena fungsi `_join()` pada parser hanya mengenali keyword `LEFT`, kemudian langsung mengharapkan keyword `JOIN`. Parser tidak memeriksa kemungkinan adanya keyword `OUTER` di antara keduanya.
Hal ini menyebabkan implementasi grammar belum sesuai dengan aturan sintaks JOIN yang ditentukan dalam spesifikasi.
Berdasar konsep Crafting Interpreters Bab 6.2 – Recursive Descent Parsing, setiap aturan grammar diterjemahkan menjadi fungsi parser. Simbol opsional dalam grammar harus ditangani menggunakan kondisi yang memungkinkan parser menerima atau melewati token tersebut. Dalam kasus ini, keyword `OUTER` merupakan bagian opsional dari aturan `LEFT JOIN`.

**Perbaikan.**
Perbaikan dilakukan pada file `crud/parser.py`, khususnya fungsi `_join()`.
Setelah parser mengenali keyword `LEFT`, ditambahkan pemeriksaan terhadap keyword `OUTER` menggunakan `_match_kw("OUTER")`. Dengan demikian, parser dapat menerima kedua bentuk sintaks, yaitu `LEFT JOIN` dan `LEFT OUTER JOIN`, tanpa membuat proses parsing JOIN menjadi dua implementasi terpisah.
Alternatif yang dapat digunakan adalah membuat percabangan terpisah untuk `LEFT JOIN` dan `LEFT OUTER JOIN`. Namun, pendekatan tersebut tidak dipilih karena akan mengulang proses parsing yang sama. Penanganan keyword opsional lebih sederhana dan tetap sesuai dengan grammar.

**Test regresi.**
Nama test: `test_parser_left_outer_join` pada file `tests/test_tambahan.py`.
Test memeriksa bahwa query dengan `LEFT OUTER JOIN` menghasilkan tepat satu statement dan tidak memiliki kesalahan parsing. Setelah perbaikan, test berhasil dijalankan.

**Peran AI.**
AI membantu mengidentifikasi kemungkinan penyebab kesalahan pada proses parsing JOIN dan memberikan arahan mengenai penanganan keyword opsional. Perbaikan kemudian diterapkan pada fungsi `_join()` dan diverifikasi dengan menjalankan test regresi serta seluruh test tambahan.

---

## Bug 5: Lexer Tidak Mengenali Keyword SQL yang Ditulis dengan Huruf Kecil

**Ditemukan oleh:** Zahra · **Diperbaiki oleh:** Zahra 

**Gejala.**
Ketika lexer menerima keyword SQL yang ditulis menggunakan huruf kecil, keyword tersebut sebelumnya tidak dikenali sebagai token `KEYWORD`. Hal ini terjadi karena pemeriksaan keyword hanya sesuai dengan bentuk huruf kapital yang terdapat pada daftar keyword.
Contoh input:
```sql
select * from pelanggan;
```
Output yang didapat sebelum perbaikan adalah token `select` dan `from` tidak dikenali sebagai keyword SQL sebagaimana mestinya. Berdasarkan SPESIFIKASI.md bagian 2.2 (Keyword dan Identifier), keyword SQL tidak peka terhadap penggunaan huruf besar maupun kecil. Dengan demikian, `select`, `Select`, dan `SELECT` harus dikenali sebagai keyword yang sama. Nilai token keyword juga harus dinormalisasi menjadi huruf kapital.
Output yang diharapkan adalah `select` dikenali sebagai token `KEYWORD` dengan nilai `SELECT`, sedangkan nama tabel `pelanggan` tetap dikenali sebagai `IDENT`.

**Reproduksi minimal.**
```sql
select * from pelanggan;
```

**Akar masalah.**
Kesalahan terjadi karena fungsi `_word()` pada lexer menggunakan teks asli untuk memeriksa apakah suatu kata termasuk dalam daftar `KEYWORDS`. Akibatnya, kata yang ditulis menggunakan huruf kecil tidak cocok dengan daftar keyword yang menggunakan huruf kapital.
Konsep yang tidak terpenuhi adalah case-insensitive keyword recognition, yaitu pengenalan keyword tanpa membedakan huruf besar dan kecil.
Berdasar konsep Crafting Interpreters Bab 4 – Scanning, lexer bertugas mengelompokkan karakter menjadi token berdasarkan jenisnya. Dalam proses tersebut, lexer harus dapat membedakan keyword dan identifier secara konsisten.

**Perbaikan.**
Perbaikan dilakukan pada file `crud/lexer.py`, khususnya fungsi `_word()`.
Sebelum memeriksa daftar keyword, teks yang diperoleh dari sumber SQL diubah menjadi huruf kapital menggunakan `text.upper()`. Jika hasilnya cocok dengan daftar `KEYWORDS`, lexer menghasilkan token `KEYWORD` dengan nilai yang sudah dinormalisasi. Jika tidak cocok, kata tersebut tetap diperlakukan sebagai `IDENT` dengan mempertahankan teks aslinya.
Alternatif yang dapat digunakan adalah mengubah seluruh isi SQL menjadi huruf kapital sebelum proses tokenisasi. Namun, pendekatan tersebut tidak dipilih karena dapat mengubah isi string dan penulisan identifier yang seharusnya tetap dipertahankan. Normalisasi hanya pada saat pemeriksaan keyword lebih aman.

**Test regresi.**
Nama test: `test_regresi_keyword_huruf_kecil` pada file `tests/test_tambahan.py`.
Test memeriksa bahwa keyword `select` dikenali sebagai token `KEYWORD` dan nilai tokennya dinormalisasi menjadi `SELECT`. Setelah perbaikan, test berhasil dijalankan.

**Peran AI.**
AI membantu menganalisis penyebab keyword huruf kecil tidak dikenali dan menyarankan normalisasi teks sebelum pemeriksaan daftar keyword. Perbaikan kemudian diterapkan pada fungsi `_word()` dan diverifikasi menggunakan test regresi yang memeriksa jenis serta nilai token.

---

## Bug 6: Lexer Tidak Dapat Menangani Komentar Blok Multiline

**Ditemukan oleh:** Zahra · **Diperbaiki oleh:** Zahra 

**Gejala.**
Ketika lexer menemukan komentar blok yang mencakup lebih dari satu baris, isi komentar sebelumnya tidak dapat dilewati dengan benar. Akibatnya, karakter di dalam komentar berpotensi terbaca sebagai bagian dari token SQL dan mengganggu proses tokenisasi.
Contoh input:
```sql
SELECT /* komentar
multiline */ * FROM pelanggan;
```
Output yang didapat sebelum perbaikan adalah lexer tidak dapat melewati seluruh isi komentar blok yang terdiri dari beberapa baris dengan benar.
Berdasarkan SPESIFIKASI.md bagian 2.3 (Komentar), komentar blok menggunakan pasangan `/*` dan `*/`, boleh melintasi beberapa baris, tidak menghasilkan token, dan komentar yang tidak ditutup harus menghasilkan `LexError`.
Output yang diharapkan adalah seluruh isi komentar dilewati sehingga lexer hanya menghasilkan token dari pernyataan SQL di luar komentar.

**Reproduksi minimal.**
```sql
SELECT /* komentar
multiline */ * FROM pelanggan;
```

**Akar masalah.**
Kesalahan terjadi karena penanganan komentar blok pada lexer belum melakukan pemindaian hingga menemukan penutup `*/` secara menyeluruh. Akibatnya, komentar yang melewati beberapa baris tidak ditangani sebagaimana aturan yang ditentukan.
Konsep yang tidak terpenuhi adalah pemindaian komentar sebagai bagian dari proses lexical analysis. Komentar harus dilewati sepenuhnya dan tidak boleh menghasilkan token yang masuk ke proses parsing.
Menurut konsep Crafting Interpreters Bab 4 – Scanning, lexer bertanggung jawab memindai karakter sumber dan menghasilkan token. Karakter yang termasuk komentar harus diabaikan oleh lexer, bukan diteruskan sebagai token kepada parser.

**Perbaikan.**
Perbaikan dilakukan pada file `crud/lexer.py`, khususnya bagian penanganan komentar blok di dalam proses tokenisasi.
Lexer diperbaiki agar terus membaca karakter sampai menemukan pasangan penutup `*/`. Proses ini tetap berjalan meskipun komentar melewati beberapa baris. Jika akhir input tercapai sebelum ditemukan penutup komentar, lexer menghasilkan `LexError` dengan pesan bahwa komentar blok tidak ditutup.
Alternatif yang dapat digunakan adalah menghapus komentar menggunakan regex sebelum proses tokenisasi. Namun, pendekatan tersebut tidak dipilih karena penanganan komentar lebih tepat dilakukan langsung oleh lexer. Selain itu, penghapusan menggunakan regex berisiko mengganggu isi string yang kebetulan mengandung pola karakter mirip komentar.

**Test regresi.**
Nama test: `test_regresi_komentar_blok_multiline` pada file `tests/test_tambahan.py`.
Test memeriksa bahwa token SQL sebelum dan sesudah komentar tetap dikenali, termasuk `SELECT`, `*`, `FROM`, dan nama tabel `pelanggan`. Setelah perbaikan, test berhasil dijalankan.

**Peran AI.**
AI membantu mengidentifikasi bahwa penanganan komentar blok perlu dilakukan dengan pemindaian sampai ditemukan pasangan penutup `*/`. AI juga membantu memberikan gambaran penanganan komentar yang tidak ditutup. Implementasi kemudian diterapkan pada lexer dan diverifikasi melalui test regresi yang memeriksa token hasil pemindaian.

---

## Bug 7: Parser Tidak Menerapkan Presedensi Operator AND dan OR dengan Benar

**Ditemukan oleh:** Zahra · **Diperbaiki oleh:** Zahra 

**Gejala.**
Ketika parser menerima ekspresi logika yang menggunakan operator `AND` dan `OR` secara bersamaan, parser sebelumnya memperlakukan kedua operator tersebut dengan tingkat presedensi yang sama.
Contoh input:
```sql
SELECT * FROM transaksi
WHERE a = 1 OR b = 2 AND c = 3;
```
Output yang didapat sebelum perbaikan adalah struktur AST yang tidak mencerminkan prioritas operator sesuai aturan SQL. Parser dapat membentuk ekspresi dengan pengelompokan yang keliru karena `AND` dan `OR` diproses pada tingkat yang sama.
Berdasarkan SPESIFIKASI.md bagian 3.1 (Presedensi), operator `OR` memiliki presedensi lebih rendah daripada `AND`. Oleh karena itu, ekspresi tersebut harus dibaca sebagai:
```sql
a = 1 OR (b = 2 AND c = 3)
```
Output yang diharapkan adalah AST dengan operator `OR` sebagai simpul utama, sedangkan ekspresi `b = 2 AND c = 3` menjadi bagian dari operand kanan.

**Reproduksi minimal.**
```sql
SELECT * FROM transaksi
WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.**
Kesalahan terjadi karena fungsi `_logical()` pada parser sebelumnya memproses operator `AND` dan `OR` dalam satu tingkat perulangan. Akibatnya, parser tidak membedakan tingkat presedensi kedua operator tersebut.
Konsep yang tidak terpenuhi adalah *operator precedence*, yaitu aturan yang menentukan operator mana yang harus dievaluasi atau dikelompokkan terlebih dahulu dalam suatu ekspresi.
Berdasar konsep Crafting Interpreters Bab 6 – Parsing Expressions, grammar ekspresi perlu disusun berdasarkan tingkat presedensi operator. Dalam pendekatan recursive descent, setiap tingkat presedensi dapat diterjemahkan menjadi fungsi parser yang berbeda sehingga struktur ekspresi yang dihasilkan sesuai dengan aturan grammar.

**Perbaikan.**
Perbaikan dilakukan pada file `crud/parser.py`, khususnya fungsi `_logical()` dan `_and()`.
Pemrosesan operator dipisahkan menjadi dua tingkat. Fungsi `_logical()` menangani operator `OR` dan memanggil `_and()` untuk memproses operandnya. Sementara itu, fungsi `_and()` menangani operator `AND` terlebih dahulu.
Dengan pemisahan tersebut, parser akan membentuk ekspresi `AND` sebagai bagian dari operand `OR`, sehingga presedensi operator menjadi benar.
Alternatif yang dapat digunakan adalah menambahkan tanda kurung secara otomatis pada ekspresi sebelum parsing. Namun, pendekatan tersebut tidak dipilih karena tanda kurung hanya merupakan salah satu cara mengelompokkan ekspresi, bukan solusi untuk memperbaiki aturan grammar. Pemisahan fungsi berdasarkan tingkat presedensi lebih sesuai dengan pendekatan recursive descent.

**Test regresi.**
Nama test: `test_regresi_presedensi_and_or` pada file `tests/test_tambahan.py`.
Test memeriksa struktur AST dengan memastikan bahwa operator utama adalah `OR` dan operand kanannya merupakan ekspresi `AND`. Setelah perbaikan, test berhasil dijalankan.

**Peran AI.**
AI membantu menganalisis kesalahan pengelompokan ekspresi dan menjelaskan hubungan antara presedensi operator dengan struktur AST. AI juga memberikan arahan untuk memisahkan pemrosesan `AND` dan `OR` ke dalam fungsi yang berbeda. Perbaikan kemudian diterapkan pada parser dan diverifikasi melalui pemeriksaan struktur AST menggunakan test regresi.

## Bug 8: Kesalahan klasifikasi operasi read pada statement UPDATE

**Ditemukan oleh:** Kayla · **Diperbaiki oleh:** Kayla

**Gejala.**

Ketika analyzer memproses statement `UPDATE` yang memiliki subquery pada kondisi `WHERE` atau nilai assignment, analyzer sebelumnya mengklasifikasikan tabel yang digunakan oleh subquery sebagai operasi Update (U), padahal tabel tersebut hanya digunakan untuk membaca data.

Contoh input:

```sql
UPDATE pelanggan
SET status = 'aktif'
WHERE id IN (
    SELECT pelanggan_id FROM pesanan
);
```

Output yang didapat sebelum perbaikan adalah:

```python
{
    "pelanggan": {"U"},
    "pesanan": {"U"}
}
```

Hasil tersebut tidak sesuai karena tabel `pesanan` hanya digunakan untuk membaca data melalui subquery, bukan untuk diperbarui.

Berdasarkan ketentuan operasi CRUD pada SPESIFIKASI.md bagian 5, tabel yang menjadi target statement UPDATE harus diklasifikasikan sebagai operasi Update (U), sedangkan tabel yang datanya dibaca melalui subquery harus diklasifikasikan sebagai operasi Read (R).

Output yang diharapkan:

```python
{
    "pelanggan": {"U"},
    "pesanan": {"R"}
}
```

**Reproduksi minimal.**

```sql
UPDATE a
SET status = 'aktif'
WHERE id IN (
    SELECT id FROM b
);
```

**Akar masalah.**

Kesalahan terjadi karena fungsi `analyze_statement()` pada analyzer sebelumnya menggunakan jenis operasi U ketika memanggil fungsi `_collect()` untuk mengumpulkan tabel dari ekspresi assignment dan kondisi `WHERE` pada statement UPDATE. Akibatnya, seluruh tabel yang ditemukan dalam ekspresi tersebut, termasuk tabel yang hanya dibaca melalui subquery, ikut diklasifikasikan sebagai operasi Update.

Konsep yang tidak terpenuhi adalah pembedaan konteks penggunaan data, yaitu antara operasi membaca data (Read) dan mengubah data (Update).

Berdasarkan konsep *Crafting Interpreters* Bab 5 – Representing Code dan Bab 6 – Parsing Expressions, AST merepresentasikan struktur sintaks program yang kemudian dapat ditelusuri untuk memproses setiap bagian ekspresi sesuai konteksnya. Dalam kasus ini, proses traversal AST perlu mempertahankan perbedaan antara tabel target yang diperbarui dan tabel sumber yang hanya dibaca.

**Perbaikan.**

Perbaikan dilakukan pada file `crud/analyzer.py`, khususnya fungsi `analyze_statement()`.

Jenis operasi pada pemanggilan `_collect()` untuk ekspresi assignment dan kondisi `WHERE` diubah dari U menjadi R. Sementara itu, tabel target statement UPDATE tetap diklasifikasikan sebagai operasi U.

Dengan perubahan tersebut, tabel yang digunakan dalam subquery pada ekspresi assignment maupun kondisi WHERE dapat diklasifikasikan sebagai operasi Read (R), tanpa mengubah klasifikasi tabel target UPDATE.

Alternatif yang dapat digunakan adalah mempertahankan jenis operasi U untuk seluruh ekspresi UPDATE. Namun, pendekatan tersebut tidak dipilih karena akan menyebabkan tabel yang hanya dibaca melalui subquery ikut diklasifikasikan sebagai tabel yang diperbarui.

**Test regresi.**

Nama test:
- `test_regresi_update_dengan_subquery`
- `test_regresi_update_subquery_di_assignment`

Kedua test terdapat pada file `tests/test_tambahan.py`.

Test pertama memeriksa klasifikasi tabel yang dibaca melalui subquery pada kondisi WHERE. Test kedua memeriksa klasifikasi tabel yang dibaca melalui subquery pada nilai assignment. Keduanya memastikan tabel sumber diklasifikasikan sebagai operasi Read (R), sedangkan tabel target tetap diklasifikasikan sebagai operasi Update (U).

**Peran AI.**

AI membantu menganalisis kesalahan klasifikasi operasi CRUD pada statement UPDATE dan menjelaskan perbedaan antara operasi Read dan Update. Perbaikan diverifikasi dengan membandingkan kode sebelum dan sesudah commit serta memeriksa hasil pengujian regresi.

## Bug 9: Resolver Tidak Menangani Kolom Tanpa Qualifier

**Ditemukan oleh:** Kayla · **Diperbaiki oleh:** Kayla

**Gejala.**

Ketika resolver menerima referensi kolom tanpa qualifier, misalnya `nama`, resolver sebelumnya belum dapat menentukan tabel asal kolom tersebut meskipun hanya terdapat satu tabel dalam scope terdalam.

Contoh input:

```sql
SELECT nama FROM pelanggan;
```

Output aktual sebelum perbaikan:

Referensi kolom `nama` tidak berhasil dihubungkan dengan tabel `pelanggan`. Nilai `ColumnRef.resolved` belum terisi.

Berdasarkan SPESIFIKASI.md bagian 4.3 (Resolusi Kolom), apabila kolom ditulis tanpa qualifier, resolver hanya memeriksa scope terdalam. Jika terdapat tepat satu tabel dalam scope tersebut, kolom harus di-resolve ke tabel itu.

Output yang diharapkan:

```python
ColumnRef.resolved = "pelanggan"
```

Spesifikasi juga mengatur bahwa jika terdapat lebih dari satu tabel, resolver harus memberikan warning `kolom 'nama' ambigu tanpa skema` dan mempertahankan nilai `resolved` sebagai `None`.

**Reproduksi minimal.**

```sql
SELECT nama FROM pelanggan;
```

**Akar masalah.**

Kesalahan terjadi karena fungsi `_column()` pada resolver sebelumnya hanya menangani referensi kolom yang memiliki qualifier, misalnya `pelanggan.nama`. Untuk kolom tanpa qualifier, implementasi masih berupa bagian yang belum diselesaikan (`TODO`), sehingga resolver belum memeriksa jumlah tabel dalam scope terdalam.

Konsep yang belum diterapkan adalah resolusi nama berdasarkan scope, yaitu menentukan referensi berdasarkan lingkungan tempat nama tersebut digunakan.

Berdasarkan konsep *Crafting Interpreters* Bab 11 – Resolving and Binding, resolver bertugas menentukan hubungan antara suatu referensi nama dengan deklarasi yang sesuai berdasarkan aturan scope. Konsep ini menjadi dasar pemahaman untuk menentukan tabel yang menjadi tujuan referensi kolom. Penerapannya pada proyek ini mengikuti aturan khusus dalam SPESIFIKASI.md bagian 4.3.

**Perbaikan.**

Perbaikan dilakukan pada file `crud/resolver.py`, khususnya fungsi `_column()`.

Implementasi ditambahkan untuk menangani kolom tanpa qualifier dengan memeriksa tabel yang terdapat pada scope terdalam:

- Jika terdapat tepat satu tabel, `ColumnRef.resolved` diisi dengan nama tabel tersebut.
- Jika terdapat lebih dari satu tabel, resolver memberikan warning bahwa kolom ambigu tanpa skema dan nilai `resolved` tetap `None`.
- Jika tidak terdapat tabel dalam scope, resolver memberikan warning bahwa kolom tidak dapat ditentukan tanpa tabel.

Alternatif yang dapat digunakan adalah selalu memberikan warning untuk setiap kolom tanpa qualifier. Namun, pendekatan tersebut tidak dipilih karena spesifikasi memperbolehkan resolusi apabila hanya terdapat satu tabel dalam scope terdalam.

**Test regresi.**

Nama test: `test_kolom_tanpa_qualifier_satu_tabel` pada file `tests/test_resolver.py`.

Test memeriksa bahwa kolom tanpa qualifier dapat di-resolve ke tabel apabila hanya terdapat satu tabel dalam scope.

Pengujian tambahan untuk kondisi ambigu juga tersedia melalui `test_resolver_kolom_ambigu_dua_tabel` pada file `tests/test_tambahan.py`. Test tersebut memastikan bahwa resolver memberikan warning dan mempertahankan nilai `resolved` sebagai `None` ketika terdapat lebih dari satu tabel.

Catatan: test resolver tersebut ditambahkan oleh Zahra, sedangkan implementasi resolusi kolom tanpa qualifier diperbaiki oleh Kayla.

**Peran AI.**

AI membantu menganalisis bagian resolver yang belum menangani kolom tanpa qualifier dan menjelaskan aturan resolusi berdasarkan scope. Perbaikan diverifikasi dengan memeriksa pengujian resolver yang tersedia.