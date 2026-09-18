"""Testes dos três chamados do Desafio Final. Rode com: python -m unittest

Cobrem o defeito de cada chamado, os casos de borda das regras do REGRAS.md
e a não-regressão do resto de cada funcionalidade.
"""
import unittest

from loja.banco import criar_conexao
from loja.precos import calcular_total
from loja.relatorios import relatorio_clientes
from loja.clientes import buscar_por_email


class TestChamado1Total(unittest.TestCase):
    """Chamado 1 — cupom não pode zerar o frete."""

    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_cupom_maior_que_subtotal_nao_come_o_frete(self):
        # 102: subtotal 70, frete 20, cupom 120 -> desconto para em 70
        # total = (70 - 70) + 20 = 20
        self.assertEqual(calcular_total(self.conn, 102), 20.0)

    def test_cupom_muito_maior_nao_gera_troco(self):
        # 107: subtotal 50, frete 30, cupom 200 -> total = 0 + 30 = 30
        self.assertEqual(calcular_total(self.conn, 107), 30.0)

    def test_cupom_normal_desconta_so_os_produtos(self):
        # 105: subtotal 90, frete 25, cupom 30 -> (90-30) + 25 = 85
        self.assertEqual(calcular_total(self.conn, 105), 85.0)

    def test_frete_gratis_a_partir_de_150(self):
        # 103: subtotal 200 -> frete grátis; cupom 50 -> 150
        self.assertEqual(calcular_total(self.conn, 103), 150.0)

    def test_estornos_somam_sem_fan_out(self):
        # 104: subtotal 100, frete 15, dois estornos (30+10) -> 75
        self.assertEqual(calcular_total(self.conn, 104), 75.0)

    def test_pedido_sem_cupom_continua_igual(self):
        # 101: 50 + 20 = 70 (não-regressão do caso básico)
        self.assertEqual(calcular_total(self.conn, 101), 70.0)

    def test_subtotal_exatamente_150_tem_frete_gratis(self):
        self.conn.execute(
            "INSERT INTO pedidos VALUES (900, 1, 40.0, 0.0, '2026-06-01')")
        self.conn.execute(
            "INSERT INTO itens VALUES (900, 900, 'Lote', 3, 50.0)")  # 150
        self.assertEqual(calcular_total(self.conn, 900), 150.0)

    def test_cupom_igual_ao_subtotal_ainda_cobra_frete(self):
        self.conn.execute(
            "INSERT INTO pedidos VALUES (901, 1, 12.5, 60.0, '2026-06-01')")
        self.conn.execute(
            "INSERT INTO itens VALUES (901, 901, 'Item', 2, 30.0)")  # 60
        self.assertEqual(calcular_total(self.conn, 901), 12.5)

    def test_cupom_com_frete_gratis_nao_ultrapassa_o_subtotal(self):
        # subtotal 160 (frete grátis), cupom 500 -> total 0, nunca negativo
        self.conn.execute(
            "INSERT INTO pedidos VALUES (902, 1, 30.0, 500.0, '2026-06-01')")
        self.conn.execute(
            "INSERT INTO itens VALUES (902, 902, 'Item', 1, 160.0)")
        self.assertEqual(calcular_total(self.conn, 902), 0.0)

    def test_pedido_sem_itens_cobra_o_frete_cheio(self):
        self.conn.execute(
            "INSERT INTO pedidos VALUES (903, 1, 18.0, 50.0, '2026-06-01')")
        self.assertEqual(calcular_total(self.conn, 903), 18.0)


class TestChamado2Relatorio(unittest.TestCase):
    """Chamado 2 — todo cliente aparece, mesmo com zero pedidos no ano."""

    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_todos_os_clientes_aparecem(self):
        r = relatorio_clientes(self.conn)
        self.assertEqual(len(r), 7)

    def test_cliente_sem_nenhum_pedido_aparece_com_zero(self):
        r = dict((nome, qtd) for nome, _c, qtd in relatorio_clientes(self.conn))
        self.assertEqual(r["Davi Nogueira"], 0)

    def test_cliente_so_com_pedido_antigo_aparece_com_zero(self):
        r = dict((nome, qtd) for nome, _c, qtd in relatorio_clientes(self.conn))
        self.assertEqual(r["Lara Vidal"], 0)  # só tem pedido de 2025

    def test_contagem_dos_clientes_com_pedidos_no_ano(self):
        r = dict((nome, qtd) for nome, _c, qtd in relatorio_clientes(self.conn))
        self.assertEqual(r["Ana Batista"], 2)
        self.assertEqual(r["Bruno Callado"], 1)
        self.assertEqual(r["Célia Marques"], 1)
        self.assertEqual(r["Steve Alex"], 2)

    def test_ordem_por_nome(self):
        nomes = [nome for nome, _c, _q in relatorio_clientes(self.conn)]
        self.assertEqual(nomes, sorted(nomes))

    def test_traz_nome_cidade_e_quantidade(self):
        r = relatorio_clientes(self.conn)
        self.assertTrue(all(len(t) == 3 for t in r))
        self.assertIn(("Davi Nogueira", "Juazeiro do Norte", 0), r)

    def test_corte_de_data_e_inclusivo_em_01_01_2026(self):
        self.conn.execute(
            "INSERT INTO pedidos VALUES (910, 4, 0.0, 0.0, '2026-01-01')")
        self.conn.execute(
            "INSERT INTO pedidos VALUES (911, 4, 0.0, 0.0, '2025-12-31')")
        r = dict((nome, qtd) for nome, _c, qtd in relatorio_clientes(self.conn))
        self.assertEqual(r["Davi Nogueira"], 1)

    def test_banco_sem_clientes_devolve_lista_vazia(self):
        self.conn.execute("DELETE FROM estornos")
        self.conn.execute("DELETE FROM itens")
        self.conn.execute("DELETE FROM pedidos")
        self.conn.execute("DELETE FROM clientes")
        self.assertEqual(relatorio_clientes(self.conn), [])


class TestChamado3Busca(unittest.TestCase):
    """Chamado 3 — busca por e-mail segura e que funciona com apóstrofo."""

    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_email_com_apostrofo_funciona(self):
        self.assertEqual(
            buscar_por_email(self.conn, "o'brien@cariri.test"),
            (6, "Ort O'Brien", "Crato"),
        )

    def test_email_conhecido_continua_funcionando(self):
        self.assertEqual(
            buscar_por_email(self.conn, "ana@cariri.test"),
            (1, "Ana Batista", "Juazeiro do Norte"),
        )

    def test_email_inexistente_devolve_none(self):
        self.assertIsNone(buscar_por_email(self.conn, "ninguem@cariri.test"))

    def test_tautologia_nao_traz_cliente(self):
        self.assertIsNone(buscar_por_email(self.conn, "x' OR '1'='1"))
        self.assertIsNone(buscar_por_email(self.conn, "' OR 1=1 --"))
        self.assertIsNone(buscar_por_email(self.conn, "' OR ''='"))

    def test_union_nao_vaza_dados(self):
        alvo = "x' UNION SELECT id, nome, cidade FROM clientes --"
        self.assertIsNone(buscar_por_email(self.conn, alvo))

    def test_injecao_destrutiva_nao_apaga_dados(self):
        try:
            buscar_por_email(self.conn, "x'; DROP TABLE clientes; --")
        except Exception:
            pass  # o que importa é a tabela seguir de pé
        n = self.conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        self.assertEqual(n, 7)

    def test_string_vazia_devolve_none(self):
        self.assertIsNone(buscar_por_email(self.conn, ""))

    def test_todos_os_clientes_sao_encontraveis(self):
        linhas = self.conn.execute("SELECT id, nome, email, cidade "
                                   "FROM clientes").fetchall()
        for cid, nome, email, cidade in linhas:
            self.assertEqual(buscar_por_email(self.conn, email),
                             (cid, nome, cidade))


if __name__ == "__main__":
    unittest.main()
