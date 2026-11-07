"""Fixtures do pytest-django: banco de teste, dados iniciais, cliente da API e tokens."""

import pytest
from rest_framework.test import APIClient

from rsc.management.commands.seed import semear_catalogo, semear_usuarios


@pytest.fixture(autouse=True)
def dados_iniciais(db, settings):
    """``db`` libera o acesso ao banco de teste (criado e apagado pelo pytest-django)."""
    settings.BCRYPT_ROUNDS = 4  # hashes mais rápidos nos testes
    settings.HASHIDS_SALT = "salt-de-teste"
    semear_catalogo()
    semear_usuarios()


@pytest.fixture
def client():
    return APIClient()


def _token(client, email: str, senha: str) -> dict[str, str]:
    resp = client.post("/api/v1/login", {"email": email, "password": senha})
    assert resp.status_code == 200, resp.json()
    return {"HTTP_AUTHORIZATION": f"Bearer {resp.json()['token']}"}


@pytest.fixture
def auth(client):
    return _token(client, "teste@teste.com.br", "123456")


@pytest.fixture
def auth_outro(client):
    return _token(client, "outro@prorsctae.local", "outro123")


@pytest.fixture
def rsc_hashid(client, auth):
    resp = client.post("/api/v1/rsc", {"rsc_escolaridade": "graduacao"}, **auth)
    assert resp.status_code == 201
    return resp.json()["rsc_hashid"]
