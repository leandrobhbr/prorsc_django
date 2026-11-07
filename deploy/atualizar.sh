#!/usr/bin/env bash
# Publica uma versão (tag git) da Calculadora RSC-TAE (Django) no servidor.
#
# Uso:    sudo /opt/prorsc-django/deploy/atualizar.sh v1.2.0
# Voltar: sudo /opt/prorsc-django/deploy/atualizar.sh <tag-anterior>   (veja docs/DEPLOY.md)
set -euo pipefail

VERSAO="${1:?Informe a tag a publicar. Exemplo: sudo deploy/atualizar.sh v1.2.0}"
APP=prorsc-django
DIR=/opt/$APP
# Pasta pública do frontend: FRONT_DIR no .env (padrão /var/www/<app>).
WEB=$(sed -n 's/^FRONT_DIR=//p' "/etc/$APP.env" | tail -1)
WEB=${WEB:-/var/www/$APP}
DADOS=/var/lib/$APP
ENV_FILE=/etc/$APP.env
HEALTH=http://127.0.0.1:8003/api/v1/health

# Executa um comando como o usuário do serviço, com as variáveis de produção carregadas.
como_app() {
    sudo -u prorsc -H bash -c "set -a; source '$ENV_FILE'; set +a; $*"
}

ANTERIOR=$(sudo -u prorsc git -C "$DIR" describe --tags --always)
echo "==> Versão atual: $ANTERIOR  →  nova: $VERSAO"

echo "==> Baixando código"
sudo -u prorsc git -C "$DIR" fetch --tags --quiet
sudo -u prorsc git -C "$DIR" checkout --quiet "$VERSAO"

echo "==> Dependências Python (versões travadas no uv.lock)"
como_app "cd '$DIR/backend' && uv sync --frozen --no-dev"

echo "==> Backup do banco antes das migrations"
BACKUP="$DADOS/backup-$(date +%Y%m%d-%H%M%S)-antes-de-${VERSAO//\//-}.db"   # "origin/master" → "origin-master"
# Como o usuário do serviço: se o sqlite3 rodasse como root, os arquivos -wal/-shm criados
# por ele ficariam com dono root e a aplicação não conseguiria mais gravar no banco.
if [ -f "$DADOS/prorsc.db" ]; then
    sudo -u prorsc sqlite3 "$DADOS/prorsc.db" ".backup '$BACKUP'"
    echo "    $BACKUP"
else
    echo "    (banco ainda não existe; nada a copiar)"
fi

echo "==> Migrations e arquivos estáticos do Django Admin"
como_app "cd '$DIR/backend' && .venv/bin/python manage.py migrate --noinput && .venv/bin/python manage.py collectstatic --noinput"

echo "==> Build do frontend (FRONT_PUBLIC_PATH e FRONT_API_URL do .env; padrão: raiz do domínio)"
como_app "cd '$DIR/frontend' && npm ci --no-audit --no-fund && PUBLIC_PATH=\"\${FRONT_PUBLIC_PATH:-/}\" API_URL=\"\${FRONT_API_URL:-/api/v1}\" npx quasar build"
install -d -m 755 "$WEB"
rsync -a --delete "$DIR/frontend/dist/spa/" "$WEB/"

echo "==> Reiniciando o serviço"
systemctl restart "$APP"

for _ in $(seq 1 10); do
    if curl -fsS "$HEALTH" > /dev/null; then
        echo "==> OK: $VERSAO publicada."
        exit 0
    fi
    sleep 2
done

echo "!! O serviço não respondeu em $HEALTH. Veja: journalctl -u $APP -n 50"
echo "!! Para voltar: sudo $DIR/deploy/atualizar.sh $ANTERIOR"
echo "!!   (se a migration alterou o banco, restaure antes: systemctl stop $APP && sudo -u prorsc cp '$BACKUP' '$DADOS/prorsc.db' && rm -f '$DADOS'/prorsc.db-wal '$DADOS'/prorsc.db-shm)"
exit 1
