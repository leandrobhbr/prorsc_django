"""Models (tabelas) da calculadora. ``db_table`` e ``db_column`` mantêm os nomes do schema
original do ProRSC-TAE, enquanto o código Python usa nomes claros (``requerimento``, ``usuario``).
"""

from django.conf import settings
from django.db import models


class RscSaber(models.Model):
    """Requerimento (cálculo) RSC-TAE de um servidor."""

    rsc_id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="usu_id",
        related_name="requerimentos",
    )
    rsc_escolaridade = models.CharField(max_length=30)
    rsc_nome_servidor = models.CharField(max_length=200, null=True, blank=True)
    rsc_nivel_selecionado = models.CharField(max_length=10, null=True, blank=True)
    rsc_data_ultima_concessao = models.DateField(null=True, blank=True)
    rsc_status = models.CharField(max_length=20, default="rascunho", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_rsc_saberes"
        verbose_name = "cálculo RSC"
        verbose_name_plural = "cálculos RSC"

    def __str__(self) -> str:
        return f"{self.rsc_nome_servidor or self.usuario} · {self.rsc_escolaridade}"


class RscAtividade(models.Model):
    """Atividade declarada em um requerimento, ligada a um requisito (I a VI)."""

    rsa_id = models.BigAutoField(primary_key=True)
    requerimento = models.ForeignKey(
        RscSaber, on_delete=models.CASCADE, db_column="rsc_id", related_name="atividades"
    )
    rsa_requisito = models.CharField(max_length=5)
    rsa_descricao = models.TextField()
    rsa_pontos = models.DecimalField(max_digits=8, decimal_places=2)
    rsa_observacoes = models.TextField(null=True, blank=True)
    rsa_situacao_avaliacao = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_rsc_atividades"
        # A ordem por requisito funciona em texto: I < II < III < IV < V < VI.
        ordering = ["rsa_requisito", "created_at", "rsa_id"]
        verbose_name = "atividade"

    def __str__(self) -> str:
        return f"[{self.rsa_requisito}] {self.rsa_descricao[:60]}"


class RscItemReferencia(models.Model):
    """Catálogo (rol) de saberes e competências — Anexos I a VI."""

    rir_id = models.BigAutoField(primary_key=True)
    rir_numero = models.PositiveSmallIntegerField("número", unique=True)
    rir_requisito = models.CharField("requisito", max_length=5, db_index=True)
    rir_descricao = models.TextField("descrição")
    rir_unidade = models.CharField("unidade", max_length=100)
    rir_pontos_unidade = models.DecimalField("pontos por unidade", max_digits=8, decimal_places=4)
    rir_ativo = models.CharField("ativo", max_length=1, default="S")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_rsc_itens_referencia"
        ordering = ["rir_requisito", "rir_numero"]
        verbose_name = "item do catálogo"
        verbose_name_plural = "itens do catálogo"

    def __str__(self) -> str:
        return f"{self.rir_numero}. {self.rir_descricao[:80]}"
