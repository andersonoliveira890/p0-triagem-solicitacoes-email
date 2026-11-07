"""Triagem de solicitações em e-mails (P0 - nível Básico).

Lê o texto de um e-mail pelo terminal (ou de um arquivo .txt), envia ao LLM
e mostra se o e-mail contém solicitações e quais são elas.

Uso:
    python main.py                       # cola o e-mail no terminal
    python main.py exemplos/email_01.txt # lê o e-mail de um arquivo
"""

import os
import sys

import requests
from dotenv import load_dotenv

INSTRUCOES = """Você é um assistente de uma consultoria que acompanha fundos FIDC e CRI.
Você recebe e-mails de construtoras e da gestora. Sua tarefa é dizer se o e-mail
contém alguma SOLICITAÇÃO (algo que a consultoria precisa fazer, enviar, verificar
ou responder) e, se contiver, listar cada pedido.

Responda EXATAMENTE neste formato, sem texto antes ou depois:

SOLICITACAO: SIM ou NAO
SOLICITANTE: <quem pediu, ou "não identificado">
PEDIDOS:
- <descrição curta do pedido> | prazo: <prazo citado no e-mail ou "não informado">

Se SOLICITACAO for NAO, escreva "PEDIDOS: nenhum".
Não invente pedidos nem prazos que não estejam no e-mail."""


def ler_email() -> str:
    """Lê o e-mail de um arquivo (se informado) ou do terminal."""
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as arquivo:
            return arquivo.read()

    print("Cole o texto do e-mail e, ao final, digite FIM em uma linha sozinha:")
    linhas = []
    for linha in sys.stdin:
        if linha.strip() == "FIM":
            break
        linhas.append(linha)
    return "".join(linhas)


def main() -> None:
    load_dotenv()
    base_url = os.environ["LLM_BASE_URL"]
    modelo = os.environ["LLM_MODEL"]
    chave = os.getenv("LLM_API_KEY")

    email = ler_email()

    cabecalhos = {"Content-Type": "application/json"}
    if chave:
        cabecalhos["Authorization"] = f"Bearer {chave}"

    # API de chat do Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md
    corpo = {
        "model": modelo,
        "stream": False,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {"role": "user", "content": email},
        ],
    }

    resposta = requests.post(
        f"{base_url.rstrip('/')}/api/chat",
        json=corpo,
        headers=cabecalhos,
        timeout=120,
    )
    resposta.raise_for_status()

    texto = resposta.json()["message"]["content"]
    print("\n===== Resultado da triagem =====")
    print(texto.strip())


if __name__ == "__main__":
    main()
