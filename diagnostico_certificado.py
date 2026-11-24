"""Diagnóstico do certificado HTTPS do servidor do LLM (uso no portal Devel).

Mostra a cadeia de certificados que o servidor apresenta: para quem cada
certificado foi emitido, quem o emitiu e a impressão digital SHA-256. Serve para
descobrir qual autoridade certificadora (CA) interna assina o certificado, de
modo que a aplicação possa confiar nela sem desligar a verificação.

A conexão é aberta SEM validar o certificado apenas para LER a cadeia; nenhum
dado é enviado ao servidor. A aplicação principal (main.py) continua sempre
com a verificação ligada.

Uso no container: defina MODO=diagnostico_certificado nas variáveis do portal.
"""

import hashlib
import os
import socket
import ssl
import tempfile
from urllib.parse import urlparse


def descrever(der: bytes) -> dict:
    """Extrai assunto, emissor e validade de um certificado em DER."""
    pem = ssl.DER_cert_to_PEM_cert(der)
    info = {}
    try:
        # API interna do Python que decodifica um certificado salvo em arquivo.
        with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as f:
            f.write(pem)
        dados = ssl._ssl._test_decode_cert(f.name)  # noqa: SLF001
        os.unlink(f.name)
        nome = lambda campos: ", ".join(f"{k}={v}" for rdn in campos for k, v in rdn)
        info = {
            "assunto": nome(dados.get("subject", ())),
            "emissor": nome(dados.get("issuer", ())),
            "valido_ate": dados.get("notAfter", "?"),
        }
    except Exception as erro:  # diagnóstico: não interromper por falha de leitura
        info = {"assunto": f"(não decodificado: {erro})", "emissor": "?", "valido_ate": "?"}
    info["sha256"] = hashlib.sha256(der).hexdigest().upper()
    info["pem"] = pem
    return info


def main() -> None:
    url = urlparse(os.getenv("LLM_BASE_URL", "https://llm-internal.softex:9001"))
    host, porta = url.hostname, url.port or 443
    print(f"Diagnóstico do certificado de {host}:{porta}\n")

    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE  # somente leitura da cadeia

    with socket.create_connection((host, porta), timeout=30) as bruto:
        with contexto.wrap_socket(bruto, server_hostname=host) as tls:
            cadeia = tls.get_unverified_chain()  # Python 3.13+

    print(f"O servidor apresentou {len(cadeia)} certificado(s).\n")
    for i, cert in enumerate(cadeia):
        der = cert if isinstance(cert, bytes) else cert.public_bytes(ssl.ENCODING_DER)
        info = descrever(der)
        autoassinado = info["assunto"] == info["emissor"]
        print(f"--- Certificado {i} {'(autoassinado: provável CA raiz)' if autoassinado else ''}")
        print(f"Assunto : {info['assunto']}")
        print(f"Emissor : {info['emissor']}")
        print(f"Válido até: {info['valido_ate']}")
        print(f"SHA-256 : {info['sha256']}")
        print(info["pem"])

    # Confere se a cadeia recebida, usada como CA, valida o servidor.
    ultimo = cadeia[-1]
    ultimo_der = ultimo if isinstance(ultimo, bytes) else ultimo.public_bytes(ssl.ENCODING_DER)
    teste = ssl.create_default_context(cadata=ssl.DER_cert_to_PEM_cert(ultimo_der))
    try:
        with socket.create_connection((host, porta), timeout=30) as bruto:
            with teste.wrap_socket(bruto, server_hostname=host):
                pass
        print("Teste: confiando no último certificado da cadeia, a verificação PASSA "
              "(nome do host e cadeia válidos).")
    except ssl.SSLError as erro:
        print(f"Teste: mesmo confiando no último certificado, a verificação FALHA: {erro}")


if __name__ == "__main__":
    main()
