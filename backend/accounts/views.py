import re

from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from core.hashid import codificar

_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _falha(mensagem: str) -> Response:
    return Response({"success": False, "message": mensagem}, status=401)


class LoginView(APIView):
    """POST /api/v1/login — autentica com e-mail e senha e devolve um JWT."""

    authentication_classes = []  # rota pública: não tenta ler token
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        senha = request.data.get("password") or ""

        if not email or not senha:
            return _falha("E-mail e senha são obrigatórios.")
        if not _RE_EMAIL.match(email):
            return _falha("E-mail inválido.")

        # authenticate() percorre os AUTHENTICATION_BACKENDS (aqui, o ModelBackend padrão),
        # que busca pelo USERNAME_FIELD (e-mail) e chama usuario.check_password().
        usuario = authenticate(request, username=email, password=senha)
        if usuario is None:
            return _falha("E-mail ou senha inválidos.")

        return Response(
            {
                "success": True,
                "token": str(AccessToken.for_user(usuario)),
                "name": usuario.name,
                "email": usuario.email,
                "usu_hashid": codificar("usuario", usuario.pk),
            }
        )


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})
