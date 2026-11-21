"""Testes da lógica local, sem chamada real ao LLM.

As chamadas HTTP são substituídas por respostas simuladas (unittest.mock), de
modo que os testes rodam sem Ollama, sem internet e sem chave de acesso.

Executar:  python -m pytest
"""

from unittest import mock

import pytest
import requests

import main
from main import ErroTriagem


# --- utilidades ------------------------------------------------------------

CONFIG = {
    "base_url": "http://localhost:11434",
    "modelo": "modelo-teste",
    "chave": None,
    "timeout": 5,
    "temperatura": 0.2,
    "max_tokens": 512,
}


def resposta_falsa(status=200, json_dados=None, json_invalido=False):
    """Cria um objeto parecido com requests.Response."""
    r = mock.Mock()
    r.status_code = status
    if json_invalido:
        r.json.side_effect = ValueError("não é JSON")
    else:
        r.json.return_value = json_dados
    return r


@pytest.fixture
def ambiente_limpo(monkeypatch):
    """Remove as variáveis LLM_* e impede a leitura do .env real."""
    for nome in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY", "LLM_TIMEOUT",
                 "LLM_TEMPERATURE", "LLM_MAX_TOKENS"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setattr(main, "load_dotenv", lambda: None)
    return monkeypatch


# --- 1. entrada ------------------------------------------------------------

@pytest.mark.parametrize("texto", ["", "   ", "\n\n  \t"])
def test_entrada_vazia_e_bloqueada(texto):
    with pytest.raises(ErroTriagem, match="vazio"):
        main.validar_entrada(texto)


def test_entrada_valida_passa():
    assert main.validar_entrada("Favor enviar o relatório.") == "Favor enviar o relatório."


def test_arquivo_inexistente():
    with pytest.raises(ErroTriagem, match="não encontrado"):
        main.ler_entrada(["main.py", "arquivo_que_nao_existe.txt"])


def test_le_email_de_arquivo(tmp_path):
    arquivo = tmp_path / "email.txt"
    arquivo.write_text("Favor enviar o parecer até 14/11.", encoding="utf-8")
    assert "parecer" in main.ler_entrada(["main.py", str(arquivo)])


# --- 2. configuração -------------------------------------------------------

def test_config_ausente_lista_variaveis(ambiente_limpo):
    with pytest.raises(ErroTriagem) as erro:
        main.carregar_config()
    assert "LLM_BASE_URL" in str(erro.value)
    assert "LLM_MODEL" in str(erro.value)


def test_config_url_invalida(ambiente_limpo):
    ambiente_limpo.setenv("LLM_BASE_URL", "localhost:11434")
    ambiente_limpo.setenv("LLM_MODEL", "m")
    with pytest.raises(ErroTriagem, match="LLM_BASE_URL inválida"):
        main.carregar_config()


def test_config_usa_padroes(ambiente_limpo):
    ambiente_limpo.setenv("LLM_BASE_URL", "http://localhost:11434")
    ambiente_limpo.setenv("LLM_MODEL", "m")
    config = main.carregar_config()
    assert config["timeout"] == main.TIMEOUT_PADRAO
    assert config["temperatura"] == main.TEMPERATURA_PADRAO
    assert config["max_tokens"] == main.MAX_TOKENS_PADRAO
    assert config["chave"] is None


def test_config_le_parametros_do_ambiente(ambiente_limpo):
    ambiente_limpo.setenv("LLM_BASE_URL", "http://localhost:11434")
    ambiente_limpo.setenv("LLM_MODEL", "m")
    ambiente_limpo.setenv("LLM_TEMPERATURE", "0")
    ambiente_limpo.setenv("LLM_MAX_TOKENS", "256")
    config = main.carregar_config()
    assert config["temperatura"] == 0.0
    assert config["max_tokens"] == 256


@pytest.mark.parametrize("nome,valor", [
    ("LLM_TEMPERATURE", "5"),
    ("LLM_TEMPERATURE", "-1"),
    ("LLM_TEMPERATURE", "quente"),
    ("LLM_MAX_TOKENS", "0"),
    ("LLM_MAX_TOKENS", "abc"),
    ("LLM_MAX_TOKENS", "1.5"),
    ("LLM_TIMEOUT", "0"),
    ("LLM_TIMEOUT", "rápido"),
])
def test_config_parametro_invalido(ambiente_limpo, nome, valor):
    ambiente_limpo.setenv("LLM_BASE_URL", "http://localhost:11434")
    ambiente_limpo.setenv("LLM_MODEL", "m")
    ambiente_limpo.setenv(nome, valor)
    with pytest.raises(ErroTriagem, match=f"{nome} inválido"):
        main.carregar_config()


# --- 3. preparação da solicitação ------------------------------------------

def test_requisicao_sem_chave():
    url, cabecalhos, corpo = main.montar_requisicao("texto do e-mail", CONFIG)
    assert url == "http://localhost:11434/api/chat"
    assert "Authorization" not in cabecalhos
    assert corpo["model"] == "modelo-teste"
    assert corpo["stream"] is False
    assert corpo["options"] == {"temperature": 0.2, "num_predict": 512}
    assert corpo["messages"][0]["role"] == "system"
    assert corpo["messages"][1] == {"role": "user", "content": "texto do e-mail"}


def test_requisicao_com_chave_e_barra_final():
    config = {**CONFIG, "chave": "segredo", "base_url": "http://servidor:9001/"}
    url, cabecalhos, _ = main.montar_requisicao("x", config)
    assert url == "http://servidor:9001/api/chat"
    assert cabecalhos["Authorization"] == "Bearer segredo"


# --- 4. chamada ao modelo (HTTP simulado) ----------------------------------

def chamar(cabecalhos=None):
    corpo = {"model": "modelo-teste", "messages": [{"role": "user", "content": "x"}]}
    return main.chamar_modelo("http://localhost:11434/api/chat",
                              cabecalhos or {}, corpo, timeout=5)


def test_chamada_sucesso():
    dados = {"message": {"content": "SOLICITACAO: NAO\nPEDIDOS: nenhum"}}
    with mock.patch("main.requests.post", return_value=resposta_falsa(200, dados)):
        assert chamar() == dados


@pytest.mark.parametrize("excecao,trecho", [
    (requests.exceptions.ConnectionError, "Não foi possível conectar"),
    (requests.exceptions.Timeout, "não respondeu em 5 segundos"),
    (requests.exceptions.RequestException, "Falha de comunicação"),
])
def test_chamada_falha_de_comunicacao(excecao, trecho):
    with mock.patch("main.requests.post", side_effect=excecao()):
        with pytest.raises(ErroTriagem, match=trecho):
            chamar()


def test_credencial_ausente():
    with mock.patch("main.requests.post", return_value=resposta_falsa(401)):
        with pytest.raises(ErroTriagem, match="Credencial ausente"):
            chamar(cabecalhos={})


def test_credencial_invalida_nao_expoe_a_chave():
    chave = "chave-super-secreta-123"
    with mock.patch("main.requests.post", return_value=resposta_falsa(401)):
        with pytest.raises(ErroTriagem) as erro:
            chamar(cabecalhos={"Authorization": f"Bearer {chave}"})
    assert "Credencial inválida" in str(erro.value)
    assert chave not in str(erro.value)


@pytest.mark.parametrize("status,trecho", [
    (404, "não encontrou o modelo"),
    (500, "indisponível"),
    (503, "indisponível"),
    (400, "recusou a solicitação"),
])
def test_chamada_status_de_erro(status, trecho):
    with mock.patch("main.requests.post", return_value=resposta_falsa(status)):
        with pytest.raises(ErroTriagem, match=trecho):
            chamar()


def test_chamada_resposta_nao_json():
    with mock.patch("main.requests.post", return_value=resposta_falsa(200, json_invalido=True)):
        with pytest.raises(ErroTriagem, match="formato inesperado"):
            chamar()


# --- 5. tratamento da resposta ---------------------------------------------

def test_extrai_texto():
    assert main.extrair_texto({"message": {"content": "  SOLICITACAO: SIM  "}}) == "SOLICITACAO: SIM"


@pytest.mark.parametrize("dados", [{}, {"done": True}, {"message": None}, []])
def test_resposta_formato_inesperado(dados):
    with pytest.raises(ErroTriagem, match="formato inesperado"):
        main.extrair_texto(dados)


@pytest.mark.parametrize("conteudo", ["", "   ", None])
def test_resposta_vazia(conteudo):
    with pytest.raises(ErroTriagem, match="vazia"):
        main.extrair_texto({"message": {"content": conteudo}})


@pytest.mark.parametrize("texto,esperado", [
    ("SOLICITACAO: SIM\nSOLICITANTE: X", True),
    ("solicitacao: nao\nPEDIDOS: nenhum", True),
    ("Claro! Aqui está a análise...", False),
    ("SOLICITACAO: TALVEZ", False),
])
def test_validacao_do_formato(texto, esperado):
    assert main.resposta_no_formato(texto) is esperado


# --- fluxo completo --------------------------------------------------------

def test_fluxo_completo_simulado(ambiente_limpo, tmp_path, capsys):
    email = tmp_path / "email.txt"
    email.write_text("Favor enviar o relatório até sexta.", encoding="utf-8")
    ambiente_limpo.setenv("LLM_BASE_URL", "http://localhost:11434")
    ambiente_limpo.setenv("LLM_MODEL", "m")
    ambiente_limpo.setattr(main.sys, "argv", ["main.py", str(email)])
    dados = {"message": {"content": "SOLICITACAO: SIM\nSOLICITANTE: não identificado\n"
                                    "PEDIDOS:\n- Enviar relatório | prazo: sexta"}}
    with mock.patch("main.requests.post", return_value=resposta_falsa(200, dados)):
        assert main.main() == 0
    saida = capsys.readouterr().out
    assert "SOLICITACAO: SIM" in saida
    assert "Enviar relatório" in saida


def test_fluxo_completo_com_erro_retorna_1(ambiente_limpo, tmp_path, capsys):
    email = tmp_path / "vazio.txt"
    email.write_text("", encoding="utf-8")
    ambiente_limpo.setattr(main.sys, "argv", ["main.py", str(email)])
    assert main.main() == 1
    assert "[Erro]" in capsys.readouterr().err
