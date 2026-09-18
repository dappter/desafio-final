# Justificativa de processo — Desafio Final

## Como cheguei às correções

Comecei lendo `REGRAS.md` e `CHANGELOG.md` **antes** do código. Os chamados
descrevem sintoma, não defeito; sem a regra escrita ao lado, eu estaria
corrigindo por palpite. O `CHANGELOG.md` ainda datou um dos defeitos: o filtro
de ano do relatório entrou em 2025-08, depois da consulta original — ou seja, a
consulta nasceu correta e o filtro foi acrescentado no lugar errado dela.

Antes de alterar qualquer linha, **reproduzi os três defeitos** rodando o código
original (commit `ff11924`) e guardei a saída. Isso mudou o meu entendimento em
dois pontos concretos: descobri que o relatório perdia **três** clientes (Davi,
Ort e Lara), e não os dois citados no chamado, e que a busca por e-mail forjado
não só falhava como devolvia um cliente real (`Ana Batista`). Diagnóstico sem
reprodução seria diagnóstico de memória.

Em cada caso busquei a **causa raiz, não o sintoma**:

- No cupom, o defeito era o teto do desconto ancorado em `subtotal + frete`.
  Corrigi o teto, em vez de adicionar um `if` tratando o caso do chamado — um
  `if` esconderia a fórmula errada e deixaria as outras bordas quebradas.
- No relatório, o defeito era *quando* a data é avaliada: no `WHERE` ela roda
  depois do join e descarta as linhas com `NULL`, degradando o `LEFT JOIN` para
  `INNER JOIN`. Movi o filtro para o `ON`, em vez de remendar os ausentes com
  um `UNION`.
- Na busca, o defeito era a ausência de fronteira entre código e dado. Usei
  consulta parametrizada, e não escape manual de aspas: escapar trata o
  sintoma, mantém o dado dentro do texto do comando e historicamente sempre
  deixa um caminho aberto.

Cuidei para que cada correção **não estragasse a regra vizinha**. A mais sutil
foi a do relatório: fazer o cliente ausente reaparecer não podia virar "contar
tudo" — a Lara volta à lista com 0, e não com 1, porque o pedido dela é de 2025.
Foi também por isso que mantive `COUNT(p.id)` em vez de `COUNT(*)`, que contaria
a linha nula como 1.

Escrevi 26 testes em `tests/test_chamados.py`, cobrindo os três defeitos, as
bordas das regras (subtotal exatamente 150, cupom igual ao subtotal, corte
inclusivo em 01/01/2026, pedido sem itens, banco sem clientes) e a
não-regressão de cada funcionalidade. Confirmei que os 3 testes de fumaça
originais continuam passando: 29 testes, todos verdes. O enunciado avisa que
uma correção que quebra outra parte perde os pontos daquele problema, então
tratei a não-regressão como parte da entrega, e não como zelo opcional.

Deixei de fora o que a regra não pedia. Na busca, por exemplo, não introduzi
normalização de maiúsculas nem corte de espaços: o `REGRAS.md` não a prevê, e
isso mudaria o comportamento da busca em vez de apenas torná-la segura.

## Uso de IA

Usei assistência de IA (Claude) neste desafio, e registro aqui o que foi feito
com ela e o que foi feito por mim.

**Onde a IA entrou:** usei a IA como par de diagnóstico e de implementação.
Ela leu o repositório comigo, ajudou a localizar os três defeitos, escreveu a
primeira versão das correções, da suíte de testes e do texto do laudo.

**O que eu mantive sob meu controle:** a decisão sobre *qual* correção adotar
em cada chamado, a conferência de cada uma contra o `REGRAS.md`, e a validação
por execução. Nenhuma correção foi aceita por parecer certa: cada defeito foi
reproduzido no código original e cada correção foi verificada rodando a suíte
de testes, com a saída conferida. Também revisei os limites do enunciado que
uma sugestão automática poderia atropelar — não alterar `loja/banco.py`, não
mudar as assinaturas das três funções, usar só a biblioteca padrão — e confirmei
que a entrega os respeita.

**O que a IA não substituiu:** o entendimento do porquê. Sei explicar, sem
consultar o laudo, por que `min(cupom, total)` deixava o cupom comer o frete,
por que uma condição no `WHERE` anula um `LEFT JOIN` enquanto a mesma condição
no `ON` não anula, e por que consulta parametrizada resolve a injeção e o
apóstrofo pelo mesmo motivo — os dois sintomas são a mesma falha de fronteira
entre código e dado. Esse entendimento é o que o laudo registra, e é o critério
que usei para aceitar ou recusar cada sugestão.

Considero esse uso legítimo pelo mesmo motivo que considero legítimo consultar
documentação ou um colega mais experiente: a ferramenta acelera o caminho, mas
a responsabilidade pelo diagnóstico, pela verificação e pelo que está escrito no
laudo continua sendo minha.
