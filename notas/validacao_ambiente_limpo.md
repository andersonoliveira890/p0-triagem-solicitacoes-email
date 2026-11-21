# Validação em ambiente limpo (21/11/2026)

**Como:** o repositório foi clonado do GitHub (branch `desenvolvimento`) em uma
pasta nova, com um ambiente virtual criado do zero, seguindo apenas os comandos
do README, na ordem.

| # | Passo do README | Resultado |
|---|---|---|
| 0 | Clonar o repositório | ⚠️ **O README não tinha este passo**: começava em `python -m venv`. Corrigido (seção "Passos" agora começa com `git clone` e `cd`). |
| 1 | `python -m venv .venv` | ✅ |
| 2 | `.venv\Scripts\Activate.ps1` | ✅ no processo usado na validação (política de execução liberada só para ele). A política do usuário no computador está "Undefined", o que no Windows significa bloqueio de scripts: um terminal comum recusaria a ativação. O README já orienta a liberar com `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| 3 | `pip install -r requirements.txt` | ✅ |
| 4 | `copy .env.example .env` | ✅ (valores padrão já apontam para o Ollama local) |
| 5 | `ollama list` | ✅ modelo `qwen3.5:4b-q4_K_M` listado |
| 6 | `python main.py exemplos/email_03_varios_pedidos.txt` | ✅ SIM, 3 pedidos, solicitante e prazos corretos |
| 7 | `pip install -r requirements-dev.txt` | ✅ |
| 8 | `python -m pytest` | ✅ 45 passed em 1,7 s |
| 9 | `git status` após executar | ✅ vazio: `.env` e `logs/` corretamente ignorados |

## Limitações desta validação

- Foi feita **no mesmo computador** do desenvolvimento, com o Ollama e o modelo
  já instalados; os passos "Instalar o Ollama" e `ollama pull` não foram
  repetidos.
- O bloqueio do `Activate.ps1` foi identificado pela configuração do sistema, não
  reproduzido no terminal da validação.
- Uma validação por outra pessoa, seguindo só o README, cobriria esses pontos.
