"""Busca de clientes."""


def buscar_por_email(conn, email):
    """Devolve (id, nome, cidade) do cliente com aquele e-mail, ou None."""
    # Consulta parametrizada: o e-mail viaja como VALOR (bind parameter), e
    # não concatenado no texto do SQL. O driver nunca interpreta o conteúdo
    # digitado como código, então não há injeção, e apóstrofo é só mais um
    # caractere do dado (nada de aspas desbalanceadas quebrando a consulta).
    sql = "SELECT id, nome, cidade FROM clientes WHERE email = ?"
    linha = conn.execute(sql, (email,)).fetchone()
    return tuple(linha) if linha else None
