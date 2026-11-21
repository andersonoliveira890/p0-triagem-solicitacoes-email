# Nível Avançado: parâmetros configuráveis e registros (21/11/2026)

## Parâmetros adicionados ao `.env`

| Variável | Padrão | Por quê |
|---|---|---|
| `LLM_TEMPERATURE` | 0.2 | Extração de dados pede respostas estáveis; no Básico (temperatura padrão do modelo) o mesmo e-mail teve prazos diferentes entre execuções |
| `LLM_MAX_TOKENS` | 512 | Suficiente para vários pedidos e impede respostas sem fim |
| `LLM_TIMEOUT` | 120 | Já existia desde o Intermediário |

Os valores chegam ao Ollama no campo `options` (`temperature`, `num_predict`).
Valores inválidos geram `ErroTriagem` com mensagem clara.

## Registros (`logs/triagem.log`, fora do Git)

Gravam apenas metadados: início, origem da entrada, parâmetros, modelo,
servidor (host), tamanho do e-mail em caracteres, status HTTP, tempo de resposta,
tamanho e formato do resultado, erros tratados. **Não** gravam o texto do e-mail,
a resposta do modelo nem a chave (só "definida"/"não definida").

## Testes

| Teste | Resultado |
|---|---|
| E-mail 03 com temperatura 0.2 | SIM, 3 pedidos, prazos corretos, **solicitante agora identificado** ("Jurídico - Gestora Beta"; no Básico vinha "não identificado") |
| `LLM_TEMPERATURE=5` | "LLM_TEMPERATURE inválido: '5'. Use um número entre 0 e 2." |
| `LLM_MAX_TOKENS=abc` | "LLM_MAX_TOKENS inválido: 'abc'. Use um número inteiro maior que zero." |
| Servidor desligado | Mensagem de conexão; registrado no log como erro tratado |

## Falha real observada: erro 500 por falta de memória

Na primeira execução do dia o Ollama respondeu **HTTP 500** após 10,9 s. A RAM
livre do computador estava em 0,5 GB. Uma chamada direta logo depois funcionou,
e a execução seguinte também. Interpretação: o modelo não conseguiu ser carregado
na memória na primeira tentativa (o processo `llama-server` ocupa ~2,7 GB).

- **Como foi identificado:** mensagem tratada "servidor indisponível (erro 500)"
  + registro no log com o tempo da chamada.
- **Tratamento:** o programa já encerrava de forma controlada; a mensagem orienta
  a tentar novamente.
- **Por que permanece:** é limitação de hardware (7,8 GB de RAM). Recomenda-se
  fechar programas pesados antes de usar o modelo local.
