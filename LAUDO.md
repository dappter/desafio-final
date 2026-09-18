# Laudo técnico — Mercadão do Cariri

**Sistema:** mini-sistema da loja online
**Commit corrigido:** `0e48338` (branch `main`)
**Arquivos alterados:** `loja/precos.py`, `loja/relatorios.py`, `loja/clientes.py`
**Arquivo não alterado:** `loja/banco.py`
**Verificação:** `python -m unittest` — 29 testes, todos passando (3 de fumaça
originais + 26 novos em `tests/test_chamados.py`).

Cada defeito foi primeiro **reproduzido** no código original (commit `ff11924`),
depois corrigido, e a correção foi verificada com teste automatizado — incluindo
testes de não-regressão do restante de cada funcionalidade.

---

## Problema 1 — Total do pedido (`loja/precos.py`)

### Causa raiz

O erro está no **teto do desconto do cupom**, na linha
`desconto = min(cupom, total)`, onde `total` já era `subtotal + frete`.

O cálculo seguia esta ordem:

```python
total = subtotal + frete
desconto = min(cupom, total)      # <-- teto errado
total = total - desconto - estornado
```

O `min` existe para impedir que o cupom vire troco. Mas ele foi ancorado no
**total com frete**, e não no subtotal de produtos. Quando o cupom é maior que
o subtotal, a diferença sobra e é consumida pelo frete: o cliente recebe, na
prática, frete grátis pago pela loja.

O `REGRAS.md` é explícito: *"o desconto do cupom vale só sobre os produtos. Ele
nunca desconta o frete. Se o cupom for maior que o subtotal, o desconto para no
subtotal"*. O teto correto é o subtotal, não o total.

O defeito é **silencioso quando `cupom <= subtotal`** — nesse caso os dois
tetos dão o mesmo resultado. Ele só aparece em cupom alto sobre pedido pequeno,
que é exatamente o cenário do chamado. Por isso passou um ano sem ser notado e
por isso os testes de fumaça não o pegam.

**Reprodução no código original:**

| Pedido | Subtotal | Frete | Cupom | Antes | Correto | Perda |
|---|---|---|---|---|---|---|
| 102 | 70 | 20 | 120 | **0,00** | 20,00 | R$ 20,00 |
| 107 | 50 | 30 | 200 | **0,00** | 30,00 | R$ 30,00 |

Em ambos o frete foi zerado pelo cupom — o dinheiro que estava saindo do caixa.

### Solução

O teto do desconto passou a ser o **subtotal de produtos**, e o frete passou a
ser somado **depois** de aplicado o desconto, espelhando a fórmula do
`REGRAS.md` (`total = (subtotal − desconto) + frete − estornos`):

```python
frete = 0.0 if subtotal >= 150 else frete_cheio

desconto = min(cupom, subtotal)   # o cupom só alcança os produtos
if desconto < 0:
    desconto = 0.0

total = (subtotal - desconto) + frete - estornado
```

Isso resolve porque o frete deixa de estar dentro da base que o cupom pode
consumir: por maior que seja o cupom, `subtotal - desconto` nunca fica abaixo
de zero, e o `+ frete` que vem depois chega intacto ao total. O pedido 102
passa a devolver 20,00 e o 107, 30,00 — o frete cheio, como manda a regra.

A guarda `desconto < 0` impede que um cupom negativo (dado por erro de
cadastro) seja somado ao total em vez de descontado.

Pontos preservados, verificados por teste:

- **Frete grátis** continua decidido pelo subtotal **antes** do cupom
  (`subtotal >= 150`), inclusive no limite exato de 150 — o cupom não muda
  quem tem direito a frete grátis.
- **Estornos** continuam subtraídos do total e são somados em consulta
  separada dos itens, sem o fan-out que o `JOIN` de itens × estornos causaria
  (o pedido 104 tem dois estornos e segue em 75,00).
- Pedido sem cupom (101) e pedido sem itens seguem inalterados.

---

## Problema 2 — Relatório de clientes (`loja/relatorios.py`)

### Causa raiz

O erro está na **cláusula `WHERE p.feito_em >= '2026-01-01'`** aplicada sobre a
tabela do lado direito de um `LEFT JOIN`.

```sql
FROM clientes c
LEFT JOIN pedidos p ON p.cliente_id = c.id
WHERE p.feito_em >= '2026-01-01'     -- <-- anula o LEFT JOIN
```

O `LEFT JOIN` faz seu trabalho corretamente: o cliente sem pedido no período
sobrevive ao join, com todas as colunas de `pedidos` preenchidas com `NULL`.
O problema é o que vem depois. O `WHERE` é avaliado **após** o join, e a
comparação `NULL >= '2026-01-01'` não resulta em verdadeiro nem em falso, mas
em `NULL` — e o `WHERE` só mantém a linha quando a condição é verdadeira. Toda
linha sem pedido correspondente é descartada.

O efeito é que o `LEFT JOIN` **degrada para um `INNER JOIN`**: só sobra quem
tem pedido dentro da janela. É por isso que os dois perfis do chamado somem
juntos — o cliente novo (nunca comprou, `NULL`) e o cliente antigo (comprou só
em 2025, a data existe mas não passa no filtro) caem pelo mesmo motivo.

O `CHANGELOG.md` mostra quando o defeito entrou: o filtro de ano foi adicionado
em **2025-08** ("relatório passou a contar só pedidos do ano corrente") e
refixado em **2026-01**. A consulta original, sem filtro, estava correta; o
filtro foi acrescentado no lugar errado da consulta.

**Reprodução no código original** — 4 clientes de 7, faltando 3:

```
[('Ana Batista', ..., 2), ('Bruno Callado', ..., 1),
 ('Célia Marques', ..., 1), ('Steve Alex', ..., 2)]
```

Sumiram **Davi Nogueira** e **Ort O'Brien** (nunca fizeram pedido) e
**Lara Vidal** (só tem o pedido 106, de 2025-12-30).

### Solução

O filtro de data foi movido do `WHERE` para a condição `ON` do próprio join:

```sql
FROM clientes c
LEFT JOIN pedidos p
       ON p.cliente_id = c.id
      AND p.feito_em >= '2026-01-01'
GROUP BY c.id, c.nome, c.cidade
ORDER BY c.nome
```

Isso resolve porque muda **quando** a data é avaliada. No `ON`, a condição
decide apenas *quais pedidos casam* com o cliente — é parte do critério de
pareamento, executado durante o join. O cliente cujos pedidos não casam não é
eliminado: ele permanece na saída com as colunas de `pedidos` em `NULL`, que é
precisamente a garantia que o `LEFT JOIN` oferece e que o `WHERE` estava
desfazendo.

O `COUNT(p.id)` completa a correção: `COUNT` de uma coluna ignora `NULL`, então
o cliente sem pedido pareado conta **0**, e não 1 — resultado que um
`COUNT(*)` (que conta linhas, inclusive a linha com `NULL`) daria errado.

O relatório passa a devolver os **7 clientes**, com Davi, Ort e Lara em 0:

```
Ana Batista 2 · Bruno Callado 1 · Célia Marques 1 · Davi Nogueira 0
Lara Vidal 0 · Ort O'Brien 0 · Steve Alex 2
```

Pontos preservados, verificados por teste:

- A **janela de 2026 continua valendo**: o pedido de 2025 da Lara não é contado
  (ela aparece com 0, não com 1). Corrigir a ausência não podia virar contar
  tudo.
- O corte é **inclusivo em 01/01/2026** e exclusivo em 31/12/2025 — as datas
  estão em `AAAA-MM-DD`, formato em que a comparação textual coincide com a
  cronológica.
- Formato `(nome, cidade, qtd_pedidos)` e a **ordem por nome** seguem iguais.
- O `GROUP BY` passou a listar as três colunas não agregadas em vez de só
  `c.id`, evitando depender da extensão de "coluna solta" do SQLite.

---

## Problema 3 — Busca por e-mail (`loja/clientes.py`)

### Causa raiz

O erro está na **construção da consulta por concatenação de texto**:

```python
sql = "SELECT id, nome, cidade FROM clientes WHERE email = '%s'" % email
linha = conn.execute(sql).fetchone()
```

O e-mail digitado pelo usuário é interpolado **dentro do texto do SQL** antes de
o banco receber a consulta. Nesse momento o dado deixa de ser dado: o que o
SQLite recebe é uma única string em que não há mais fronteira entre o comando
escrito pelo programador e o conteúdo digitado por quem usa o sistema. As aspas
que deveriam delimitar o valor são apenas mais dois caracteres do texto, e quem
digita pode fechá-las.

Os dois sintomas do chamado são **a mesma falha**, vista de dois lados:

1. **E-mail forjado (injeção de SQL).** Digitando `x' OR '1'='1`, a consulta
   montada vira `WHERE email = 'x' OR '1'='1'` — uma condição sempre verdadeira.
   O sistema devolve o primeiro cliente da tabela. Reproduzido no código
   original: retornou `(1, 'Ana Batista', 'Juazeiro do Norte')` para um e-mail
   que não existe. Pela mesma porta passam `UNION SELECT` para ler outras
   tabelas e `;` para encadear comandos.

2. **Apóstrofo legítimo.** `o'brien@cariri.test` (cliente 6, que existe no
   banco) monta `WHERE email = 'o'brien@cariri.test'`. O apóstrofo do nome
   fecha a string cedo e o resto vira sintaxe inválida. Reproduzido:
   `sqlite3.OperationalError: near "brien": syntax error`.

A causa raiz de ambos é **não separar código de dado**. Escapar aspas
manualmente não é solução: trata o sintoma, mantém o dado no texto do comando e
historicamente sempre deixa um caminho aberto.

### Solução

A consulta passou a ser **parametrizada** (*bind parameter*), com o e-mail
enviado como valor, fora do texto do SQL:

```python
sql = "SELECT id, nome, cidade FROM clientes WHERE email = ?"
linha = conn.execute(sql, (email,)).fetchone()
```

Isso resolve porque restaura a fronteira entre comando e dado. O texto do SQL
vai ao banco **completo e fixo**, e é compilado antes de o valor entrar. O
`?` é um espaço reservado no plano já compilado; o driver `sqlite3` entrega o
e-mail no lugar dele como um valor único. Não existe etapa em que o conteúdo
digitado possa ser lido como sintaxe — nem aspas, nem `OR`, nem `;`, nem
`--` têm qualquer efeito estrutural. A defesa não depende de prever quais
caracteres são perigosos, e sim de o dado nunca ser interpretado.

Os dois sintomas caem juntos, pelo mesmo motivo:

- `x' OR '1'='1`, `' OR 1=1 --`, `x' UNION SELECT ... --` e
  `x'; DROP TABLE clientes; --` passam a ser tratados como e-mails literais.
  Nenhum casa com registro nenhum, e a função devolve `None` — que é a resposta
  certa para um e-mail que não existe. A tabela `clientes` segue intacta.
- `o'brien@cariri.test` volta a funcionar e devolve
  `(6, "Ort O'Brien", "Crato")`. O apóstrofo é só um caractere do dado.

Pontos preservados, verificados por teste:

- Busca de e-mail existente devolve `(id, nome, cidade)`; e-mail inexistente e
  string vazia devolvem `None` — contrato inalterado.
- Teste que percorre **os 7 clientes do banco** e confirma que cada um é
  encontrado pelo seu próprio e-mail.
- Nenhuma normalização (minúsculas, corte de espaços) foi introduzida: o
  `REGRAS.md` não a prevê, e acrescentá-la mudaria o comportamento da busca em
  vez de apenas torná-la segura.

---

## Resumo

| # | Arquivo | Causa raiz | Correção |
|---|---|---|---|
| 1 | `loja/precos.py` | teto do cupom ancorado em `subtotal + frete`, permitindo que o cupom consumisse o frete | teto passou a ser o subtotal; frete somado após o desconto |
| 2 | `loja/relatorios.py` | filtro de data no `WHERE` sobre a tabela à direita do `LEFT JOIN`, que o degradava para `INNER JOIN` | filtro movido para o `ON`; `COUNT(p.id)` mantém o zero |
| 3 | `loja/clientes.py` | e-mail concatenado no texto do SQL: código e dado sem fronteira | consulta parametrizada com `?` e passagem por valor |
