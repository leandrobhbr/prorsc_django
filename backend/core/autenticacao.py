"""Autenticação JWT do DRF com mensagens em português.

Estende a classe do djangorestframework-simplejwt só para trocar as mensagens de erro.
Ela é ativada para todas as views em ``REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]``
e, quando o token é válido, preenche ``request.user``.
"""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import ExpiredTokenError, TokenError
from rest_framework_simplejwt.tokens import AccessToken


class JWTAutenticacao(JWTAuthentication):
    def get_validated_token(self, raw_token):
        try:
            return AccessToken(raw_token)
        except ExpiredTokenError:
            raise AuthenticationFailed("Token expirado.") from None
        except TokenError:
            raise AuthenticationFailed("Token inválido.") from None

    def get_user(self, validated_token):
        try:
            return super().get_user(validated_token)
        except AuthenticationFailed:
            raise AuthenticationFailed("Usuário do token não existe mais.") from None
