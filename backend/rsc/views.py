"""Views da calculadora (class-based views do DRF).

Em uma ``APIView``, cada método HTTP vira um método da classe (``get``, ``post``...).
A autenticação JWT e a permissão ``IsAuthenticated`` vêm das configurações globais em
``settings.REST_FRAMEWORK``; ``request.user`` já chega preenchido.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.hashid import codificar
from rsc import services
from rsc.serializers import (
    AtividadeEntrada,
    CriarRequerimentoEntrada,
    DadosBasicosEntrada,
    ItemCatalogoSaida,
    NivelEntrada,
    NovaAtividadeEntrada,
    RequerimentoDetalheSaida,
    RequerimentoResumoSaida,
)


def _validar(serializer_cls, request) -> dict:
    serializer = serializer_cls(data=request.data)
    serializer.is_valid(raise_exception=True)  # inválido → ValidationError → 422
    return serializer.validated_data


class CatalogoView(APIView):
    def get(self, request):
        catalogo = services.listar_catalogo()
        return Response(
            {req: ItemCatalogoSaida(itens, many=True).data for req, itens in catalogo.items()}
        )


class RequerimentosView(APIView):
    def get(self, request):
        reqs = services.listar_requerimentos(request.user)
        return Response(RequerimentoResumoSaida(reqs, many=True).data)

    def post(self, request):
        dados = _validar(CriarRequerimentoEntrada, request)
        rsc = services.criar_requerimento(
            request.user, dados.get("rsc_escolaridade"), dados.get("rsc_nome_servidor")
        )
        return Response(
            {"success": True, "rsc_hashid": codificar("rsc", rsc.rsc_id)},
            status=status.HTTP_201_CREATED,
        )


class RequerimentoView(APIView):
    def get(self, request, hashid):
        rsc = services.obter_requerimento(hashid, request.user)
        return Response(RequerimentoDetalheSaida(rsc).data)


class DadosBasicosView(APIView):
    def post(self, request, hashid):
        rsc = services.obter_requerimento(hashid, request.user)
        dados = _validar(DadosBasicosEntrada, request)
        calculos = services.atualizar_dados_basicos(rsc, dados)
        return Response({"success": True, "calculos": calculos.to_dict()})


class NivelSelecionadoView(APIView):
    def post(self, request, hashid):
        rsc = services.obter_requerimento(hashid, request.user)
        dados = _validar(NivelEntrada, request)
        services.salvar_nivel_selecionado(rsc, dados["rsc_nivel_selecionado"])
        return Response({"success": True})


class AtividadesView(APIView):
    def post(self, request):
        dados = _validar(NovaAtividadeEntrada, request)
        ati, calculos = services.adicionar_atividade(request.user, dados)
        return Response(
            {
                "success": True,
                "message": "Atividade adicionada com sucesso.",
                "rsa_hashid": codificar("atividade", ati.rsa_id),
                "calculos": calculos.to_dict(),
            }
        )


class AtividadeView(APIView):
    def put(self, request, hashid):
        ati = services.obter_atividade(hashid, request.user)
        dados = _validar(AtividadeEntrada, request)
        calculos = services.atualizar_atividade(ati, dados)
        return Response(
            {
                "success": True,
                "message": "Atividade atualizada com sucesso.",
                "calculos": calculos.to_dict(),
            }
        )

    def delete(self, request, hashid):
        ati = services.obter_atividade(hashid, request.user)
        calculos = services.excluir_atividade(ati)
        return Response(
            {
                "success": True,
                "message": "Atividade removida com sucesso.",
                "calculos": calculos.to_dict(),
            }
        )
