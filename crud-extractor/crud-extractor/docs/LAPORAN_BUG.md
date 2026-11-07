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
