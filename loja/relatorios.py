"""Relatórios da loja.

Regras do negócio: veja REGRAS.md, seção "Relatório de clientes".
"""


def relatorio_clientes(conn):
    """(nome, cidade, qtd_pedidos) de cada cliente, em ordem de nome.

    Conta só os pedidos feitos a partir de 2026 (veja REGRAS.md).
    """
    # O filtro de data fica no ON, e não no WHERE: no WHERE ele descartaria
    # as linhas em que o LEFT JOIN não achou pedido (p.feito_em é NULL),
    # transformando o LEFT JOIN em INNER JOIN e sumindo com quem não tem
    # pedido no período. No ON, o cliente permanece na lista com qtd = 0.
    sql = """
        SELECT c.nome, c.cidade, COUNT(p.id) AS qtd
        FROM clientes c
        LEFT JOIN pedidos p
               ON p.cliente_id = c.id
              AND p.feito_em >= '2026-01-01'
        GROUP BY c.id, c.nome, c.cidade
        ORDER BY c.nome
    """
    return [tuple(r) for r in conn.execute(sql).fetchall()]
