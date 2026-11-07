# Resultados do nível Básico (rascunho para o RELATORIO_EXECUCAO.md)

Execução real em 07/11/2026 com Ollama local 0.40.15, modelo `qwen3.5:4b-q4_K_M`,
CPU Intel i3-10110U, 7,8 GB RAM, sem GPU. `think: false`.

| E-mail | Classificação esperada | Obtida | Observação | Tempo |
|---|---|---|---|---|
| 01 pedido explícito | SIM, prazo 14/11 | SIM | **Errou o prazo** ("não informado"); solicitante veio entre `< >` | 29 s |
| 02 pedido implícito | SIM | SIM | Pedido implícito reconhecido; prazo "esta semana (até segunda-feira)" | 30 s |
| 03 vários pedidos | SIM, 3 pedidos | SIM, 3 pedidos | Prazos corretos; **solicitante "não identificado"** (era Jurídico - Gestora Beta) | 44 s |
| 04 informativo | NAO | NAO | Linha SOLICITANTE omitida (fora do formato) | 20 s |
| 05 agradecimento | NAO | NAO | Linha SOLICITANTE omitida (fora do formato) | 17 s |
| 06 prazo relativo | SIM, 2 pedidos | SIM, 2 pedidos | "próxima semana" ficou na descrição, prazo "não informado" | 29 s |

## Conclusões

- Classificação SIM/NAO correta em 6 de 6 casos.
- Falhas na extração: prazo perdido (01), solicitante não identificado (03),
  prazo relativo fora do campo (06).
- O modelo nem sempre segue o formato (SOLICITANTE omitido, `< >` copiado do modelo do prompt).
  → No Intermediário: validar o formato da resposta e tratar desvios; ajustar o prompt
  (exemplo concreto em vez de `<placeholder>`).
