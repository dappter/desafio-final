"""Testes de EXEMPLO (fumaça) do Desafio Final. Rode com: python -m unittest

Eles cobrem o comportamento BÁSICO do sistema e passam no código como ele
está. NÃO cobrem os três defeitos dos chamados — encontrá-los é com você.
A correção é feita por uma suíte oculta, que inclui casos de borda e testes
de que o resto do sistema continua funcionando.
"""
import unittest

from loja.banco import criar_conexao
from loja.precos import calcular_total
from loja.relatorios import relatorio_clientes
from loja.clientes import buscar_por_email


class TestFumaca(unittest.TestCase):
    def setUp(self):
        self.conn = criar_conexao()

    def tearDown(self):
        self.conn.close()

    def test_total_pedido_simples(self):
        # pedido 101: 2x Café 25,00 = 50; frete 20; sem cupom -> 70
        self.assertEqual(calcular_total(self.conn, 101), 70.0)

    def test_relatorio_devolve_tuplas(self):
        r = relatorio_clientes(self.conn)
        self.assertTrue(all(len(t) == 3 for t in r))
        self.assertTrue(any(nome == "Ana Batista" for nome, _c, _q in r))

    def test_busca_email_conhecido(self):
        self.assertEqual(
            buscar_por_email(self.conn, "ana@cariri.test"),
            (1, "Ana Batista", "Juazeiro do Norte"),
        )


if __name__ == "__main__":
    unittest.main()
