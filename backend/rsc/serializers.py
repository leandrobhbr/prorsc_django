"""Serializers do Django REST Framework.

- Entrada: ``Serializer(data=request.data).is_valid(raise_exception=True)`` valida e converte.
- Saída: ``ModelSerializer`` lê os campos do model; ``source=`` renomeia e
  ``SerializerMethodField`` calcula valores.
"""

from rest_framework import serializers

from core.hashid import codificar
from rsc import services
from rsc.domain.calculo import ESCOLARIDADES, NIVEIS, REQUISITOS, para_json
from rsc.models import RscAtividade, RscItemReferencia, RscSaber


def _obrigatorio(msg: str) -> dict[str, str]:
    return {"required": msg, "null": msg, "blank": msg}


# ─── Entrada ─────────────────────────────────────────────────────────────────


class Entrada(serializers.Serializer):
    def to_internal_value(self, data):
        """Texto vazio ou null equivalem a "não informado"."""
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v not in ("", None)}
        return super().to_internal_value(data)


_ESCOLARIDADE_INVALIDA = {"invalid_choice": "Escolaridade inválida."}


class CriarRequerimentoEntrada(Entrada):
    rsc_escolaridade = serializers.ChoiceField(
        choices=list(ESCOLARIDADES), required=False, error_messages=_ESCOLARIDADE_INVALIDA
    )
    rsc_nome_servidor = serializers.CharField(required=False, max_length=200)


class DadosBasicosEntrada(Entrada):
    rsc_escolaridade = serializers.ChoiceField(
        choices=list(ESCOLARIDADES),
        error_messages={**_obrigatorio("A escolaridade é obrigatória."), **_ESCOLARIDADE_INVALIDA},
    )
    rsc_nome_servidor = serializers.CharField(required=False, max_length=200)
    rsc_data_ultima_concessao = serializers.DateField(
        required=False, error_messages={"invalid": "Data inválida."}
    )


class NivelEntrada(Entrada):
    rsc_nivel_selecionado = serializers.ChoiceField(
        choices=list(NIVEIS),
        error_messages={
            **_obrigatorio("O nível é obrigatório."),
            "invalid_choice": "Nível RSC inválido.",
        },
    )


_PONTOS_FORA_DA_FAIXA = "A pontuação deve estar entre 0 e 9999."


class AtividadeEntrada(Entrada):
    rsa_requisito = serializers.ChoiceField(
        choices=list(REQUISITOS),
        error_messages={
            **_obrigatorio("O requisito é obrigatório."),
            "invalid_choice": "Requisito inválido. Use I, II, III, IV, V ou VI.",
        },
    )
    rsa_descricao = serializers.CharField(
        max_length=1000,
        error_messages={
            **_obrigatorio("A descrição é obrigatória."),
            "max_length": "A descrição deve ter no máximo 1000 caracteres.",
        },
    )
    rsa_pontos = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        max_value=9999,
        error_messages={
            **_obrigatorio("A pontuação é obrigatória."),
            "invalid": "A pontuação deve ser um número.",
            "min_value": _PONTOS_FORA_DA_FAIXA,
            "max_value": _PONTOS_FORA_DA_FAIXA,
            "max_digits": _PONTOS_FORA_DA_FAIXA,
            "max_decimal_places": "A pontuação deve ter no máximo 2 casas decimais.",
        },
    )
    rsa_observacoes = serializers.CharField(required=False, max_length=2000)


class NovaAtividadeEntrada(AtividadeEntrada):
    rsc_hashid = serializers.CharField(error_messages=_obrigatorio("O requerimento é obrigatório."))


# ─── Saída ───────────────────────────────────────────────────────────────────

_FORMATO_DATA_HORA = "%d/%m/%Y %H:%M"  # o DRF converte para o fuso TIME_ZONE


class ItemCatalogoSaida(serializers.ModelSerializer):
    item_numero = serializers.IntegerField(source="rir_numero")
    item_requisito = serializers.CharField(source="rir_requisito")
    item_descricao = serializers.CharField(source="rir_descricao")
    item_unidade = serializers.CharField(source="rir_unidade")
    item_pontos_unidade = serializers.SerializerMethodField()

    class Meta:
        model = RscItemReferencia
        fields = [
            "item_numero",
            "item_requisito",
            "item_descricao",
            "item_unidade",
            "item_pontos_unidade",
        ]

    def get_item_pontos_unidade(self, obj):
        return para_json(obj.rir_pontos_unidade)


class AtividadeSaida(serializers.ModelSerializer):
    rsa_hashid = serializers.SerializerMethodField()
    rsa_pontos = serializers.SerializerMethodField()

    class Meta:
        model = RscAtividade
        fields = [
            "rsa_hashid",
            "rsa_requisito",
            "rsa_descricao",
            "rsa_pontos",
            "rsa_observacoes",
            "rsa_situacao_avaliacao",
        ]

    def get_rsa_hashid(self, obj):
        return codificar("atividade", obj.rsa_id)

    def get_rsa_pontos(self, obj):
        return para_json(obj.rsa_pontos)


class _ComCalculos(serializers.ModelSerializer):
    """Calcula uma única vez por requerimento e guarda no contexto do serializer."""

    rsc_hashid = serializers.SerializerMethodField()

    def _calculos(self, obj):
        cache = self.context.setdefault("_calculos", {})
        if obj.pk not in cache:
            cache[obj.pk] = services.calcular(obj)
        return cache[obj.pk]

    def get_rsc_hashid(self, obj):
        return codificar("rsc", obj.rsc_id)


class RequerimentoResumoSaida(_ComCalculos):
    atividades_count = serializers.SerializerMethodField()
    total_pontos = serializers.SerializerMethodField()
    melhor_nivel = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format=_FORMATO_DATA_HORA)
    updated_at = serializers.DateTimeField(format=_FORMATO_DATA_HORA)

    class Meta:
        model = RscSaber
        fields = [
            "rsc_hashid",
            "rsc_status",
            "rsc_escolaridade",
            "rsc_nivel_selecionado",
            "atividades_count",
            "total_pontos",
            "melhor_nivel",
            "created_at",
            "updated_at",
        ]

    def get_atividades_count(self, obj):
        return len(obj.atividades.all())  # usa o prefetch (sem consulta extra)

    def get_total_pontos(self, obj):
        return para_json(self._calculos(obj).total_pontos)

    def get_melhor_nivel(self, obj):
        return self._calculos(obj).melhor_nivel


class RequerimentoDetalheSaida(_ComCalculos):
    atividades = AtividadeSaida(many=True, read_only=True)
    calculos = serializers.SerializerMethodField()

    class Meta:
        model = RscSaber
        fields = [
            "rsc_hashid",
            "rsc_status",
            "rsc_escolaridade",
            "rsc_nome_servidor",
            "rsc_nivel_selecionado",
            "rsc_data_ultima_concessao",
            "atividades",
            "calculos",
        ]

    def get_calculos(self, obj):
        return self._calculos(obj).to_dict()
