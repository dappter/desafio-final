"""Banco de dados da loja (SQLite em memória).

Cria o esquema e carrega os dados de exemplo. Este arquivo está
CORRETO e não deve ser alterado: os defeitos não estão aqui.
"""
import sqlite3

ESQUEMA = """
CREATE TABLE clientes (
    id     INTEGER PRIMARY KEY,
    nome   TEXT NOT NULL,
    email  TEXT NOT NULL UNIQUE,
    cidade TEXT NOT NULL
);

CREATE TABLE pedidos (
    id         INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    frete      REAL NOT NULL DEFAULT 0,
    cupom      REAL NOT NULL DEFAULT 0,   -- desconto em reais
    feito_em   TEXT NOT NULL              -- 'AAAA-MM-DD'
);

CREATE TABLE itens (
    id         INTEGER PRIMARY KEY,
    pedido_id  INTEGER NOT NULL REFERENCES pedidos(id),
    produto    TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unit REAL NOT NULL
);

CREATE TABLE estornos (
    id        INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
    valor     REAL NOT NULL
);
"""

CLIENTES = [
    # id, nome, email, cidade
    (1, "Ana Batista",     "ana@cariri.test",       "Juazeiro do Norte"),
    (2, "Bruno Callado",   "bruno@cariri.test",     "Crato"),
    (3, "Célia Marques",   "celia@cariri.test",     "Barbalha"),
    (4, "Davi Nogueira",   "davi@cariri.test",      "Juazeiro do Norte"),  # sem pedidos
    (5, "Steve Alex",      "steve@cariri.test",     "Missão Velha"),
    (6, "Ort O'Brien",     "o'brien@cariri.test","Crato"),               # apóstrofo no login
    (7, "Lara Vidal",      "lara@cariri.test",      "Juazeiro do Norte"),   # só pedido de 2025
]

PEDIDOS = [
    # id, cliente_id, frete, cupom, feito_em
    (101, 1, 20.0,   0.0, "2026-02-10"),
    (102, 1, 20.0, 120.0, "2026-03-01"),   # cupom MAIOR que o subtotal, com frete
    (103, 2,  0.0,  50.0, "2026-02-15"),   # subtotal alto: frete grátis
    (104, 3, 15.0,   0.0, "2026-01-20"),   # tem estorno
    (105, 5, 25.0,  30.0, "2026-04-02"),
    (107, 5, 30.0, 200.0, "2026-05-01"),   # cupom (200) MUITO maior que o subtotal (50), frete 30
    (106, 7, 18.0,   0.0, "2025-12-30"),   # pedido de 2025 (fora da janela do relatório)
]

ITENS = [
    # id, pedido_id, produto, quantidade, preco_unit
    (1, 101, "Café 500g",          2, 25.0),   # subtotal 50
    (2, 102, "Picareta de ferro",  1, 40.0),
    (3, 102, "Balde de água",      1, 30.0),   # subtotal 70
    (4, 103, "Cesta básica",       1, 200.0),  # subtotal 200 -> frete grátis
    (5, 104, "Arroz 5kg",          2, 30.0),
    (6, 104, "Feijão 1kg",         4, 10.0),   # subtotal 100
    (7, 105, "Redstone 1kg",       1, 90.0),   # subtotal 90
    (9, 107, "Espada de diamante", 1, 50.0),   # subtotal 50
    (8, 106, "Panela",             1, 60.0),   # subtotal 60 (pedido de 2025)
]

ESTORNOS = [
    # id, pedido_id, valor
    (1, 104, 30.0),
    (2, 104, 10.0),   # dois estornos no mesmo pedido (armadilha de fan-out)
]


def criar_conexao():
    """Cria um banco novo em memória, já com o esquema e os dados."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(ESQUEMA)
    conn.executemany("INSERT INTO clientes VALUES (?,?,?,?)", CLIENTES)
    conn.executemany("INSERT INTO pedidos  VALUES (?,?,?,?,?)", PEDIDOS)
    conn.executemany("INSERT INTO itens    VALUES (?,?,?,?,?)", ITENS)
    conn.executemany("INSERT INTO estornos VALUES (?,?,?)", ESTORNOS)
    conn.commit()
    return conn
