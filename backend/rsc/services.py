"""Casos de uso da calculadora RSC.

Orquestra: busca no banco (Django ORM), checa permissão, aplica as regras do domínio
(``rsc.domain.calculo``) e grava. Não conhece ``request`` nem JSON.
"""

from collections import defaultdict

from django.db import transaction

from core.excecoes import AcessoNegado, NaoEncontrado, RegraNegocio
from core.hashid import decodificar
from rsc.domain import calculo
from rsc.models import RscAtividade, RscItemReferencia, RscSaber


def calcular(rsc: RscSaber) -> calculo.ResultadoCalculo:
    # .all() usa o cache do prefetch_related quando ele existe (sem nova consulta).
    atividades = [
        calculo.AtividadeCalculo(a.rsa_requisito, a.rsa_pontos, a.rsa_situacao_avaliacao)
        for a in rsc.atividades.all()
    ]
    return calculo.calcular(atividades, rsc.rsc_escolaridade)


def listar_catalogo() -> dict[str, list[RscItemReferencia]]:
    agrupado: dict[str, list[RscItemReferencia]] = defaultdict(list)
    for item in RscItemReferencia.objects.filter(rir_ativo="S"):  # ordem vem do Meta.ordering
        agrupado[item.rir_requisito].append(item)
    return dict(agrupado)


def listar_requerimentos(usuario):
    # prefetch_related: 1 consulta para os requerimentos + 1 para TODAS as atividades
    # (evita o problema N+1).
    return (
        RscSaber.objects.filter(usuario=usuario)
        .prefetch_related("atividades")
        .order_by("-created_at", "-rsc_id")
    )


def criar_requerimento(usuario, escolaridade: str | None, nome: str | None) -> RscSaber:
    return RscSaber.objects.create(
        usuario=usuario,
        rsc_escolaridade=escolaridade or "graduacao",
        rsc_nome_servidor=nome or usuario.name,
        rsc_status="rascunho",
    )


def obter_requerimento(hashid: str, usuario) -> RscSaber:
    rsc_id = decodificar("rsc", hashid)
    rsc = RscSaber.objects.filter(pk=rsc_id).first() if rsc_id else None
    if rsc is None:
        raise NaoEncontrado("Requerimento não encontrado.", como_lista=False)
    if rsc.usuario_id != usuario.pk:
        raise AcessoNegado("Acesso negado.", como_lista=False)
    return rsc


def garantir_editavel(rsc: RscSaber) -> None:
    if not calculo.status_editavel(rsc.rsc_status):
        raise RegraNegocio(
            f'O requerimento não pode ser editado no status atual ("{rsc.rsc_status}").'
        )


def atualizar_dados_basicos(rsc: RscSaber, dados: dict) -> calculo.ResultadoCalculo:
    garantir_editavel(rsc)
    rsc.rsc_escolaridade = dados["rsc_escolaridade"]
    rsc.rsc_nome_servidor = dados.get("rsc_nome_servidor")
    rsc.rsc_data_ultima_concessao = dados.get("rsc_data_ultima_concessao")
    rsc.save()
    return calcular(rsc)


def salvar_nivel_selecionado(rsc: RscSaber, nivel: str) -> None:
    garantir_editavel(rsc)
    erro = calculo.validar_nivel_selecionado(nivel, rsc.rsc_escolaridade)
    if erro:
        raise RegraNegocio(erro)
    rsc.rsc_nivel_selecionado = nivel
    rsc.save(update_fields=["rsc_nivel_selecionado", "updated_at"])


def obter_atividade(hashid: str, usuario) -> RscAtividade:
    rsa_id = decodificar("atividade", hashid)
    # select_related: traz o requerimento na mesma consulta (JOIN).
    ati = (
        RscAtividade.objects.select_related("requerimento").filter(pk=rsa_id).first()
        if rsa_id
        else None
    )
    if ati is None or ati.requerimento.usuario_id != usuario.pk:
        raise NaoEncontrado("Atividade não encontrada.")
    return ati


@transaction.atomic
def adicionar_atividade(usuario, dados: dict) -> tuple[RscAtividade, calculo.ResultadoCalculo]:
    rsc = obter_requerimento(dados["rsc_hashid"], usuario)
    garantir_editavel(rsc)

    numero = calculo.numero_item_catalogo(dados.get("rsa_observacoes"))
    if (
        numero is not None
        and rsc.atividades.filter(
            rsa_requisito=dados["rsa_requisito"],
            rsa_observacoes__startswith=f"Item nº {numero} ",
        ).exists()
    ):
        raise RegraNegocio("Este item já foi adicionado neste requisito.")

    ati = RscAtividade.objects.create(
        requerimento=rsc,
        rsa_requisito=dados["rsa_requisito"],
        rsa_descricao=dados["rsa_descricao"],
        rsa_pontos=dados["rsa_pontos"],
        rsa_observacoes=dados.get("rsa_observacoes"),
    )
    return ati, calcular(rsc)


def atualizar_atividade(ati: RscAtividade, dados: dict) -> calculo.ResultadoCalculo:
    garantir_editavel(ati.requerimento)
    ati.rsa_requisito = dados["rsa_requisito"]
    ati.rsa_descricao = dados["rsa_descricao"]
    ati.rsa_pontos = dados["rsa_pontos"]
    ati.rsa_observacoes = dados.get("rsa_observacoes")
    ati.save()
    return calcular(ati.requerimento)


def excluir_atividade(ati: RscAtividade) -> calculo.ResultadoCalculo:
    rsc = ati.requerimento
    garantir_editavel(rsc)
    ati.delete()
    return calcular(rsc)
