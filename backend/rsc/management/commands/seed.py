"""Comando ``python manage.py seed``: catálogo RSC e usuários de demonstração.

Todo arquivo em ``<app>/management/commands/`` vira um comando do ``manage.py``.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from rsc.models import RscItemReferencia

CATALOGO_JSON = Path(__file__).resolve().parents[2] / "data" / "catalogo_rsc.json"

USUARIOS_DEMO = [
    ("Servidor Demonstração", "teste@teste.com.br", "123456", False),
    ("Outro Servidor", "outro@prorsctae.local", "outro123", False),
    ("Administrador", "admin@prorsctae.local", "admin123", True),
]


def semear_catalogo() -> int:
    itens = json.loads(CATALOGO_JSON.read_text(encoding="utf-8"))
    for dado in itens:
        # update_or_create: atualiza se existir, cria se não (pode rodar várias vezes).
        RscItemReferencia.objects.update_or_create(
            rir_numero=dado["numero"],
            defaults={
                "rir_requisito": dado["requisito"],
                "rir_descricao": dado["descricao"],
                "rir_unidade": dado["unidade"],
                "rir_pontos_unidade": Decimal(str(dado["pontos_unidade"])),
                "rir_ativo": "S",
            },
        )
    return len(itens)


def semear_usuarios() -> list[str]:
    Usuario = get_user_model()
    criados = []
    for nome, email, senha, staff in USUARIOS_DEMO:
        if not Usuario.objects.filter(email=email).exists():
            Usuario.objects.create_user(email=email, name=nome, password=senha, is_staff=staff)
            criados.append(email)
    return criados


class Command(BaseCommand):
    help = "Carrega o catálogo RSC e os usuários de demonstração."

    def handle(self, *args, **options):
        self.stdout.write(f"Catálogo: {semear_catalogo()} itens.")
        for email in semear_usuarios():
            self.stdout.write(self.style.SUCCESS(f"Usuário criado: {email}"))
