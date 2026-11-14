"""Triagem de solicitações em e-mails (P0).

Lê o texto de um e-mail pelo terminal (ou de um arquivo .txt), envia ao LLM
e mostra se o e-mail contém solicitações e quais são elas.

Uso:
    python main.py                       # cola o e-mail no terminal
    python main.py exemplos/email_01.txt # lê o e-mail de um arquivo

O fluxo é dividido em seis etapas, cada uma em sua própria função:
    1. ler_entrada        -> obtém o texto do e-mail
    2. carregar_config    -> lê as variáveis de ambiente (.env)
    3. montar_requisicao  -> prepara o corpo e os cabeçalhos da chamada
    4. chamar_modelo      -> envia a requisição HTTP ao servidor do LLM
    5. extrair_texto      -> tira o texto útil da resposta JSON
    6. exibir_resultado   -> mostra o resultado ao usuário
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


# 1. Entrada ----------------------------------------------------------------

def ler_entrada(argumentos: list[str]) -> str:
    """Lê o e-mail de um arquivo (se informado nos argumentos) ou do terminal."""
    if len(argumentos) > 1:
        with open(argumentos[1], encoding="utf-8") as arquivo:
            return arquivo.read()

    print("Cole o texto do e-mail e, ao final, digite FIM em uma linha sozinha:")
    linhas = []
    for linha in sys.stdin:
        if linha.strip() == "FIM":
            break
        linhas.append(linha)
    return "".join(linhas)


# 2. Configuração -----------------------------------------------------------

def carregar_config() -> dict:
    """Lê do ambiente (.env) o endereço do servidor, o modelo e a chave opcional."""
    load_dotenv()
    return {
        "base_url": os.environ["LLM_BASE_URL"],
        "modelo": os.environ["LLM_MODEL"],
        "chave": os.getenv("LLM_API_KEY"),
    }


# 3. Preparação da solicitação ----------------------------------------------

def montar_requisicao(email: str, config: dict) -> tuple[str, dict, dict]:
    """Devolve a URL, os cabeçalhos e o corpo da chamada à API de chat do Ollama.

    Documentação da API: https://github.com/ollama/ollama/blob/main/docs/api.md
    """
    url = f"{config['base_url'].rstrip('/')}/api/chat"

    cabecalhos = {"Content-Type": "application/json"}
    if config["chave"]:
        cabecalhos["Authorization"] = f"Bearer {config['chave']}"

    corpo = {
        "model": config["modelo"],
        "stream": False,
        # O qwen3.5 "pensa" antes de responder; desligar deixa a resposta
        # muito mais rápida e a tarefa não precisa desse raciocínio.
        "think": False,
        "messages": [
            {"role": "system", "content": INSTRUCOES},
            {"role": "user", "content": email},
        ],
    }
    return url, cabecalhos, corpo


# 4. Chamada ao modelo ------------------------------------------------------

def chamar_modelo(url: str, cabecalhos: dict, corpo: dict) -> dict:
    """Envia a requisição ao servidor do LLM e devolve o JSON da resposta."""
    resposta = requests.post(url, json=corpo, headers=cabecalhos, timeout=120)
    resposta.raise_for_status()
    return resposta.json()


# 5. Tratamento da resposta -------------------------------------------------

def extrair_texto(dados: dict) -> str:
    """Extrai o texto gerado pelo modelo do JSON devolvido pelo Ollama."""
    return dados["message"]["content"].strip()


# 6. Apresentação -----------------------------------------------------------

def exibir_resultado(texto: str) -> None:
    """Mostra o resultado da triagem no terminal."""
    print("\n===== Resultado da triagem =====")
    print(texto)


def main() -> None:
    email = ler_entrada(sys.argv)
    config = carregar_config()
    url, cabecalhos, corpo = montar_requisicao(email, config)
    dados = chamar_modelo(url, cabecalhos, corpo)
    texto = extrair_texto(dados)
    exibir_resultado(texto)


if __name__ == "__main__":
    main()
