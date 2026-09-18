# Regras do negócio — leia antes de mexer no código

Este arquivo é a fonte da verdade sobre **como o sistema deve se comportar**.
Os chamados do enunciado dizem o que está errado; aqui está o certo.

## Total do pedido (`loja/precos.py`)

O total de um pedido é calculado assim, nesta ordem:

1. **Subtotal** = soma de `quantidade × preço unitário` de todos os itens.
2. **Frete**: é **grátis** quando o subtotal (de produtos, antes do cupom)
   é **150 ou mais**. Abaixo disso, cobra-se o frete cheio do pedido.
3. **Cupom**: o desconto do cupom vale **só sobre os produtos**. Ele
   **nunca** desconta o frete. Se o cupom for maior que o subtotal, o
   desconto para no subtotal (o cliente ainda paga o frete; não existe troco).
4. **Estornos**: o valor estornado é subtraído do total.

Resumo: `total = (subtotal − desconto_no_subtotal) + frete − estornos`.

## Relatório de clientes (`loja/relatorios.py`)

`relatorio_clientes` devolve `(nome, cidade, qtd_pedidos)` de **todos os
clientes**, em ordem de nome — inclusive quem **nunca fez pedido** (aparece
com `qtd_pedidos = 0`).

A contagem considera só os pedidos **feitos a partir de 01/01/2026**. Um
cliente cujos pedidos são todos anteriores a 2026 continua no relatório,
com contagem 0. Ele não pode sumir da lista.

## Busca por e-mail (`loja/clientes.py`)

`buscar_por_email` devolve `(id, nome, cidade)` do cliente com aquele
e-mail, ou `None`. O e-mail vem digitado por quem usa o sistema, então
**trate a entrada como não confiável**. E-mails legítimos podem conter
apóstrofo (existe cliente com e-mail assim no banco).
