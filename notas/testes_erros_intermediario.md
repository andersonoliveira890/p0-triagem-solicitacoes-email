# Testes de tratamento de erros (nível Intermediário)

Executados em 13/11/2026 na branch `desenvolvimento`.

- **Real:** contra o Ollama local (qwen3.5:4b-q4_K_M) ou provocado de verdade
  (arquivo inexistente, servidor desligado etc.).
- **Simulado:** contra um servidor HTTP falso que imita respostas do Ollama.
  Usado porque o Ollama local não exige chave e não produz esses erros sob demanda.

| # | Cenário | Tipo | Como foi provocado | Resultado esperado | Resultado obtido |
|---|---|---|---|---|---|
| 1 | Entrada válida | Real | `email_01_pedido_explicito.txt` | Resposta útil do modelo | SIM, 1 pedido, prazo 14/11 ✅ |
| 2 | Entrada vazia | Real | Arquivo vazio | Envio impedido, orientação | "O e-mail está vazio..." ✅ |
| 3 | Entrada só com espaços | Real | Arquivo com espaços/quebras | Envio impedido | Mesma mensagem ✅ |
| 4 | Arquivo inexistente | Real | `nao_existe.txt` | Mensagem clara | "Arquivo não encontrado" ✅ |
| 5 | Configuração ausente | Real | `LLM_MODEL` vazio | Indica a variável que falta | "Configuração ausente: LLM_MODEL..." ✅ |
| 6 | Configuração inválida | Real | `LLM_BASE_URL=localhost:11434` | Indica o problema | "LLM_BASE_URL inválida..." ✅ |
| 7 | Timeout inválido | Real | `LLM_TIMEOUT=abc` | Indica o problema | "LLM_TIMEOUT inválido..." ✅ |
| 8 | Servidor desligado / falha de comunicação | Real | Porta sem servidor | Mensagem compreensível | "Não foi possível conectar..." ✅ |
| 9 | Modelo inexistente | Real | `LLM_MODEL=modelo-que-nao-existe` | Mensagem clara | "O servidor não encontrou o modelo..." ✅ |
| 10 | Credencial ausente | Simulado | Servidor responde 401, sem chave | Informa sem expor segredo | "Credencial ausente..." ✅ |
| 11 | Credencial inválida | Simulado | Servidor responde 401, com chave falsa | Encerra de forma controlada, sem mostrar a chave | "Credencial inválida..." (chave não aparece) ✅ |
| 12 | LLM indisponível | Simulado | Servidor responde 500 | Mensagem compreensível | "...indisponível no momento (erro 500)" ✅ |
| 13 | Timeout | Simulado | Servidor demora 5 s, limite 2 s | Mensagem compreensível | "...não respondeu em 2 segundos" ✅ |
| 14 | Resposta não-JSON | Simulado | Servidor devolve HTML | Formato inesperado | "...resposta em formato inesperado" ✅ |
| 15 | JSON sem o campo esperado | Simulado | `{"done": true}` | Formato inesperado | Mesma mensagem ✅ |
| 16 | Resposta vazia | Simulado | `content` só com espaços | Mensagem compreensível | "O modelo devolveu uma resposta vazia" ✅ |
| 17 | Texto fora do formato | Simulado | Modelo responde texto livre | Aviso para conferir | "[Atenção] ...fora do formato esperado" ✅ |

Em todos os casos de erro o programa termina com código de saída 1, sem traceback.
