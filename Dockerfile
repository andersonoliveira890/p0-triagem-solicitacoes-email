# Imagem para executar a triagem no portal Devel (LLM institucional).
# Nenhuma configuração ou segredo vai para a imagem: LLM_BASE_URL, LLM_MODEL etc.
# são informados como variáveis de ambiente no portal.
FROM python:3.12-slim

WORKDIR /app

# Logs aparecem imediatamente no painel "Logs" do portal
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY exemplos/ exemplos/

# Processa os e-mails fictícios um a um e termina; o resultado fica nos Logs.
# Para processar só um e-mail, defina a variável EMAILS no portal, por exemplo:
#   EMAILS=exemplos/email_03_varios_pedidos.txt
CMD ["sh", "-c", "for f in ${EMAILS:-exemplos/*.txt}; do echo \"##### $f\"; python main.py \"$f\"; echo; done"]
