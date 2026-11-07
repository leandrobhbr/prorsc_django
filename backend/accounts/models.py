"""Usuário próprio, ligado à tabela ``users`` do schema original.

O padrão do Django é ``AbstractUser`` (com username, first_name, grupos, permissões...).
Aqui usamos ``AbstractBaseUser``, a versão mínima, para casar com as colunas existentes.
"""

import bcrypt
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra):
        usuario = self.model(email=self.normalize_email(email), name=name, **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, name, password=None, **extra):
        extra.setdefault("is_staff", True)
        return self.create_user(email, name, password, **extra)


class Usuario(AbstractBaseUser):
    name = models.CharField("nome", max_length=255)
    email = models.EmailField("e-mail", max_length=255, unique=True)
    password = models.CharField("senha", max_length=255)
    # Única coluna a mais em relação ao schema original: libera o acesso ao Django Admin.
    is_staff = models.BooleanField("acesso ao admin", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Remove a coluna "last_login" herdada (ela não existe no schema original).
    last_login = None

    objects = UsuarioManager()

    USERNAME_FIELD = "email"  # o login é pelo e-mail
    REQUIRED_FIELDS = ["name"]  # pedidos pelo "createsuperuser"

    class Meta:
        db_table = "users"
        verbose_name = "usuário"

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    # ─── Senha ───────────────────────────────────────────────────────────────
    # Os hashers do Django gravam "algoritmo$..." (ex.: "pbkdf2_sha256$..."). O sistema
    # original grava bcrypt puro ("$2y$10$..."). Para continuar aceitando essas senhas,
    # os dois métodos abaixo usam o bcrypt diretamente.

    def set_password(self, raw_password):
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        self.password = bcrypt.hashpw(raw_password.encode(), salt).decode()
        self._password = raw_password

    def check_password(self, raw_password):
        try:
            return bcrypt.checkpw(raw_password.encode(), self.password.encode())
        except ValueError:
            return False

    # ─── Permissões mínimas para o Django Admin ──────────────────────────────

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff
