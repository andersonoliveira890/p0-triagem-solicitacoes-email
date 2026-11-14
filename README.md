# Triagem de solicitações em e-mails (FIDC / CRI)

Projeto P0 — Primeiro fluxo com LLM (capacitação TrendsIA / Instituto Hardware Br).

> **Status:** nível Intermediário em construção (Básico concluído na tag
> `p0-basico`). Este README será completado no nível Avançado.

## Problema

Uma equipe de consultoria que acompanha fundos e operações de **FIDC** e **CRI**
recebe diariamente dezenas de e-mails de construtoras e da gestora. Muitos são
apenas informativos ("segue o comprovante", "recebido, obrigado"); outros trazem
pedidos que exigem ação, com prazo. Hoje é preciso ler um por um para descobrir
o que precisa ser feito.

**Usuário:** analista da consultoria responsável pela caixa de entrada.

**Entrada:** o texto de um e-mail (remetente, assunto e corpo).

**Saída:** se o e-mail contém solicitação e, em caso afirmativo, a lista de
pedidos com o solicitante e o prazo.

## Por que usar um LLM

Os pedidos aparecem em linguagem livre e muitas vezes implícita ("seria possível
nos posicionar…", "aguardamos o retorno…"), enquanto e-mails informativos usam
palavras parecidas. Prazos também vêm em formatos variados ("até 14/11",
"esta semana", "em 5 dias úteis"). Regras fixas por palavra-chave erram nos dois
sentidos; interpretar a intenção do texto é uma tarefa de linguagem.

O programa tem papel **informativo**: ele sugere a lista e o analista confere.

## Como funciona

O programa lê um e-mail, envia ao LLM junto com uma instrução de formato e mostra
a resposta. O fluxo está dividido em seis funções em [`main.py`](main.py):

| Etapa | Função | Responsabilidade |
|---|---|---|
| 1 | `ler_entrada` | Lê o e-mail de um arquivo ou do terminal e impede entradas vazias |
| 2 | `carregar_config` | Lê e valida as variáveis do `.env` |
| 3 | `montar_requisicao` | Monta a URL, os cabeçalhos e o corpo da chamada |
| 4 | `chamar_modelo` | Envia a requisição ao servidor do LLM e trata falhas de comunicação |
| 5 | `extrair_texto` | Extrai o texto da resposta e trata respostas vazias ou inesperadas |
| 6 | `exibir_resultado` | Mostra o resultado e avisa se o modelo fugiu do formato |

Situações previsíveis (entrada vazia, configuração ausente, servidor fora do ar,
timeout, credencial recusada, resposta inesperada) geram uma mensagem
compreensível e encerram o programa com código de saída `1`, sem expor a chave
de acesso.

## Estrutura do repositório

```
.
├── main.py              # aplicação (todo o fluxo)
├── requirements.txt     # dependências Python
├── .env.example         # modelo de configuração, sem segredos
├── .gitignore           # impede versionar .env, ambiente virtual etc.
├── exemplos/            # e-mails fictícios usados nos testes
└── notas/               # registros de execução e de testes (base do relatório)
```

## Dados

Todos os e-mails em [`exemplos/`](exemplos/) são **fictícios** (empresas,
empreendimentos, nomes e valores inventados). Nenhum e-mail real de cliente é
publicado neste repositório.

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
```

Windows (PowerShell):

```bash
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## LLM utilizado

A aplicação usa a API de chat do [Ollama](https://ollama.com) (`POST /api/chat`)
e funciona com dois servidores, trocando apenas o `.env`:

| Ambiente | Servidor | Modelo | Uso |
|---|---|---|---|
| Local | Ollama instalado na máquina (`http://localhost:11434`) | `qwen3.5:4b-q4_K_M` | desenvolvimento e testes |
| Institucional | LLM do Devel (`https://llm-internal.softex:9001`) | `qwen3.5:9b-q4_K_M` | demonstração; acessível somente de dentro de um container no portal Devel |

O modelo de 9B (6,6 GB) não cabe na memória da máquina de desenvolvimento
(7,8 GB de RAM, sem GPU dedicada); por isso, localmente é usada a versão de 4B
da mesma família.

### Preparar o Ollama local

1. Instale o Ollama: <https://ollama.com/download> (no Windows também é possível
   usar `winget install Ollama.Ollama`).
2. Baixe o modelo (cerca de 3,3 GB):

```bash
ollama pull qwen3.5:4b-q4_K_M
```

## Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
copy .env.example .env
```

(no Linux/macOS: `cp .env.example .env`)

| Variável | Descrição |
|---|---|
| `LLM_BASE_URL` | Endereço do servidor Ollama (local ou institucional) |
| `LLM_MODEL` | Nome do modelo (ex.: `qwen3.5:4b-q4_K_M`) |
| `LLM_TIMEOUT` | Tempo máximo de espera pela resposta, em segundos (opcional; padrão `120`) |
| `LLM_API_KEY` | Chave de acesso, se o servidor exigir; o Ollama local e o Devel não exigem, deixe vazio |

Antes de executar, confirme que o Ollama está rodando (o aplicativo Ollama aberto
ou `ollama serve`) e que o modelo aparece em:

```bash
ollama list
```

## Execução

Lendo um e-mail de arquivo:

```bash
python main.py exemplos/email_03_varios_pedidos.txt
```

Colando o e-mail no terminal (termine com uma linha contendo apenas `FIM`):

```bash
python main.py
```

Com o modelo local em CPU, cada e-mail leva de 15 a 60 segundos.

## Exemplos de entrada e saída

Saídas reais obtidas com `qwen3.5:4b-q4_K_M`. Como o LLM não é determinístico,
o texto pode variar um pouco entre execuções.

**E-mail com vários pedidos** ([`exemplos/email_03_varios_pedidos.txt`](exemplos/email_03_varios_pedidos.txt)):

```
===== Resultado da triagem =====
SOLICITACAO: SIM
SOLICITANTE: não identificado
PEDIDOS:
- Encaminhar a carteira de recebíveis atualizada | prazo: 10/11
- Confirmar a verificação de lastro por amostragem | prazo: não informado
- Enviar comentários sobre a minuta do aditamento | prazo: 5 dias úteis
```

**E-mail apenas informativo** ([`exemplos/email_04_informativo.txt`](exemplos/email_04_informativo.txt)):

```
===== Resultado da triagem =====
SOLICITACAO: NAO
PEDIDOS: nenhum
```

**Exemplos de erro:**

```
[Erro] O e-mail está vazio. Informe o texto do e-mail que deseja analisar.
```

```
[Erro] Não foi possível conectar ao servidor do LLM (http://localhost:11434/api/chat).
Verifique se o servidor está ligado (no Ollama local: abra o aplicativo Ollama)
e se LLM_BASE_URL está correta.
```

```
[Erro] Configuração ausente: LLM_MODEL. Copie o arquivo .env.example para .env
e preencha os valores.
```

## Testes

Os testes estão registrados em
[`notas/testes_erros_intermediario.md`](notas/testes_erros_intermediario.md).

- **Testes reais:** executados contra o Ollama local ou provocando a falha de
  verdade (entrada válida, entrada vazia, arquivo inexistente, configuração
  ausente ou inválida, servidor desligado, modelo inexistente).
- **Testes simulados:** executados contra um servidor HTTP falso que imita
  respostas do Ollama (credencial ausente, credencial inválida, erro 500,
  timeout, resposta não-JSON, resposta vazia, texto fora do formato). Foram
  necessários porque o Ollama local não exige chave e não produz esses erros sob
  demanda.

## Limitações conhecidas

- O modelo local de 4B às vezes erra o solicitante ou o prazo, ou foge do
  formato pedido; o programa avisa quando o formato não é reconhecido, mas não
  corrige o conteúdo. O resultado deve ser conferido pelo analista.
- Processa um e-mail por execução.
- O LLM institucional só é acessível de dentro de um container no portal Devel.
