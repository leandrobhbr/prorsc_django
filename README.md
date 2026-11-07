# Calculadora RSC-TAE de livre acesso — implementação em Django

Calculadora de pontuação do **Reconhecimento de Saberes e Competências (RSC)** dos servidores
**Técnico-Administrativos em Educação (TAE)**. O servidor informa a escolaridade, escolhe
atividades do catálogo oficial de saberes (Anexos I a VI) e vê na hora a pontuação e os níveis
RSC atingidos.

A mesma calculadora existe em três backends Python, com a mesma API e o mesmo frontend:

| Implementação | Repositório |
|---|---|
| Flask | [prorsc_flask](https://github.com/leandrobhbr/prorsc_flask) |
| FastAPI | [prorsc_fastapi](https://github.com/leandrobhbr/prorsc_fastapi) |
| **Django** (este) | [prorsc_django](https://github.com/leandrobhbr/prorsc_django) |

Derivada do [ProRSC-TAE](https://github.com/leandrobhbr/pro-rsc-tae), sistema completo oferecido
como Software Público Brasileiro.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+ · Django 5.2 LTS · Django REST Framework · djangorestframework-simplejwt · django-cors-headers |
| Banco | SQLite (modo WAL) |
| Frontend | Vue 3 · Quasar 2 · Pinia · axios |
| Produção | Ubuntu 24.04 · Apache (proxy reverso + estáticos) · Gunicorn · systemd |
| Qualidade | pytest + pytest-django · ruff · uv |

## Rodando localmente

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Node.js 22+.

```bash
# Backend → http://localhost:8003   (Admin em http://localhost:8003/admin/)
cd backend
cp .env.example .env
uv sync
uv run python manage.py migrate      # cria as tabelas (data/prorsc.db)
uv run python manage.py seed         # catálogo de 60 itens + usuários de demonstração
uv run python manage.py runserver 8003

# Frontend → http://localhost:9001   (em outro terminal)
cd frontend
npm install
npm run dev
```

Usuários de demonstração: **teste@teste.com.br** / **123456** (calculadora) e
**admin@prorsctae.local** / **admin123** (Django Admin).

Testes e qualidade:

```bash
cd backend
uv run pytest            # testes unitários do cálculo + integração da API
uv run ruff check .      # lint
uv run ruff format .     # formatação
```

Publicação em servidor: veja **[docs/DEPLOY.md](docs/DEPLOY.md)** (Ubuntu + Apache + Gunicorn).

## Estrutura

```
backend/
  manage.py
  config/              # projeto: settings.py, urls.py (raiz), wsgi.py
  accounts/            # app de contas
    models.py          # Usuario (AbstractBaseUser) na tabela "users"; senha bcrypt
    views.py           # LoginView (gera o JWT), HealthView
    admin.py
  rsc/                 # app da calculadora
    domain/calculo.py  # REGRAS DE NEGÓCIO em Python puro (sem Django, sem banco)
    models.py          # tabelas tb_rsc_* (db_table / db_column)
    serializers.py     # DRF: validação da entrada e formato da saída
    services.py        # casos de uso: consulta, permissão, regra, gravação
    views.py           # APIViews (uma classe por recurso)
    urls.py
    admin.py           # telas do Django Admin para catálogo e cálculos
    management/commands/seed.py   # python manage.py seed
    migrations/
    data/catalogo_rsc.json
  core/
    autenticacao.py    # JWT (simplejwt) com mensagens em português
    excecoes.py        # exceções e EXCEPTION_HANDLER do DRF (401, 403, 404, 422)
    hashid.py
  tests/               # pytest-django + APIClient
  gunicorn.conf.py
frontend/              # Vue 3 + Quasar (idêntico nas três implementações)
deploy/                # Apache, systemd, script de atualização
docs/DEPLOY.md
```

O fluxo de uma requisição:

```
HTTP → middlewares → urls.py → JWTAutenticacao preenche request.user → APIView
     → Serializer valida → services.py → rsc/domain/calculo.py
          └→ Django ORM → SQLite
```

## API

Prefixo `/api/v1`. Todas as rotas, exceto o login, exigem `Authorization: Bearer <token>`.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/login` | autentica com e-mail e senha e devolve o JWT |
| GET | `/rsc/catalogo` | catálogo de itens agrupado por requisito (I a VI) |
| GET | `/rsc` | meus cálculos, com total de pontos e melhor nível |
| POST | `/rsc` | cria um cálculo |
| GET | `/rsc/{id}` | dados, atividades e resultado do cálculo |
| POST | `/rsc/{id}/escolaridade` | altera escolaridade e nome; devolve o resultado |
| POST | `/rsc/{id}/nivel-selecionado` | define o nível pleiteado (validado pela escolaridade) |
| POST | `/rsc/atividade` | adiciona atividade (bloqueia item repetido) |
| PUT | `/rsc/atividade/{id}` | altera atividade |
| DELETE | `/rsc/atividade/{id}` | remove atividade |

Erros: `401` sem token; `403` cálculo de outro usuário; `404` não encontrado; `422` com
`{"errors": {"campo": ["mensagem"]}}` (validação) ou `{"errors": ["mensagem"]}` (regra).
Os IDs na URL são *hashids* (`/rsc/MMhbs5`), não números sequenciais.

## Regras do cálculo

| Nível | Escolaridade exigida | Pontos | Atividades | Exige pontuar em |
|---|---|---|---|---|
| RSC-I | Fund. incompleto | 10 | 1 | — |
| RSC-II | Fund. completo | 15 | 2 | — |
| RSC-III | Médio/Técnico | 25 | 2 | — |
| RSC-IV | Graduação | 30 | 3 | II, IV, V ou VI |
| RSC-V | Especialização | 52 | 5 | IV, V ou VI |
| RSC-VI | Mestrado | 75 | 7 | VI |

Cada atividade soma os pontos do item × quantidade e conta como um critério no seu requisito.
O nível pleiteado é sempre o correspondente à escolaridade; doutores não têm nível RSC.

## Como o Django resolve cada parte

| Tema | No Django (este projeto) |
|---|---|
| Organização | um **projeto** (`config/`) com vários **apps** reutilizáveis (`accounts`, `rsc`) |
| Rotas | `urls.py` com `path()`; o `config/urls.py` inclui os `urls.py` de cada app |
| Views | `APIView` do DRF: um método por verbo HTTP (`get`, `post`, `put`, `delete`) |
| Validação | `Serializer` do DRF: `is_valid(raise_exception=True)` → `validated_data` |
| Saída | `ModelSerializer` com `source=` (renomear) e `SerializerMethodField` (calcular) |
| ORM | Django ORM: `objects.filter()`, `select_related` (JOIN), `prefetch_related` (N+1) |
| Migrations | nativas: `makemigrations` gera, `migrate` aplica |
| Autenticação | `AUTH_USER_MODEL` próprio + simplejwt; `request.user` preenchido pelo DRF |
| Permissões | `IsAuthenticated` global em `REST_FRAMEWORK`; `AllowAny` no login |
| Erros | `EXCEPTION_HANDLER` do DRF converte exceções em JSON |
| Comandos | `management/commands/seed.py` → `python manage.py seed` |
| Admin | **Django Admin** gerado a partir dos models, em `/admin/` |
| Transações | `@transaction.atomic` |
| Testes | pytest-django + `APIClient`; banco de teste criado e destruído automaticamente |
| Servidor de produção | Gunicorn (WSGI) |

## Equivalências entre as três implementações

| Conceito | Flask | FastAPI | Django |
|---|---|---|---|
| Agrupar rotas | `Blueprint` | `APIRouter` | app + `urls.py` |
| Definir rota | `@bp.get("/x")` | `@router.get("/x")` | `path("x", View.as_view())` |
| Validar entrada | marshmallow `Schema` | Pydantic `BaseModel` | DRF `Serializer` |
| ORM | SQLAlchemy | SQLAlchemy (async) | Django ORM |
| Migrations | Alembic (Flask-Migrate) | Alembic | `makemigrations` / `migrate` |
| Usuário logado | `current_user` (jwt-extended) | `Depends(get_current_user)` | `request.user` |
| Dependências | contexto global (`current_app`, `g`) | `Depends()` | middleware + `request` |
| Tratar erros | `@app.errorhandler` | `@app.exception_handler` | `EXCEPTION_HANDLER` do DRF |
| Comando de CLI | `@app.cli.command` | script Python | `management/commands` |
| Admin pronto | — | — | Django Admin |
| Documentação da API | — | OpenAPI automático em `/docs` | — (opcional: drf-spectacular) |
| Servidor | Gunicorn (WSGI) | Gunicorn + Uvicorn (ASGI) | Gunicorn (WSGI) |
| Regra de negócio | `app/domain/calculo.py` | `app/domain/calculo.py` | `rsc/domain/calculo.py` |

## Decisões técnicas

- **Regra de negócio isolada.** `rsc/domain/calculo.py` não importa Django nem banco: recebe
  dados simples e devolve um resultado. O arquivo é idêntico nas três implementações e é
  testado sem subir aplicação.
- **Banco legado com nomes limpos no código.** `db_table` e `db_column` mantêm as tabelas
  `tb_rsc_*` e colunas como `usu_id`, enquanto o Python usa `requerimento` e `usuario`.
- **Usuário próprio sem `last_login`.** `AbstractBaseUser` com `last_login = None` para casar
  com a tabela `users`; a única coluna nova é `is_staff`, para o Django Admin.
- **Senhas bcrypt compatíveis com o PHP.** Os hashers do Django usam o formato
  `algoritmo$...`; `set_password`/`check_password` usam bcrypt diretamente para aceitar os
  hashes `$2y$` do sistema original.
- **N+1 evitado e testado.** `prefetch_related("atividades")` na listagem; um teste usa
  `django_assert_max_num_queries` para garantir que o número de consultas não cresce.
- **422 em vez de 400.** O DRF responde 400 para validação; o handler troca para 422,
  como nas outras implementações.
- **Configuração de produção** (`check --deploy`): cookies seguros, cabeçalho do proxy para
  HTTPS e HSTS configurável por variável de ambiente.
- **`Decimal` nos pontos**, **JWT sem estado**, **hashids com conferência de entidade**,
  **mensagem de login única**, **SQLite com WAL** e **datas em UTC (`USE_TZ`)** — iguais às
  outras versões.

## Licença

Código sob **GNU GPL v2.0 ou posterior** ([LICENSE](LICENSE)), a mesma do ProRSC-TAE, do qual
este projeto deriva.
