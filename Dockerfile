# Imagem para executar a triagem no portal Devel (LLM institucional).
# Nenhuma configuração ou segredo vai para a imagem: LLM_BASE_URL, LLM_MODEL etc.
# são informados como variáveis de ambiente no portal.
FROM python:3.13-slim

WORKDIR /app

# Logs aparecem imediatamente no painel "Logs" do portal
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py diagnostico_certificado.py ./
COPY exemplos/ exemplos/

# Modo padrão: processa os e-mails fictícios um a um e termina; o resultado
# fica nos Logs. Para processar só um e-mail, defina no portal, por exemplo:
#   EMAILS=exemplos/email_03_varios_pedidos.txt
# Modo diagnóstico: MODO=diagnostico_certificado mostra a cadeia de
# certificados do servidor do LLM.
CMD ["sh", "-c", "if [ \"$MODO\" = diagnostico_certificado ]; then python diagnostico_certificado.py; else for f in ${EMAILS:-exemplos/*.txt}; do echo \"##### $f\"; python main.py \"$f\"; echo; done; fi"]
