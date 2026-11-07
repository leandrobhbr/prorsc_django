"""Configuração do Gunicorn (servidor WSGI de produção).

O Apache recebe as requisições na porta 80/443 e repassa /api/ e /admin/ para cá.
"""

import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8003")

# Com SQLite, poucos workers bastam: leituras em paralelo (WAL), uma escrita por vez.
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))

timeout = 30
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "127.0.0.1"
