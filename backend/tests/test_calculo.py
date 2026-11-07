"""Testes unitários das regras de negócio (sem banco e sem framework)."""

from decimal import Decimal

import pytest

from rsc.domain.calculo import (
    AtividadeCalculo,
    calcular,
    nivel_disponivel,
    numero_item_catalogo,
    validar_nivel_selecionado,
)


def ati(requisito: str, pontos: str, situacao: str | None = None) -> AtividadeCalculo:
    return AtividadeCalculo(requisito, Decimal(pontos), situacao)


def test_sem_atividades_nenhum_nivel_atingido():
    r = calcular([], "graduacao")
    assert r.total_pontos == 0
    assert r.total_criterios == 0
    assert r.melhor_nivel is None
    assert r.proximo_nivel == "RSC-I"


def test_soma_pontos_e_criterios_por_requisito():
    r = calcular([ati("I", "3"), ati("I", "1.5"), ati("VI", "10")], "graduacao")
    assert r.pontos_por_requisito["I"] == Decimal("4.5")
    assert r.criterios_por_requisito["I"] == 2
    assert r.total_pontos == Decimal("14.5")
    assert r.total_criterios == 3


def test_decimal_evita_erro_de_ponto_flutuante():
    r = calcular([ati("I", "0.1"), ati("I", "0.2")], "graduacao")
    assert r.total_pontos == Decimal("0.3")


def test_nao_favoravel_nao_conta():
    r = calcular([ati("I", "50", "nao_favoravel"), ati("I", "5")], "graduacao")
    assert r.total_pontos == 5
    assert r.total_criterios == 1


def test_rsc_iv_exige_requisito_obrigatorio():
    # 30 pontos e 3 critérios, mas só no requisito I (não obrigatório para o RSC-IV)
    sem_obrigatorio = [ati("I", "10"), ati("I", "10"), ati("I", "10")]
    r = calcular(sem_obrigatorio, "graduacao")
    assert r.niveis["RSC-IV"].req_obrigatorio_ok is False
    assert r.niveis["RSC-IV"].atingido is False
    assert r.melhor_nivel == "RSC-III"
    assert r.proximo_nivel == "RSC-IV"

    com_obrigatorio = [ati("I", "10"), ati("I", "10"), ati("II", "10")]
    r = calcular(com_obrigatorio, "graduacao")
    assert r.niveis["RSC-IV"].atingido is True
    assert r.melhor_nivel == "RSC-IV"
    assert r.proximo_nivel is None  # RSC-V não está disponível para graduação


def test_nivel_acima_da_escolaridade_nao_e_atingido():
    muitas = [ati("VI", "20") for _ in range(7)]  # 140 pontos, 7 critérios
    r = calcular(muitas, "medio")
    assert r.niveis["RSC-VI"].disponivel is False
    assert r.niveis["RSC-VI"].atingido is False
    assert r.melhor_nivel == "RSC-III"


def test_doutorado_nao_tem_nivel_disponivel():
    r = calcular([ati("VI", "100")], "doutorado")
    assert not any(n.disponivel for n in r.niveis.values())
    assert r.melhor_nivel is None
    assert r.proximo_nivel is None


def test_restantes_nunca_negativos():
    r = calcular([ati("VI", "100")], "mestrado")
    assert r.niveis["RSC-I"].pontos_restantes == 0
    assert r.niveis["RSC-VI"].criterios_restantes == 6


def test_to_dict_e_serializavel_em_json():
    import json

    d = calcular([ati("I", "1.5"), ati("II", "2")], "graduacao").to_dict()
    json.dumps(d)  # não pode lançar exceção
    assert d["total_pontos"] == 3.5
    assert d["pontos_por_requisito"]["II"] == 2
    assert list(d["niveis"]) == ["RSC-I", "RSC-II", "RSC-III", "RSC-IV", "RSC-V", "RSC-VI"]


@pytest.mark.parametrize(
    ("nivel", "escolaridade", "esperado"),
    [
        ("RSC-IV", "graduacao", True),
        ("RSC-I", "graduacao", True),
        ("RSC-V", "graduacao", False),
        ("RSC-I", "doutorado", False),
    ],
)
def test_nivel_disponivel(nivel, escolaridade, esperado):
    assert nivel_disponivel(nivel, escolaridade) is esperado


def test_validar_nivel_selecionado():
    assert validar_nivel_selecionado("RSC-IV", "graduacao") is None
    assert "não está disponível" in validar_nivel_selecionado("RSC-V", "graduacao")
    assert "abaixo do indicado" in validar_nivel_selecionado("RSC-III", "graduacao")
    assert "não está disponível" in validar_nivel_selecionado("RSC-I", "doutorado")


@pytest.mark.parametrize(
    ("obs", "esperado"),
    [
        ("Item nº 12 · 3.0 pt/Por ano", 12),
        ("Item nº 7 — minha observação", 7),
        ("Observação livre", None),
        (None, None),
    ],
)
def test_numero_item_catalogo(obs, esperado):
    assert numero_item_catalogo(obs) == esperado
