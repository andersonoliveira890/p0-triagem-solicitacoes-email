# Execução no portal Devel (LLM institucional)

## Contexto

- O LLM institucional (`https://llm-internal.softex:9001`, `qwen3.5:9b-q4_K_M`) só
  é acessível de dentro de um container no portal Devel.
- A imagem Docker é gerada pelo **GitHub Actions** (sem Docker local, por limite
  de hardware) e baixada como artefato `.tar`.
- A configuração vai em variáveis de ambiente no portal; nenhum segredo na imagem.
- O mentor (Frederic Ferreira, 17/11) orientou: seguir com o 4B local e, se
  testar o 9B, usar o mesmo e-mail fictício e indicar modelo e ambiente.

## 1ª execução — 23/11/2026 (container `72-andersonoliveira890-0`)

Variáveis: `LLM_BASE_URL=https://llm-internal.softex:9001`,
`LLM_MODEL=qwen3.5:9b-q4_K_M`, `LLM_TIMEOUT=300`, `LLM_TEMPERATURE=0.2`,
`LLM_MAX_TOKENS=512`.

Logs (trecho; os 6 e-mails tiveram o mesmo resultado):

```
2026-11-24T00:02:59Z ##### exemplos/email_01_pedido_explicito.txt
2026-11-24T00:02:59Z [Erro] Não foi possível validar o certificado HTTPS do servidor do LLM. Se o servidor usa uma autoridade certificadora interna, informe o arquivo do certificado na variável REQUESTS_CA_BUNDLE.
...
2026-11-24T00:03:00Z ##### exemplos/email_06_prazo_relativo.txt
2026-11-24T00:03:00Z [Erro] Não foi possível validar o certificado HTTPS do servidor do LLM. ...
```

**Análise**

- O certificado do servidor é emitido por uma autoridade certificadora (CA)
  interna, ausente na imagem `python:3.12-slim`.
- O tratamento de `SSLError` adicionado no mesmo dia funcionou: sem ele, a
  mensagem seria um enganoso "não foi possível conectar".
- **Decisão:** não desligar a verificação (`verify=False`), conforme o manual e a
  orientação do mentor Pedro Andrade no fórum; obter o certificado da CA.

**Ações**

- Ticket **IT-9** no Jira pedindo o `.pem` da CA interna.
- Modo de diagnóstico (`MODO=diagnostico_certificado`) para ler a cadeia de
  certificados apresentada pelo servidor.
- O portal permite 1 container por conta: o container `-0` foi excluído para
  enviar a imagem de diagnóstico.

## 2ª execução — diagnóstico do certificado (23/11/2026, container ID 228)

Variáveis: `MODO=diagnostico_certificado`, `LLM_BASE_URL=https://llm-internal.softex:9001`.

```
O servidor apresentou 1 certificado(s).
--- Certificado 0 (autoassinado: provável CA raiz)
Assunto : organizationName=Acme Co, commonName=Kubernetes Ingress Controller Fake Certificate
Emissor : organizationName=Acme Co, commonName=Kubernetes Ingress Controller Fake Certificate
Válido até: Nov  9 06:51:32 2027 GMT
SHA-256 : FC4A8F631A3D6874F2AE72DA16DF09A272AEDFA8253299BEE923365628F2F891
Teste: mesmo confiando no último certificado, a verificação FALHA:
[SSL: CERTIFICATE_VERIFY_FAILED] Hostname mismatch, certificate is not valid for 'llm-internal.softex'.
```

**Conclusão**

- O servidor **não** usa uma CA interna: apresenta o certificado autoassinado
  padrão do NGINX Ingress Controller do Kubernetes ("Fake Certificate"), emitido
  para `ingress.local`.
- Por isso não existe um `.pem` de CA que resolva: mesmo confiando nesse
  certificado, o nome do host não confere.
- A correção adequada é na infraestrutura (configurar no ingress um certificado
  válido para `llm-internal.softex`). Achado relatado no ticket IT-9.
