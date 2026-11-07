# Calculadora RSC-TAE de livre acesso — derivada do ProRSC-TAE (Software Público Brasileiro).
# Licenciado sob a GNU General Public License v2.0 ou posterior (GPL-2.0-or-later).
"""Regras de negócio do RSC-TAE em Python puro.

Este módulo NÃO importa nada de framework (Flask, FastAPI, Django) nem de banco de dados.
Ele recebe dados simples e devolve dados simples. Por isso o mesmo arquivo é usado, sem
nenhuma alteração, nas três implementações do backend — e é testado de forma isolada.

Conceitos de Python usados aqui:
- ``dataclass(frozen=True)``: classes de dados imutáveis (equivalem a "value objects").
- ``Decimal``: aritmética decimal exata (evita 0.1 + 0.2 = 0.30000000000000004).
- type hints (``str | None``, ``Iterable[...]``) — documentam e permitem checagem estática.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from decimal import Decimal

# ─── Constantes ──────────────────────────────────────────────────────────────

REQUISITOS: tuple[str, ...] = ("I", "II", "III", "IV", "V", "VI")

#: Status em que o requerimento ainda pode ser alterado pelo servidor.
STATUS_EDITAVEIS: tuple[str, ...] = ("rascunho", "pendente")

#: Parecer de avaliação que faz a atividade deixar de contar pontos.
SITUACAO_NAO_FAVORAVEL = "nao_favoravel"

ESCOLARIDADES: dict[str, str] = {
    "fund_incompleto": "Ensino Fundamental Incompleto",
    "fund_completo": "Ensino Fundamental Completo",
    "medio": "Ensino Médio / Técnico",
    "graduacao": "Graduação",
    "especializacao": "Pós-Graduação (Especialização)",
    "mestrado": "Mestrado",
    "doutorado": "Doutorado",
}

_ATENCAO_PADRAO = (
    "O título utilizado como requisito de entrada não serve para pontuar no rol de saberes."
)


@dataclass(frozen=True)
class NivelConfig:
    """Requisitos mínimos de um nível RSC."""

    pontos: int
    criterios: int
    req_obrigatorio: tuple[str, ...]
    label: str
    label_curto: str
    equivalente: str
    atencao: str


# A ordem das chaves importa: do menor (RSC-I) para o maior (RSC-VI).
# Desde o Python 3.7, dicionários preservam a ordem de inserção.
NIVEIS: dict[str, NivelConfig] = {
    "RSC-I": NivelConfig(
        pontos=10,
        criterios=1,
        req_obrigatorio=(),
        label="Ensino Fundamental Incompleto",
        label_curto="Fund. Incompleto",
        equivalente="Ensino Fundamental Completo",
        atencao=_ATENCAO_PADRAO,
    ),
    "RSC-II": NivelConfig(
        pontos=15,
        criterios=2,
        req_obrigatorio=(),
        label="Ensino Fundamental Completo",
        label_curto="Fund. Completo",
        equivalente="Ensino Médio",
        atencao=_ATENCAO_PADRAO,
    ),
    "RSC-III": NivelConfig(
        pontos=25,
        criterios=2,
        req_obrigatorio=(),
        label="Ensino Médio ou Técnico",
        label_curto="Médio/Técnico",
        equivalente="Graduação",
        atencao=_ATENCAO_PADRAO,
    ),
    "RSC-IV": NivelConfig(
        pontos=30,
        criterios=3,
        req_obrigatorio=("II", "IV", "V", "VI"),
        label="Graduação",
        label_curto="Graduação",
        equivalente="Especialização",
        atencao=_ATENCAO_PADRAO,
    ),
    "RSC-V": NivelConfig(
        pontos=52,
        criterios=5,
        req_obrigatorio=("IV", "V", "VI"),
        label="Pós-Graduação Lato Sensu",
        label_curto="Pós-graduação",
        equivalente="Mestrado",
        atencao=(
            "A Pós-Graduação Lato Sensu usada como requisito de entrada não pontua "
            "novamente como saber adicional."
        ),
    ),
    "RSC-VI": NivelConfig(
        pontos=75,
        criterios=7,
        req_obrigatorio=("VI",),
        label="Mestrado",
        label_curto="Mestrado",
        equivalente="Doutorado",
        atencao=(
            "O Mestrado usado como requisito de entrada não pontua novamente como saber "
            "adicional. Se você possuir apenas um título de Mestre, não o marque na tabela "
            "de itens."
        ),
    ),
}

ORDEM_NIVEIS: tuple[str, ...] = tuple(NIVEIS)

#: Nível RSC correspondente a cada escolaridade. Doutorado não tem RSC (None).
NIVEL_MAX_POR_ESCOLARIDADE: dict[str, str | None] = {
    "fund_incompleto": "RSC-I",
    "fund_completo": "RSC-II",
    "medio": "RSC-III",
    "graduacao": "RSC-IV",
    "especializacao": "RSC-V",
    "mestrado": "RSC-VI",
    "doutorado": None,
}


# ─── Estruturas de entrada e saída ───────────────────────────────────────────


@dataclass(frozen=True)
class AtividadeCalculo:
    """O mínimo que o cálculo precisa saber de uma atividade."""

    requisito: str
    pontos: Decimal
    situacao_avaliacao: str | None = None


@dataclass(frozen=True)
class StatusNivel:
    nivel: str
    label: str
    label_curto: str
    equivalente: str
    atencao: str
    pontos_minimos: int
    criterios_minimos: int
    req_obrigatorio: list[str]
    disponivel: bool
    atingido: bool
    req_obrigatorio_ok: bool
    pontos_restantes: Decimal
    criterios_restantes: int


@dataclass(frozen=True)
class ResultadoCalculo:
    total_pontos: Decimal
    total_criterios: int
    pontos_por_requisito: dict[str, Decimal]
    criterios_por_requisito: dict[str, int]
    niveis: dict[str, StatusNivel] = field(default_factory=dict)
    melhor_nivel: str | None = None
    proximo_nivel: str | None = None

    def to_dict(self) -> dict:
        """Converte para tipos aceitos por JSON (Decimal vira int ou float)."""
        return para_json(asdict(self))


def para_json(valor):
    """Percorre a estrutura convertendo Decimal em número JSON."""
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    if isinstance(valor, dict):
        return {k: para_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [para_json(v) for v in valor]
    return valor


# ─── Regras ──────────────────────────────────────────────────────────────────


def nivel_disponivel(nivel: str, escolaridade: str) -> bool:
    """Um nível está disponível se não passa do nível máximo da escolaridade."""
    nivel_max = NIVEL_MAX_POR_ESCOLARIDADE.get(escolaridade)
    if nivel_max is None:
        return False
    return ORDEM_NIVEIS.index(nivel) <= ORDEM_NIVEIS.index(nivel_max)


def calcular(atividades: Iterable[AtividadeCalculo], escolaridade: str) -> ResultadoCalculo:
    """Soma pontos e critérios por requisito e diz quais níveis foram atingidos.

    - Cada atividade conta como 1 critério no seu requisito.
    - Atividades com parecer "não favorável" não somam pontos nem critérios.
    - Um nível é atingido quando: está disponível para a escolaridade, os pontos e
      critérios mínimos foram alcançados e, se houver requisito obrigatório, pelo
      menos um deles tem pontuação.
    """
    pontos = {req: Decimal("0") for req in REQUISITOS}
    criterios = {req: 0 for req in REQUISITOS}

    for ati in atividades:
        if ati.situacao_avaliacao == SITUACAO_NAO_FAVORAVEL:
            continue
        pontos[ati.requisito] += Decimal(ati.pontos)
        criterios[ati.requisito] += 1

    total_pontos = sum(pontos.values(), Decimal("0"))
    total_criterios = sum(criterios.values())

    niveis: dict[str, StatusNivel] = {}
    for nome, cfg in NIVEIS.items():
        disponivel = nivel_disponivel(nome, escolaridade)
        # any() com gerador: True se pelo menos um requisito obrigatório pontuou.
        req_ok = not cfg.req_obrigatorio or any(pontos[r] > 0 for r in cfg.req_obrigatorio)
        atingido = (
            disponivel
            and total_pontos >= cfg.pontos
            and total_criterios >= cfg.criterios
            and req_ok
        )
        niveis[nome] = StatusNivel(
            nivel=nome,
            label=cfg.label,
            label_curto=cfg.label_curto,
            equivalente=cfg.equivalente,
            atencao=cfg.atencao,
            pontos_minimos=cfg.pontos,
            criterios_minimos=cfg.criterios,
            req_obrigatorio=list(cfg.req_obrigatorio),
            disponivel=disponivel,
            atingido=atingido,
            req_obrigatorio_ok=req_ok,
            pontos_restantes=max(Decimal("0"), cfg.pontos - total_pontos),
            criterios_restantes=max(0, cfg.criterios - total_criterios),
        )

    # Melhor nível: o maior atingido (percorre do RSC-VI para o RSC-I).
    melhor = next((n for n in reversed(ORDEM_NIVEIS) if niveis[n].atingido), None)

    # Próximo nível: o primeiro disponível e não atingido acima do melhor.
    inicio = 0 if melhor is None else ORDEM_NIVEIS.index(melhor) + 1
    proximo = next(
        (n for n in ORDEM_NIVEIS[inicio:] if niveis[n].disponivel and not niveis[n].atingido),
        None,
    )

    return ResultadoCalculo(
        total_pontos=total_pontos,
        total_criterios=total_criterios,
        pontos_por_requisito=pontos,
        criterios_por_requisito=criterios,
        niveis=niveis,
        melhor_nivel=melhor,
        proximo_nivel=proximo,
    )


def validar_nivel_selecionado(nivel: str, escolaridade: str) -> str | None:
    """Devolve a mensagem de erro, ou None se o nível pode ser escolhido.

    A regra do RSC-TAE: o servidor só pode pleitear exatamente o nível
    correspondente à sua escolaridade.
    """
    nivel_max = NIVEL_MAX_POR_ESCOLARIDADE.get(escolaridade)
    indisponivel = f"O nível {nivel} não está disponível para a sua escolaridade atual."
    if nivel_max is None:
        return indisponivel

    idx_sel = ORDEM_NIVEIS.index(nivel)
    idx_max = ORDEM_NIVEIS.index(nivel_max)
    if idx_sel > idx_max:
        return indisponivel
    if idx_sel < idx_max:
        return (
            f"O nível {nivel} está abaixo do indicado para a sua escolaridade. "
            f"O nível indicado é {nivel_max}."
        )
    return None


def status_editavel(status: str) -> bool:
    return status in STATUS_EDITAVEIS


_RE_ITEM = re.compile(r"^Item nº (\d+) ")


def numero_item_catalogo(observacoes: str | None) -> int | None:
    """Extrai o número do item do catálogo gravado em ``rsa_observacoes``.

    O frontend grava observações no formato "Item nº 12 · 3.0 pt/Por ano".
    Esse número é usado para impedir que o mesmo item seja adicionado duas vezes.
    """
    if not observacoes:
        return None
    m = _RE_ITEM.match(observacoes)
    return int(m.group(1)) if m else None
