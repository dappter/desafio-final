"""Busca de clientes."""


def buscar_por_email(conn, email):
    """Devolve (id, nome, cidade) do cliente com aquele e-mail, ou None."""
    sql = "SELECT id, nome, cidade FROM clientes WHERE email = '%s'" % email
    linha = conn.execute(sql).fetchone()
    return tuple(linha) if linha else None
