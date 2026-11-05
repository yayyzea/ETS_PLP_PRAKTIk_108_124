"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

from crud.lexer import tokenize, TokenType
from crud.parser import parse_sql

# LEXER

def test_regresi_keyword_huruf_kecil():
    # Bug: keyword SQL huruf kecil sebelumnya tidak dikenali sebagai keyword karena pemeriksaan hanya menggunakan huruf kapital.
    tokens = tokenize("select * from pelanggan")

    assert tokens[0].type == TokenType.KEYWORD
    assert tokens[0].value == "SELECT"


def test_regresi_komentar_blok_multiline():
    # Bug: Lexer sebelumnya belum dapat melewati komentar blok yang dapat mencakup beberapa baris.
    tokens = tokenize("SELECT /* komentar\nmultiline */ * FROM pelanggan")

    values = [token.value for token in tokens]

    assert "SELECT" in values
    assert "*" in values
    assert "FROM" in values
    assert "pelanggan" in values


# PARSER

def test_regresi_insert_select():
    # Bug: Parser sebelumnya menolak INSERT ... SELECT.
    script = parse_sql(
        "INSERT INTO arsip (id) SELECT id FROM pesanan"
    )

    assert script.errors == []
    assert len(script.statements) == 1
    assert script.statements[0].query is not None


def test_regresi_presedensi_and_or():
    # Bug: AND dan OR sebelumnya dianggap memiliki presedensi sama.
    script = parse_sql(
        "SELECT * FROM transaksi "
        "WHERE a = 1 OR b = 2 AND c = 3"
    )

    assert script.errors == []
    query = script.statements[0]

    assert query.where.op == "OR"
    assert query.where.right.op == "AND"

def test_edge_nested_parentheses():
    # Risiko: tanda kurung bertingkat dapat menyebabkan kesalahan saat parser membaca dan menutup ekspresi.
    script = parse_sql(
        "SELECT * FROM pelanggan WHERE ((id = 1))"
    )

    assert script.errors == []
    assert len(script.statements) == 1


def test_edge_not_in():
    # Risiko: NOT dapat salah ditempatkan atau tidak diterapkan pada kondisi IN.
    script = parse_sql(
        "SELECT * FROM pelanggan WHERE id NOT IN (1, 2, 3)"
    )

    assert script.errors == []
    assert len(script.statements) == 1


def test_edge_precedence_arithmetic():
    # Risiko: perkalian harus diproses lebih dahulu daripada penjumlahan dalam satu ekspresi aritmetika.
    script = parse_sql(
        "SELECT * FROM transaksi WHERE total + pajak * 2 > 100"
    )

    assert script.errors == []
    assert len(script.statements) == 1


def test_edge_in_subquery():
    # Risiko: parser harus membedakan daftar nilai IN dengan subquery SELECT yang berada di dalam tanda kurung.
    script = parse_sql(
        "SELECT * FROM pelanggan "
        "WHERE id IN (SELECT pelanggan_id FROM pesanan)"
    )

    assert script.errors == []
    assert len(script.statements) == 1


def test_edge_multiple_statements_and_empty_statement():
    # Risiko: titik koma berulang atau beberapa statement dapat menyebabkan parser salah menentukan batas statement.
    script = parse_sql(
        "SELECT * FROM pelanggan;; SELECT * FROM pesanan;"
    )

    assert script.errors == []
    assert len(script.statements) == 2

def test_regresi_parser_melanjutkan_setelah_statement_error():
    # Bug: Parser sebelumnya membuang seluruh sisa input ketika menemukan statement yang tidak valid.
    script = parse_sql(
        "SELECT FROM pelanggan; "
        "SELECT * FROM produk;"
    )

    assert len(script.errors) == 1
    assert len(script.statements) == 1

    # Pastikan statement kedua tetap berhasil diproses.
    assert script.statements[0].sources[0].name == "produk"