"""Django Admin: telas de cadastro prontas, geradas a partir dos models.

Acesse em /admin com um usuário ``is_staff`` (o seed cria admin@prorsctae.local).
"""

from django.contrib import admin

from rsc.models import RscAtividade, RscItemReferencia, RscSaber


@admin.register(RscItemReferencia)
class RscItemReferenciaAdmin(admin.ModelAdmin):
    list_display = ["rir_numero", "rir_requisito", "rir_descricao", "rir_unidade",
                    "rir_pontos_unidade", "rir_ativo"]  # fmt: skip
    list_filter = ["rir_requisito", "rir_ativo"]
    search_fields = ["rir_descricao"]
    ordering = ["rir_numero"]


class RscAtividadeInline(admin.TabularInline):
    model = RscAtividade
    extra = 0
    fields = ["rsa_requisito", "rsa_descricao", "rsa_pontos", "rsa_situacao_avaliacao"]


@admin.register(RscSaber)
class RscSaberAdmin(admin.ModelAdmin):
    list_display = ["rsc_id", "rsc_nome_servidor", "rsc_escolaridade", "rsc_nivel_selecionado",
                    "rsc_status", "updated_at"]  # fmt: skip
    list_filter = ["rsc_status", "rsc_escolaridade"]
    search_fields = ["rsc_nome_servidor", "usuario__email"]
    inlines = [RscAtividadeInline]
