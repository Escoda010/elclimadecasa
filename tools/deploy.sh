#!/bin/bash
# deploy.sh — Despliega elclimadecasa.com en Namecheap cPanel
# Uso: ssh usuario@servidor 'bash -s' < tools/deploy.sh
#   o bien subir a ~/deploy.sh en el servidor y ejecutar: bash ~/deploy.sh

set -euo pipefail

REPO="https://github.com/Escoda010/elclimadecasa.git"
REPO_DIR="$HOME/elclimadecasa-repo"
WEB_DIR="$HOME/public_html"

echo "=== Deploy elclimadecasa.com ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"

# 1. Clonar o actualizar el repo
if [ -d "$REPO_DIR/.git" ]; then
    echo "-> Actualizando repo..."
    cd "$REPO_DIR"
    git fetch origin
    git reset --hard origin/master
else
    echo "-> Clonando repo por primera vez..."
    git clone "$REPO" "$REPO_DIR"
    cd "$REPO_DIR"
fi

# 2. Sincronizar archivos al public_html (solo los de la web)
echo "-> Copiando archivos a $WEB_DIR..."

rsync -av --delete \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='.claude/' \
    --exclude='tools/' \
    --exclude='datos/' \
    --exclude='.htaccess.bak' \
    "$REPO_DIR/" "$WEB_DIR/"

# 3. Permisos correctos
echo "-> Ajustando permisos..."
find "$WEB_DIR" -type d -exec chmod 755 {} \;
find "$WEB_DIR" -type f -exec chmod 644 {} \;

echo ""
echo "=== Deploy completado ==="
echo "Archivos desplegados en $WEB_DIR"
