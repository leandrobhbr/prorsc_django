"""Testes de integração dos 10 endpoints (HTTP → serviço → banco de teste SQLite)."""

API = "/api/v1"


def atividade(rsc_hashid=None, **extra):
    dados = {
        "rsa_requisito": "II",
        "rsa_descricao": "Coordenação de projeto institucional (2 Por projeto)",
        "rsa_pontos": 10,
        "rsa_observacoes": "Item nº 11 · 5.0 pt/Por projeto",
    }
    if rsc_hashid:
        dados["rsc_hashid"] = rsc_hashid
    return {**dados, **extra}


# ─── Login ───────────────────────────────────────────────────────────────────


def test_login_ok(client):
    resp = client.post(f"{API}/login", {"email": "teste@teste.com.br", "password": "123456"})
    corpo = resp.json()
    assert resp.status_code == 200
    assert corpo["success"] is True
    assert corpo["token"]
    assert corpo["name"] == "Servidor Demonstração"
    assert corpo["usu_hashid"]


def test_login_senha_errada(client):
    resp = client.post(f"{API}/login", {"email": "teste@teste.com.br", "password": "x"})
    assert resp.status_code == 401
    assert resp.json() == {"success": False, "message": "E-mail ou senha inválidos."}


def test_login_campos_obrigatorios(client):
    resp = client.post(f"{API}/login", {})
    assert resp.status_code == 401
    assert resp.json()["message"] == "E-mail e senha são obrigatórios."


def test_login_aceita_hash_do_laravel(client):
    from accounts.models import Usuario

    # Hash "$2y$" gerado pelo PHP (password_hash) para a senha "tae123".
    hash_php = "$2y$10$lo1zUyQDnpN1K5TQb0krGuPRSfosxyg5/ja.oARO8h2gWukAhHcrm"
    Usuario.objects.create(name="Legado", email="legado@prorsctae.local", password=hash_php)
    resp = client.post(f"{API}/login", {"email": "legado@prorsctae.local", "password": "tae123"})
    assert resp.status_code == 200


def test_rotas_rsc_exigem_token(client):
    resp = client.get(f"{API}/rsc")
    assert resp.status_code == 401
    assert resp.json() == {"message": "Token não informado."}
    resp = client.get(f"{API}/rsc", HTTP_AUTHORIZATION="Bearer lixo")
    assert resp.status_code == 401
    assert resp.json() == {"message": "Token inválido."}


# ─── Catálogo ────────────────────────────────────────────────────────────────


def test_catalogo_agrupado_por_requisito(client, auth):
    corpo = client.get(f"{API}/rsc/catalogo", **auth).json()
    assert list(corpo) == ["I", "II", "III", "IV", "V", "VI"]
    assert sum(len(v) for v in corpo.values()) == 60
    item = corpo["I"][0]
    assert set(item) == {
        "item_numero",
        "item_requisito",
        "item_descricao",
        "item_unidade",
        "item_pontos_unidade",
    }
    assert item["item_numero"] == 1


# ─── Requerimentos ───────────────────────────────────────────────────────────


def test_criar_listar_e_obter(client, auth, rsc_hashid):
    lista = client.get(f"{API}/rsc", **auth).json()
    assert len(lista) == 1
    assert lista[0]["rsc_hashid"] == rsc_hashid
    assert lista[0]["rsc_status"] == "rascunho"
    assert lista[0]["total_pontos"] == 0

    dados = client.get(f"{API}/rsc/{rsc_hashid}", **auth).json()
    assert dados["rsc_escolaridade"] == "graduacao"
    assert dados["rsc_nome_servidor"] == "Servidor Demonstração"
    assert dados["atividades"] == []
    assert dados["calculos"]["niveis"]["RSC-IV"]["pontos_minimos"] == 30


def test_criar_com_escolaridade_invalida(client, auth):
    resp = client.post(f"{API}/rsc", {"rsc_escolaridade": "xpto"}, **auth)
    assert resp.status_code == 422
    assert resp.json()["errors"] == {"rsc_escolaridade": ["Escolaridade inválida."]}


def test_hashid_invalido_404_e_de_outro_usuario_403(client, auth, auth_outro, rsc_hashid):
    assert client.get(f"{API}/rsc/naoexiste", **auth).status_code == 404
    resp = client.get(f"{API}/rsc/{rsc_hashid}", **auth_outro)
    assert resp.status_code == 403
    assert resp.json() == {"message": "Acesso negado."}


def test_atualizar_escolaridade_recalcula(client, auth, rsc_hashid):
    resp = client.post(
        f"{API}/rsc/{rsc_hashid}/escolaridade",
        {"rsc_escolaridade": "doutorado", "rsc_data_ultima_concessao": ""},
        **auth,
    )
    corpo = resp.json()
    assert resp.status_code == 200
    assert corpo["success"] is True
    assert not any(n["disponivel"] for n in corpo["calculos"]["niveis"].values())


def test_escolaridade_obrigatoria(client, auth, rsc_hashid):
    resp = client.post(f"{API}/rsc/{rsc_hashid}/escolaridade", {}, **auth)
    assert resp.status_code == 422
    assert resp.json()["errors"]["rsc_escolaridade"] == ["A escolaridade é obrigatória."]


def test_nivel_selecionado(client, auth, rsc_hashid):
    url = f"{API}/rsc/{rsc_hashid}/nivel-selecionado"
    assert client.post(url, {"rsc_nivel_selecionado": "RSC-IV"}, **auth).status_code == 200

    abaixo = client.post(url, {"rsc_nivel_selecionado": "RSC-II"}, **auth)
    assert abaixo.status_code == 422
    assert "abaixo do indicado" in abaixo.json()["errors"][0]

    assert client.post(url, {"rsc_nivel_selecionado": "RSC-X"}, **auth).status_code == 422


# ─── Atividades ──────────────────────────────────────────────────────────────


def test_ciclo_completo_da_atividade(client, auth, rsc_hashid):
    resp = client.post(f"{API}/rsc/atividade", atividade(rsc_hashid), **auth)
    corpo = resp.json()
    assert resp.status_code == 200
    assert corpo["calculos"]["total_pontos"] == 10
    assert corpo["calculos"]["pontos_por_requisito"]["II"] == 10
    rsa_hashid = corpo["rsa_hashid"]

    resp = client.put(f"{API}/rsc/atividade/{rsa_hashid}", atividade(rsa_pontos=12.5), **auth)
    assert resp.json()["calculos"]["total_pontos"] == 12.5

    dados = client.get(f"{API}/rsc/{rsc_hashid}", **auth).json()
    assert dados["atividades"][0]["rsa_pontos"] == 12.5

    resp = client.delete(f"{API}/rsc/atividade/{rsa_hashid}", **auth)
    assert resp.json()["calculos"]["total_pontos"] == 0


def test_item_duplicado_e_bloqueado(client, auth, rsc_hashid):
    client.post(f"{API}/rsc/atividade", atividade(rsc_hashid), **auth)
    resp = client.post(f"{API}/rsc/atividade", atividade(rsc_hashid), **auth)
    assert resp.status_code == 422
    assert resp.json() == {"errors": ["Este item já foi adicionado neste requisito."]}


def test_validacao_da_atividade(client, auth, rsc_hashid):
    resp = client.post(
        f"{API}/rsc/atividade",
        atividade(rsc_hashid, rsa_requisito="VII", rsa_pontos="abc"),
        **auth,
    )
    erros = resp.json()["errors"]
    assert resp.status_code == 422
    assert erros["rsa_requisito"] == ["Requisito inválido. Use I, II, III, IV, V ou VI."]
    assert erros["rsa_pontos"] == ["A pontuação deve ser um número."]


def test_atividade_de_outro_usuario_404(client, auth, auth_outro, rsc_hashid):
    rsa_hashid = client.post(f"{API}/rsc/atividade", atividade(rsc_hashid), **auth).json()[
        "rsa_hashid"
    ]
    assert client.delete(f"{API}/rsc/atividade/{rsa_hashid}", **auth_outro).status_code == 404
    # O código de uma atividade não vale como código de requerimento.
    assert client.get(f"{API}/rsc/{rsa_hashid}", **auth).status_code == 404


def test_requerimento_nao_editavel(client, auth, rsc_hashid):
    from core.hashid import decodificar
    from rsc.models import RscSaber

    RscSaber.objects.filter(pk=decodificar("rsc", rsc_hashid)).update(rsc_status="enviado")

    resp = client.post(f"{API}/rsc/atividade", atividade(rsc_hashid), **auth)
    assert resp.status_code == 422
    assert resp.json()["errors"][0].startswith("O requerimento não pode ser editado")


def test_listagem_sem_n_mais_1(client, auth, django_assert_max_num_queries):
    """Com 5 cálculos, a listagem continua com o mesmo número de consultas."""
    for _ in range(5):
        h = client.post(f"{API}/rsc", {}, **auth).json()["rsc_hashid"]
        client.post(f"{API}/rsc/atividade", atividade(h), **auth)
    # usuário do token + requerimentos + atividades (prefetch)
    with django_assert_max_num_queries(3):
        assert len(client.get(f"{API}/rsc", **auth).json()) == 5
