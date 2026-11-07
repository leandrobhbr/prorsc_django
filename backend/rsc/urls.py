from django.urls import path

from rsc import views

# A ordem importa: as rotas fixas ("catalogo", "atividade") vêm antes de "<hashid>".
urlpatterns = [
    path("rsc", views.RequerimentosView.as_view()),
    path("rsc/catalogo", views.CatalogoView.as_view()),
    path("rsc/atividade", views.AtividadesView.as_view()),
    path("rsc/atividade/<str:hashid>", views.AtividadeView.as_view()),
    path("rsc/<str:hashid>", views.RequerimentoView.as_view()),
    path("rsc/<str:hashid>/escolaridade", views.DadosBasicosView.as_view()),
    path("rsc/<str:hashid>/nivel-selecionado", views.NivelSelecionadoView.as_view()),
]
