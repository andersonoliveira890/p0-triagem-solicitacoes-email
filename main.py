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

Situações previsíveis (entrada vazia, configuração ausente, servidor fora do
ar, timeout etc.) geram um ErroTriagem com uma mensagem compreensível, que é
exibida ao usuário no lugar do erro técnico do Python.
"""

import os
import re
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

TIMEOUT_PADRAO = 120  # segundos; o modelo local em CPU pode levar ~1 minuto


class ErroTriagem(Exception):
    """Erro previsível, com mensagem pronta para ser mostrada ao usuário."""


# 1. Entrada ----------------------------------------------------------------

def ler_entrada(argumentos: list[str]) -> str:
    """Lê o e-mail de um arquivo (se informado nos argumentos) ou do terminal."""
    if len(argumentos) > 1:
        caminho = argumentos[1]
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                texto = arquivo.read()
        except FileNotFoundError:
            raise ErroTriagem(f"Arquivo não encontrado: {caminho}")
        except UnicodeDecodeError:
            raise ErroTriagem(
                f"Não foi possível ler {caminho}. Salve o arquivo como texto UTF-8."
            )
    else:
        print("Cole o texto do e-mail e, ao final, digite FIM em uma linha sozinha:")
        linhas = []
        for linha in sys.stdin:
            if linha.strip() == "FIM":
                break
            linhas.append(linha)
        texto = "".join(linhas)

    return validar_entrada(texto)


def validar_entrada(texto: str) -> str:
    """Impede o envio de entradas vazias (ou só com espaços) ao modelo."""
    if not texto.strip():
        raise ErroTriagem(
            "O e-mail está vazio. Informe o texto do e-mail que deseja analisar."
        )
    return texto


# 2. Configuração -----------------------------------------------------------

def carregar_config() -> dict:
    """Lê do ambiente (.env) o endereço do servidor, o modelo e a chave opcional."""
    load_dotenv()

    base_url = os.getenv("LLM_BASE_URL", "").strip()
    modelo = os.getenv("LLM_MODEL", "").strip()

    faltando = [nome for nome, valor in
                (("LLM_BASE_URL", base_url), ("LLM_MODEL", modelo)) if not valor]
    if faltando:
        raise ErroTriagem(
            "Configuração ausente: " + ", ".join(faltando) + ". "
            "Copie o arquivo .env.example para .env e preencha os valores."
        )

    if not base_url.startswith(("http://", "https://")):
        raise ErroTriagem(
            f"LLM_BASE_URL inválida: '{base_url}'. "
            "O endereço deve começar com http:// ou https://."
        )

    timeout_texto = os.getenv("LLM_TIMEOUT", "").strip()
    try:
        timeout = float(timeout_texto) if timeout_texto else TIMEOUT_PADRAO
        if timeout <= 0:
            raise ValueError
    except ValueError:
        raise ErroTriagem(
            f"LLM_TIMEOUT inválido: '{timeout_texto}'. Use um número de segundos maior que zero."
        )

    return {
        "base_url": base_url,
        "modelo": modelo,
        "chave": os.getenv("LLM_API_KEY", "").strip() or None,
        "timeout": timeout,
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

def chamar_modelo(url: str, cabecalhos: dict, corpo: dict, timeout: float) -> dict:
    """Envia a requisição ao servidor do LLM e devolve o JSON da resposta.

    Traduz as falhas de comunicação em mensagens compreensíveis. A chave de
    acesso nunca é incluída nas mensagens.
    """
    try:
        resposta = requests.post(url, json=corpo, headers=cabecalhos, timeout=timeout)
    except requests.exceptions.ConnectionError:
        raise ErroTriagem(
            f"Não foi possível conectar ao servidor do LLM ({url}). "
            "Verifique se o servidor está ligado (no Ollama local: abra o aplicativo "
            "Ollama) e se LLM_BASE_URL está correta."
        )
    except requests.exceptions.Timeout:
        raise ErroTriagem(
            f"O servidor do LLM não respondeu em {timeout:.0f} segundos. "
            "Tente novamente ou aumente LLM_TIMEOUT no .env."
        )
    except requests.exceptions.RequestException:
        raise ErroTriagem("Falha de comunicação com o servidor do LLM. Tente novamente.")

    status = resposta.status_code
    if status in (401, 403):
        if "Authorization" in cabecalhos:
            raise ErroTriagem(
                "Credencial inválida: o servidor recusou a chave informada em "
                "LLM_API_KEY. Confira a chave no .env."
            )
        raise ErroTriagem(
            "Credencial ausente: o servidor exige uma chave de acesso. "
            "Informe LLM_API_KEY no .env."
        )
    if status == 404:
        raise ErroTriagem(
            f"O servidor não encontrou o modelo '{corpo['model']}' ou o endereço da API. "
            "Confira LLM_MODEL e LLM_BASE_URL (no Ollama local: ollama list)."
        )
    if status >= 500:
        raise ErroTriagem(
            f"O servidor do LLM está indisponível no momento (erro {status}). "
            "Tente novamente em alguns minutos."
        )
    if status >= 400:
        raise ErroTriagem(f"O servidor do LLM recusou a solicitação (erro {status}).")

    try:
        return resposta.json()
    except ValueError:
        raise ErroTriagem("O servidor do LLM devolveu uma resposta em formato inesperado.")


# 5. Tratamento da resposta -------------------------------------------------

def extrair_texto(dados: dict) -> str:
    """Extrai o texto gerado pelo modelo do JSON devolvido pelo Ollama."""
    try:
        texto = dados["message"]["content"]
    except (KeyError, TypeError):
        raise ErroTriagem("O servidor do LLM devolveu uma resposta em formato inesperado.")

    if not isinstance(texto, str) or not texto.strip():
        raise ErroTriagem("O modelo devolveu uma resposta vazia. Tente novamente.")
    return texto.strip()


def resposta_no_formato(texto: str) -> bool:
    """Confere se o texto do modelo começa pela linha 'SOLICITACAO: SIM/NAO'."""
    return re.match(r"^\s*SOLICITACAO:\s*(SIM|NAO)\b", texto, re.IGNORECASE) is not None


# 6. Apresentação -----------------------------------------------------------

def exibir_resultado(texto: str) -> None:
    """Mostra o resultado da triagem no terminal."""
    print("\n===== Resultado da triagem =====")
    if not resposta_no_formato(texto):
        print("[Atenção] O modelo respondeu fora do formato esperado. "
              "Confira o texto abaixo manualmente.\n")
    print(texto)


def main() -> int:
    try:
        email = ler_entrada(sys.argv)
        config = carregar_config()
        url, cabecalhos, corpo = montar_requisicao(email, config)
        dados = chamar_modelo(url, cabecalhos, corpo, config["timeout"])
        texto = extrair_texto(dados)
        exibir_resultado(texto)
        return 0
    except ErroTriagem as erro:
        print(f"\n[Erro] {erro}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nExecução cancelada pelo usuário.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
