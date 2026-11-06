"""Test tambahan buatan kelompok.

Isi dengan:
1. Satu test regresi untuk setiap bug yang kalian perbaiki (gagal sebelum perbaikan,
   lulus sesudahnya). Beri nama yang menjelaskan bug-nya.
2. Lima test kasus tepi, masing-masing dengan komentar singkat mengapa kasus itu berisiko.
"""

import pytest

from crud.lexer import LexError, TokenType, TokenType as T, tokenize
from crud.analyzer import analyze_statement
from crud.parser import parse_sql
from crud import ast_nodes as ast
from crud.resolver import Resolver

def values(src):
    return [t.value for t in tokenize(src) if t.type != T.EOF]

# LEXER

def test_regresi_keyword_huruf_kecil():
    # Bug: keyword SQL huruf kecil sebelumnya tidak dikenali sebagai keyword karena pemeriksaan hanya menggunakan huruf kapital.
    tokens = tokenize("select * from pelanggan")

    assert tokens[0].type == T.KEYWORD
    assert tokens[0].value == "SELECT"


def test_regresi_komentar_blok_multiline():
    # Bug: Lexer sebelumnya belum dapat melewati komentar blok yang dapat mencakup beberapa baris.
    tokens = tokenize("SELECT /* komentar\nmultiline */ * FROM pelanggan")

    values = [token.value for token in tokens]

    assert "SELECT" in values
    assert "*" in values
    assert "FROM" in values
    assert "pelanggan" in values

def test_operator_tidak_sama_dengan():
    # Bug: Operator "<>" sebelumnya tidak dikenali sebagai satu token utuh.
    assert values("a <> b") == ["a", "<>", "b"]


def test_string_escaped_quote():
    # Bug: Dua kutip tunggal berturut-turut harus dibaca sebagai satu karakter kutip.
    toks = tokenize("'O''Brien'")

    assert toks[0].type == T.STRING
    assert toks[0].value == "O'Brien"


def test_string_multiple_escaped_quotes():
     # Risiko: Beberapa kutip tunggal yang di-escape dalam satu string dapat menyebabkan kesalahan pembacaan isi string.
    toks = tokenize("'It''s Noya''s book'")

    assert toks[0].type == T.STRING
    assert toks[0].value == "It's Noya's book"


def test_string_kosong():
    # Risiko: String kosong dapat salah dianggap sebagai string yang tidak ditutup.
    toks = tokenize("''")

    assert toks[0].type == T.STRING
    assert toks[0].value == ""


def test_string_operator_dan_tanda_baca():
    # Risiko: Operator dan tanda baca di dalam string tidak boleh dianggap token terpisah.
    toks = tokenize("'a <> b, c >= d!'")

    assert toks[0].type == T.STRING
    assert toks[0].value == "a <> b, c >= d!"


def test_string_tidak_ditutup():
    # Risiko: String tanpa kutip penutup harus menghasilkan LexError.
    with pytest.raises(LexError):
        tokenize("'Hello")



# PARSER

def test_parser_insert_select():
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

def test_regresi_parser_multiple_statement_error():
    # Risiko: Beberapa statement rusak dapat membuat parser berhenti sebelum mencapai statement valid.
    script = parse_sql(
        "SELECT FROM pelanggan; "
        "INSERT INTO ; "
        "SELECT * FROM produk;"
    )

    assert len(script.errors) == 2
    assert len(script.statements) == 1
    assert script.statements[0].sources[0].name == "produk"

# RESOLVER

def resolve(sql):
    script = parse_sql(sql)
    assert script.errors == [], script.errors
    diagnostics = Resolver().resolve_script(script)
    return script, diagnostics


def columns(node):
    return [
        n for n in ast.iter_nodes(node)
        if isinstance(n, ast.ColumnRef)
    ]


def test_resolver_shadowing_alias_scope_dalam():
    # Alias yang sama pada scope dalam dan luar harus menggunakan deklarasi yang paling dekat.
    script, diags = resolve(
        "SELECT p.id FROM pelanggan p "
        "WHERE EXISTS ("
        "SELECT p.id FROM transaksi p"
        ")"
    )
    p_columns = [
        c for c in columns(script)
        if c.qualifier == "p" and c.name == "id"
    ]
    assert len(p_columns) == 2
    assert p_columns[0].resolved == "pelanggan"
    assert p_columns[1].resolved == "transaksi"
    assert diags == []


def test_resolver_correlated_subquery():
    # Subquery dapat menggunakan alias dari scope luar jika alias tersebut tidak ditemukan pada scope dalam.
    script, diags = resolve(
        "SELECT p.id FROM pelanggan p "
        "WHERE EXISTS ("
        "SELECT t.id FROM transaksi t "
        "WHERE t.pelanggan_id = p.id"
        ")"
    )
    resolved = {
        (c.qualifier, c.name): c.resolved
        for c in columns(script)
    }
    assert resolved[("t", "id")] == "transaksi"
    assert resolved[("t", "pelanggan_id")] == "transaksi"
    assert resolved[("p", "id")] == "pelanggan"
    assert diags == []


def test_resolver_kolom_ambigu_dua_tabel():
    # Kolom tanpa qualifier menjadi ambigu jika terdapat
    # lebih dari satu tabel dalam scope.
    script, diags = resolve(
        "SELECT id FROM pelanggan p "
        "JOIN pesanan o ON p.id = o.pelanggan_id"
    )
    id_column = next(
        c for c in columns(script)
        if c.qualifier is None and c.name == "id"
    )
    assert id_column.resolved is None
    assert any(
        d.level == "warning" and "ambigu" in d.message
        for d in diags
    )


def test_resolver_scope_delete_dibersihkan():
    # Alias dari DELETE tidak boleh terbawa ke statement berikutnya.
    script, diags = resolve(
        "DELETE FROM pelanggan p WHERE p.id = 1; "
        "SELECT p.id FROM pesanan"
    )
    p_columns = [
        c for c in columns(script)
        if c.qualifier == "p"
    ]
    # Ada dua p.id: satu dari DELETE dan satu dari SELECT.
    assert len(p_columns) == 2
    # p.id pada DELETE harus ter-resolve ke pelanggan.
    assert p_columns[0].resolved == "pelanggan"
    # p.id pada SELECT tidak boleh memakai alias dari DELETE.
    assert p_columns[1].resolved is None
    assert any(
        d.level == "error" and "'p'" in d.message
        for d in diags
    )


def test_resolver_subquery_from_dengan_alias():
    # Subquery di FROM dikenali melalui aliasnya, sedangkan kolom di dalam subquery tetap di-resolve sendiri.
    script, diags = resolve(
        "SELECT d.id FROM "
        "(SELECT p.id FROM pelanggan p) d"
    )
    resolved = {
        (c.qualifier, c.name): c.resolved
        for c in columns(script)
    }
    assert resolved[("p", "id")] == "pelanggan"
    assert resolved[("d", "id")] == "<subquery d>"
    assert diags == []

# ANALYZER

def test_regresi_update_dengan_subquery():
    # Risiko: Tabel yang dibaca oleh subquery UPDATE bisa tidak tercatat sebagai operasi Read.
    script = parse_sql(
        "UPDATE pelanggan "
        "SET status = 'aktif' "
        "WHERE id IN ("
        "SELECT pelanggan_id FROM pesanan"
        ")"
    )

    assert script.errors == []

    result = analyze_statement(script.statements[0])

    assert result == {
        "pelanggan": {"U"},
        "pesanan": {"R"}
    }

def test_regresi_update_subquery_di_assignment():
    # Risiko: Subquery di dalam nilai assignment dapat terlewat saat mengumpulkan tabel yang dibaca.
    script = parse_sql(
        "UPDATE produk "
        "SET stok = ("
        "SELECT SUM(jumlah) FROM detail_pesanan"
        ")"
    )

    assert script.errors == []

    result = analyze_statement(script.statements[0])

    assert result == {
        "produk": {"U"},
        "detail_pesanan": {"R"}
    }

def test_analyzer_insert_select():
    # Risiko: Tabel sumber SELECT bisa terlewat dan tidak tercatat sebagai operasi Read.
    script = parse_sql(
        "INSERT INTO arsip_pelanggan "
        "SELECT id FROM pelanggan"
    )
    assert script.errors == []

    result = analyze_statement(script.statements[0])

    assert result == {
        "arsip_pelanggan": {"C"},
        "pelanggan": {"R"}
    }

def test_regresi_delete_dengan_subquery():
    # Risiko: Tabel yang dibaca oleh subquery DELETE bisa tidak tercatat sebagai Read.
    script = parse_sql(
        "DELETE FROM pelanggan "
        "WHERE id IN ("
        "SELECT pelanggan_id FROM pesanan"
        ")"
    )
    assert script.errors == []

    result = analyze_statement(script.statements[0])

    assert result == {
        "pelanggan": {"D"},
        "pesanan": {"R"}
    }

def test_analyzer_gabungan_operasi_satu_tabel():
    # Risiko: Operasi dari beberapa statement pada tabel yang sama bisa tidak tergabung.
    script = parse_sql(
        "SELECT * FROM pelanggan; "
        "UPDATE pelanggan SET status = 'aktif'"
    )
    assert script.errors == []

    result = {}

    for statement in script.statements:
        usage = analyze_statement(statement)
        for table, operations in usage.items():
            result.setdefault(table, set()).update(operations)

    assert result == {
        "pelanggan": {"R", "U"}
    }