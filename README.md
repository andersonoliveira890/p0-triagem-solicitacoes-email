# Triagem de solicitações em e-mails (FIDC / CRI)

Projeto P0 — Primeiro fluxo com LLM (capacitação TrendsIA / Instituto Hardware Br).

> **Status:** nível Básico em construção. Este README será completado nos níveis
> Intermediário e Avançado.

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

## Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
copy .env.example .env
```

(no Linux/macOS: `cp .env.example .env`)

| Variável | Descrição |
|---|---|
| `LLM_BASE_URL` | Endereço do servidor Ollama do LLM institucional |
| `LLM_MODEL` | Nome do modelo (ex.: `qwen3.5:9b-q4_K_M`) |
| `LLM_API_KEY` | Chave de acesso, se o ambiente exigir; caso contrário, deixe vazio |

## Execução

Lendo um e-mail de arquivo:

```bash
python main.py exemplos/email_03_varios_pedidos.txt
```

Colando o e-mail no terminal (termine com uma linha contendo apenas `FIM`):

```bash
python main.py
```

## Exemplo de saída esperada

```
===== Resultado da triagem =====
SOLICITACAO: SIM
SOLICITANTE: Jurídico - Gestora Beta
PEDIDOS:
- Encaminhar a carteira de recebíveis atualizada | prazo: 10/11
- Confirmar a verificação de lastro por amostragem | prazo: não informado
- Revisar a minuta do aditamento e enviar comentários | prazo: 5 dias úteis
```
