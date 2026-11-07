# Deploy em Ubuntu Server + Apache — Calculadora RSC-TAE (Django)

Guia para publicar a aplicação em um servidor **Ubuntu 24.04 LTS** com **Apache**, e para
subir versões novas depois.

## Arquitetura

```
navegador ──HTTPS──► Apache :443 ─┬─ /         → /var/www/prorsc-django        (frontend compilado)
                                  ├─ /static/  → backend/staticfiles/           (CSS/JS do Admin)
                                  └─ /api/ e /admin/ → 127.0.0.1:8003           (Gunicorn + Django)
                                                          │
                                                          └─ /var/lib/prorsc-django/prorsc.db (SQLite)
```

- O **Apache** serve os arquivos do frontend e os estáticos do Django Admin, e funciona como
  **proxy reverso** da API e do Admin.
- O **Gunicorn** é o servidor de aplicação Python. Ele roda vários processos (*workers*) do
  Django e é gerenciado pelo **systemd**, que o reinicia se cair e o sobe no boot.
- O **Django Admin** fica em `https://seu-dominio/admin/` (usuário `is_staff`).
- Front e API ficam no **mesmo domínio**, então o navegador não precisa de CORS em produção.

### WSGI × ASGI

| | WSGI | ASGI |
|---|---|---|
| Modelo | síncrono: um request por vez em cada worker | assíncrono: muitos requests por worker (`async`/`await`) |
| Frameworks | Flask, Django | FastAPI, Starlette (o Django também suporta) |
| Servidor | Gunicorn, uWSGI, `mod_wsgi` | Uvicorn, Hypercorn, Gunicorn + `UvicornWorker` |

Esta aplicação usa o Django em modo **WSGI** (`config/wsgi.py`). Também daria para rodá-lo
dentro do Apache com o `mod_wsgi` (`libapache2-mod-wsgi-py3`); aqui usamos Gunicorn + proxy
reverso porque é o mesmo desenho das versões Flask e FastAPI, e porque separa o processo
Python do processo do Apache (reinicia um sem afetar o outro).

O Django só serve arquivos estáticos com `DEBUG=1`. Em produção, o `collectstatic` copia
o CSS/JS do Admin para `backend/staticfiles/`, e o Apache os entrega diretamente.

## 1. Preparar o servidor

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y apache2 git sqlite3 rsync curl python3

# uv (gerenciador de pacotes e ambientes Python)
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh

# Node.js 22 (só para compilar o frontend)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Usuário de serviço, sem login
sudo useradd --system --create-home --home-dir /var/lib/prorsc --shell /usr/sbin/nologin prorsc

# Firewall: SSH e web
sudo ufw allow OpenSSH
sudo ufw allow "Apache Full"
sudo ufw enable
```

## 2. Banco de dados (SQLite)

O SQLite é um arquivo; não há servidor de banco para instalar. Basta uma pasta em que só o
usuário do serviço escreve:

```bash
sudo install -d -o prorsc -g prorsc -m 750 /var/lib/prorsc-django
```

**Backup diário** (cópia consistente mesmo com a aplicação rodando):

```bash
sudo tee /etc/cron.daily/prorsc-django-backup > /dev/null <<'EOF'
#!/bin/sh
sqlite3 /var/lib/prorsc-django/prorsc.db ".backup '/var/lib/prorsc-django/backup-diario.db'"
EOF
sudo chmod +x /etc/cron.daily/prorsc-django-backup
```

> SQLite atende bem a dezenas de usuários simultâneos (leituras em paralelo com o modo WAL,
> uma escrita por vez). Para muitas escritas concorrentes, troque para PostgreSQL: basta mudar
> a `DATABASE_URL` e instalar o driver (`psycopg`).

## 3. Primeira instalação

```bash
# Código (cada versão é uma tag git)
sudo install -d -o prorsc -g prorsc /opt/prorsc-django
sudo -u prorsc git clone https://github.com/leandrobhbr/prorsc_django.git /opt/prorsc-django
sudo -u prorsc git -C /opt/prorsc-django checkout v1.0.0

# Variáveis de produção (segredos fora do git)
sudo cp /opt/prorsc-django/deploy/prorsc-django.env.example /etc/prorsc-django.env
sudo chown root:prorsc /etc/prorsc-django.env && sudo chmod 640 /etc/prorsc-django.env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # rode 3x e cole no arquivo
sudo nano /etc/prorsc-django.env

# Backend: dependências, tabelas e dados iniciais
cd /opt/prorsc-django/backend
sudo -u prorsc -H uv sync --frozen --no-dev
sudo -u prorsc -H bash -c 'set -a; source /etc/prorsc-django.env; set +a; .venv/bin/python manage.py migrate && .venv/bin/python manage.py collectstatic --noinput && .venv/bin/python manage.py seed'

# Frontend: compila com a API no mesmo domínio (em subpasta, veja a seção 5.1)
cd /opt/prorsc-django/frontend
sudo -u prorsc -H bash -c 'npm ci --no-audit --no-fund && API_URL=/api/v1 npx quasar build'
sudo install -d /var/www/prorsc-django
sudo rsync -a --delete dist/spa/ /var/www/prorsc-django/
```

> O `manage.py seed` cria usuários de demonstração (`teste@teste.com.br` / `123456` e o
> administrador `admin@prorsctae.local` / `admin123`). Em um ambiente real, remova-os e crie
> o seu administrador com `manage.py createsuperuser`.

## 4. Serviço (systemd)

```bash
sudo cp /opt/prorsc-django/deploy/systemd/prorsc-django.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now prorsc-django
systemctl status prorsc-django
curl http://127.0.0.1:8003/api/v1/health        # {"status": "ok"}
journalctl -u prorsc-django -f                    # logs em tempo real
```

## 5. Apache

```bash
sudo a2enmod proxy proxy_http headers
sudo cp /opt/prorsc-django/deploy/apache/prorsc-django.conf /etc/apache2/sites-available/
sudo nano /etc/apache2/sites-available/prorsc-django.conf   # ajuste o ServerName
sudo a2ensite prorsc-django
sudo a2dissite 000-default                                  # opcional
sudo apache2ctl configtest                                  # deve dizer "Syntax OK"
sudo systemctl reload apache2

# HTTPS gratuito com Let's Encrypt (o domínio precisa apontar para o servidor)
sudo apt install -y certbot python3-certbot-apache
sudo certbot --apache -d calculadora.exemplo.com.br
```

### 5.1 Alternativa: subpasta de um domínio que já existe

Para publicar em `https://exemplo.com.br/prorsc_django/`, num domínio que já tem outros sistemas
(PHP, por exemplo), não crie um VirtualHost novo. Inclua um trecho dentro do
`<VirtualHost *:443>` que já existe:

1. No `/etc/prorsc-django.env`, **antes do build do frontend** (seção 3):
   ```ini
   FRONT_PUBLIC_PATH=/prorsc_django/
   FRONT_API_URL=/prorsc_django/api/v1
   # Links e login do Django Admin com o prefixo:
   FORCE_SCRIPT_NAME=/prorsc_django
   ALLOWED_HOSTS=exemplo.com.br,www.exemplo.com.br,127.0.0.1
   CSRF_TRUSTED_ORIGINS=https://exemplo.com.br,https://www.exemplo.com.br
   ```
   Para compilar à mão, use `PUBLIC_PATH=/prorsc_django/ API_URL=/prorsc_django/api/v1 npx quasar build`.
2. Copie o trecho do Apache:
   ```bash
   sudo mkdir -p /etc/apache2/prorsc
   sudo cp /opt/prorsc-django/deploy/apache/prorsc-django-subpasta.conf /etc/apache2/prorsc/
   ```
3. Dentro do `<VirtualHost *:443>` do domínio, adicione **uma vez** a linha:
   ```apache
   IncludeOptional /etc/apache2/prorsc/*.conf
   ```
4. `sudo a2enmod proxy proxy_http headers && sudo apache2ctl configtest && sudo systemctl reload apache2`

Resultado:
- Frontend: `https://exemplo.com.br/prorsc_django/`
- API: `https://exemplo.com.br/prorsc_django/api/v1/...`
- Django Admin: `https://exemplo.com.br/prorsc_django/admin/`

O Apache tira o prefixo antes de repassar ao Gunicorn (`/prorsc_django/api/v1/login` chega como
`/api/v1/login`). Por isso o backend não muda; só os pontos acima precisam saber da subpasta.

## 6. Subir uma versão nova

As versões seguem **SemVer** (`MAJOR.MINOR.PATCH`): PATCH para correções, MINOR para
funcionalidades compatíveis, MAJOR para mudanças incompatíveis.

**Na sua máquina**, depois de testar e fazer merge na `master`:

```bash
git tag -a v1.1.0 -m "v1.1.0: descrição curta"
git push origin v1.1.0
```

**No servidor**:

```bash
sudo /opt/prorsc-django/deploy/atualizar.sh v1.1.0
```

O script [`deploy/atualizar.sh`](../deploy/atualizar.sh) faz, em ordem:

1. `git fetch` + `checkout` da tag;
2. `uv sync --frozen` (instala exatamente as versões do `uv.lock`);
3. backup do banco com `sqlite3 .backup`;
4. `manage.py migrate` e `collectstatic` (migrations e arquivos do Django Admin);
5. build do frontend e cópia para `/var/www/prorsc-django`;
6. `systemctl restart` e checagem em `/api/v1/health`.

### Voltar para a versão anterior (rollback)

```bash
sudo /opt/prorsc-django/deploy/atualizar.sh v1.0.0
```

Se a versão nova tinha migration que alterou tabelas, restaure antes o backup que o script
mostrou (`cp backup-...db prorsc.db`) ou desfaça a migration com `manage.py migrate <app> <migration_anterior>`.

## 7. Problemas comuns

| Sintoma | Causa provável | Como verificar |
|---|---|---|
| `502 Bad Gateway` / `503` | serviço parado ou porta diferente no Apache | `systemctl status prorsc-django`, `ss -ltnp \| grep 8003` |
| `500` em toda chamada | variável faltando no `.env`, banco sem migration | `journalctl -u prorsc-django -n 50` |
| `attempt to write a readonly database` | dono da pasta do banco | `ls -l /var/lib/prorsc-django` (dono `prorsc`) |
| Front abre, mas a API falha com erro de CORS | front compilado com a URL errada | refaça o build com `API_URL=/api/v1` |
| Login volta sempre para a tela inicial | `JWT_SECRET` mudou (tokens antigos ficam inválidos) | faça login de novo |
| Front mostra versão antiga | cache do navegador | o `index.html` já sai com `no-cache`; recarregue com Ctrl+F5 |
