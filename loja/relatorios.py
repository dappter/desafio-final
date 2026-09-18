"""Relatórios da loja.

Regras do negócio: veja REGRAS.md, seção "Relatório de clientes".
"""


def relatorio_clientes(conn):
    """(nome, cidade, qtd_pedidos) de cada cliente, em ordem de nome.

    Conta só os pedidos feitos a partir de 2026 (veja REGRAS.md).
    """
    sql = """
        SELECT c.nome, c.cidade, COUNT(p.id) AS qtd
        FROM clientes c
        LEFT JOIN pedidos p ON p.cliente_id = c.id
        WHERE p.feito_em >= '2026-01-01'
        GROUP BY c.id
        ORDER BY c.nome
    """
    return [tuple(r) for r in conn.execute(sql).fetchall()]
