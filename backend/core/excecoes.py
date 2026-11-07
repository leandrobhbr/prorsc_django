"""Exceções da aplicação e tradução de erros em JSON no formato da API.

- 401/403/404: ``{"message": "..."}``
- 422 de validação: ``{"message": "...", "errors": {"campo": ["mensagem"]}}``
  (o DRF responderia 400; aqui usamos 422, como as outras implementações)
- 422 de regra de negócio: ``{"errors": ["mensagem"]}``
"""

from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ErroAplicacao(Exception):
    status_code = 400

    def __init__(self, mensagem: str, *, como_lista: bool = True):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.como_lista = como_lista

    def to_dict(self) -> dict:
        return {"errors": [self.mensagem]} if self.como_lista else {"message": self.mensagem}


class NaoEncontrado(ErroAplicacao):
    status_code = 404


class AcessoNegado(ErroAplicacao):
    status_code = 403


class RegraNegocio(ErroAplicacao):
    status_code = 422


def tratar_excecao(exc, context):
    """Configurado em ``REST_FRAMEWORK["EXCEPTION_HANDLER"]``."""
    if isinstance(exc, ErroAplicacao):
        return Response(exc.to_dict(), status=exc.status_code)

    # O handler padrão do DRF converte Http404, PermissionDenied e APIException em Response.
    resposta = exception_handler(exc, context)
    if resposta is None:
        return None  # erro inesperado: o Django responde 500 e registra no log

    if isinstance(exc, ValidationError):
        return Response(
            {"message": "Os dados informados são inválidos.", "errors": resposta.data},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, NotAuthenticated):
        mensagem = "Token não informado."
    else:
        detalhe = resposta.data.get("detail", "") if isinstance(resposta.data, dict) else ""
        mensagem = str(detalhe) or "Erro na requisição."
    resposta.data = {"message": mensagem}
    return resposta
