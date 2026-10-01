# -*- coding: utf-8 -*-
"""
publicar.py - Publica elclimadecasa.com en el hosting de Namecheap por FTPS.

Uso normal (desde la carpeta del proyecto):

    python tools/build_site.py && python tools/publicar.py

Opciones:
    --dry-run   Enseña lo que subiría, sin tocar el servidor.
    --todo      Sube todos los archivos, aunque no hayan cambiado.
    --borrar    Borra en el servidor los archivos que ya no existen en local.
    --config X  Usa otro archivo de configuración.

Credenciales: tools/deploy.config.json (no se sube a git). Copia
tools/deploy.config.ejemplo.json y rellénalo. También valen las variables de
entorno ECDC_FTP_HOST, ECDC_FTP_USER, ECDC_FTP_PASS y ECDC_FTP_DIR.

Solo sube los archivos del sitio: quedan fuera .git, .claude, tools y datos.
"""
import argparse
import ftplib
import hashlib
import io
import json
import os
import ssl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_POR_DEFECTO = os.path.join(BASE, "tools", "deploy.config.json")
MANIFIESTO = os.path.join(BASE, "tools", ".publicado.json")

# Carpetas y archivos que nunca se publican
DIRS_EXCLUIDOS = {".git", ".claude", "tools", "datos", "__pycache__", ".idea", ".vscode"}
ARCHIVOS_EXCLUIDOS = {".gitignore", ".DS_Store", "Thumbs.db", "desktop.ini"}
EXT_EXCLUIDAS = {".bak", ".orig", ".pyc", ".swp", ".zip"}

# Nunca se borran en remoto aunque no estén en local
PROTEGIDOS_REMOTOS = {"cgi-bin", ".well-known", "cpanel", ".htpasswd", "php.ini",
                      ".ftpquota", ".hcflag", ".litespeed_flag", ".lscache_vary",
                      "error_log", ".trash"}


# ── Configuración ───────────────────────────────────────────

def cargar_config(ruta):
    cfg = {"host": "", "usuario": "", "password": "", "carpeta_remota": "public_html",
           "tls": True, "puerto": 21}

    if os.path.exists(ruta):
        with io.open(ruta, encoding="utf-8") as f:
            cfg.update(json.load(f))

    cfg["host"] = os.environ.get("ECDC_FTP_HOST", cfg["host"])
    cfg["usuario"] = os.environ.get("ECDC_FTP_USER", cfg["usuario"])
    cfg["password"] = os.environ.get("ECDC_FTP_PASS", cfg["password"])
    cfg["carpeta_remota"] = os.environ.get("ECDC_FTP_DIR", cfg["carpeta_remota"])

    faltan = [k for k in ("host", "usuario", "password") if not cfg[k]]
    if faltan:
        print("Faltan credenciales: " + ", ".join(faltan))
        print("Rellena {} (mira deploy.config.ejemplo.json).".format(ruta))
        sys.exit(1)
    return cfg


# ── Inventario local ────────────────────────────────────────

def sha1(ruta):
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def archivos_locales():
    """Devuelve {ruta_relativa_con_barras: (ruta_absoluta, sha1, tamano)}."""
    salida = {}
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in DIRS_EXCLUIDOS]
        for nombre in files:
            if nombre in ARCHIVOS_EXCLUIDOS:
                continue
            if os.path.splitext(nombre)[1].lower() in EXT_EXCLUIDAS:
                continue
            absoluta = os.path.join(root, nombre)
            rel = os.path.relpath(absoluta, BASE).replace(os.sep, "/")
            salida[rel] = (absoluta, sha1(absoluta), os.path.getsize(absoluta))
    return salida


def cargar_manifiesto():
    if os.path.exists(MANIFIESTO):
        try:
            with io.open(MANIFIESTO, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_manifiesto(datos):
    with io.open(MANIFIESTO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, indent=2, sort_keys=True)
        f.write("\n")


# ── FTP ─────────────────────────────────────────────────────

def conectar(cfg):
    if cfg.get("tls", True):
        ftp = ftplib.FTP_TLS(context=ssl.create_default_context())
        ftp.connect(cfg["host"], int(cfg.get("puerto", 21)), timeout=30)
        ftp.login(cfg["usuario"], cfg["password"])
        ftp.prot_p()
    else:
        ftp = ftplib.FTP()
        ftp.connect(cfg["host"], int(cfg.get("puerto", 21)), timeout=30)
        ftp.login(cfg["usuario"], cfg["password"])
    ftp.set_pasv(True)
    return ftp


def unir(raiz, sub):
    """Une la raiz remota con una subruta sin dejar barras dobles."""
    if not sub:
        return raiz
    return raiz.rstrip("/") + "/" + sub.lstrip("/")


def asegurar_directorio(ftp, ruta_remota, creados):
    """Crea (si hace falta) la ruta remota y deja el cwd en ella."""
    if ruta_remota in creados:
        ftp.cwd(ruta_remota)
        return
    partes = [p for p in ruta_remota.split("/") if p]
    ftp.cwd("/")
    acumulado = ""
    for parte in partes:
        acumulado += "/" + parte
        try:
            ftp.cwd(acumulado)
        except ftplib.error_perm:
            ftp.mkd(acumulado)
            ftp.cwd(acumulado)
            print("   creada carpeta remota {}".format(acumulado))
    creados.add(ruta_remota)


def listar_remoto(ftp, raiz):
    """Lista recursivamente los archivos bajo `raiz` (rutas relativas)."""
    encontrados = []

    def recorrer(actual, prefijo):
        try:
            entradas = list(ftp.mlsd(actual))
        except (ftplib.error_perm, ftplib.error_proto, AttributeError):
            raise RuntimeError("el servidor no soporta MLSD")
        for nombre, hechos in entradas:
            if nombre in (".", ".."):
                continue
            tipo = hechos.get("type")
            rel = (prefijo + "/" + nombre).lstrip("/")
            if tipo == "dir":
                if nombre in PROTEGIDOS_REMOTOS:
                    continue
                recorrer(actual + "/" + nombre, rel)
            elif tipo == "file":
                encontrados.append(rel)

    recorrer(raiz, "")
    return encontrados


# ── Publicación ─────────────────────────────────────────────

# ── IndexNow (Bing, Yandex, Seznam, Naver...) ──────────────────
# Avisa al momento de las URLs nuevas o cambiadas. Google no usa IndexNow:
# para Google estan el sitemap y Search Console. La clave vive como fichero
# <clave>.txt en la raiz del sitio (se sube con el resto).
SITE_URL = "https://elclimadecasa.com"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def clave_indexnow():
    import re
    for nombre in os.listdir(BASE):
        m = re.match(r"^([0-9a-f]{32})\.txt$", nombre)
        if m:
            with io.open(os.path.join(BASE, nombre), encoding="utf-8") as f:
                if f.read().strip() == m.group(1):
                    return m.group(1)
    return None


def ruta_a_url(rel):
    if not rel.endswith(".html"):
        return None
    if rel == "index.html":
        return SITE_URL + "/"
    if rel.endswith("/index.html"):
        return "{}/{}/".format(SITE_URL, rel[:-len("/index.html")])
    return "{}/{}".format(SITE_URL, rel)


def urls_del_sitemap():
    import re
    with io.open(os.path.join(BASE, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>([^<]+)</loc>", f.read())


def avisar_indexnow(urls):
    """POST a IndexNow. Nunca hace fallar la publicacion."""
    import urllib.request
    urls = sorted({u for u in urls if u})
    clave = clave_indexnow()
    if not urls or not clave:
        if not clave:
            print("IndexNow: no hay fichero de clave en la raiz; no se avisa.")
        return
    cuerpo = json.dumps({"host": SITE_URL.split("//")[1], "key": clave,
                         "keyLocation": "{}/{}.txt".format(SITE_URL, clave),
                         "urlList": urls[:10000]}).encode("utf-8")
    req = urllib.request.Request(INDEXNOW_ENDPOINT, data=cuerpo, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("IndexNow: {} URLs enviadas (HTTP {})".format(len(urls), r.status))
    except Exception as e:
        print("IndexNow: no se pudo avisar ({})".format(e))


def main():
    ap = argparse.ArgumentParser(description="Publica el sitio por FTPS")
    ap.add_argument("--dry-run", action="store_true", help="no sube nada, solo informa")
    ap.add_argument("--todo", action="store_true", help="sube todos los archivos")
    ap.add_argument("--borrar", action="store_true", help="borra en remoto lo que ya no existe en local")
    ap.add_argument("--git", action="store_true",
                    help="tras publicar, guarda los cambios en git y los envia a GitHub")
    ap.add_argument("--config", default=CONFIG_POR_DEFECTO)
    ap.add_argument("--indexnow-todo", action="store_true",
                    help="solo avisa a IndexNow de todas las URLs del sitemap y termina")
    args = ap.parse_args()

    if args.indexnow_todo:
        avisar_indexnow(urls_del_sitemap())
        return

    cfg = cargar_config(args.config)
    raiz = "/" + cfg.get("carpeta_remota", "").strip("/")

    locales = archivos_locales()
    manifiesto = {} if args.todo else cargar_manifiesto()

    pendientes = sorted(rel for rel, (_, h, _) in locales.items() if manifiesto.get(rel) != h)
    sobrantes = sorted(set(manifiesto) - set(locales))

    total_bytes = sum(locales[r][2] for r in pendientes)
    print("Sitio: {}".format(BASE))
    print("Destino: {}@{}{}".format(cfg["usuario"], cfg["host"], raiz))
    print("Archivos del sitio: {} | por subir: {} ({:,} bytes)".format(
        len(locales), len(pendientes), total_bytes))

    if not pendientes and not args.borrar:
        print("No hay cambios que publicar.")
        return

    if args.dry_run:
        for rel in pendientes:
            print("   subiría  {}".format(rel))
        if args.borrar:
            # Para saber que sobra hay que preguntarle al servidor (solo lectura)
            ftp = conectar(cfg)
            try:
                remotos = set(listar_remoto(ftp, raiz))
            except RuntimeError as e:
                remotos = set()
                print("No se pudo listar el remoto: {}".format(e))
            finally:
                try:
                    ftp.quit()
                except Exception:
                    ftp.close()
            for rel in sorted(remotos - set(locales)):
                if rel.split("/")[0] in PROTEGIDOS_REMOTOS:
                    continue
                print("   borraría {}".format(rel))
        print("(dry-run: no se ha modificado nada en el servidor)")
        return

    ftp = conectar(cfg)
    print("Conectado ({})".format("FTPS" if cfg.get("tls", True) else "FTP sin cifrar"))

    creados = set()
    subidos = 0
    fallos = []
    try:
        for rel in pendientes:
            absoluta, h, tam = locales[rel]
            carpeta = os.path.dirname(rel)
            destino = unir(raiz, carpeta)
            try:
                asegurar_directorio(ftp, destino, creados)
                with open(absoluta, "rb") as f:
                    ftp.storbinary("STOR " + os.path.basename(rel), f)
                manifiesto[rel] = h
                subidos += 1
                print("   subido  {:<55} {:>9,} B".format(rel, tam))
            except Exception as e:
                fallos.append((rel, str(e)))
                print("   FALLO   {} -> {}".format(rel, e))

        if args.borrar:
            try:
                remotos = set(listar_remoto(ftp, raiz))
            except RuntimeError as e:
                print("No se pudo listar el remoto ({}); no se borra nada.".format(e))
                remotos = set()
            carpetas_tocadas = set()
            for rel in sorted(remotos - set(locales)):
                if rel.split("/")[0] in PROTEGIDOS_REMOTOS:
                    continue
                try:
                    ftp.delete(unir(raiz, rel))
                    manifiesto.pop(rel, None)
                    if "/" in rel:
                        partes = rel.split("/")[:-1]
                        for i in range(len(partes), 0, -1):
                            carpetas_tocadas.add("/".join(partes[:i]))
                    print("   borrado {}".format(rel))
                except Exception as e:
                    print("   no se pudo borrar {} -> {}".format(rel, e))

            carpetas_locales = {os.path.dirname(r) for r in locales if "/" in r}
            for carpeta in sorted(carpetas_tocadas, key=lambda c: c.count("/"), reverse=True):
                if carpeta in carpetas_locales or carpeta.split("/")[0] in PROTEGIDOS_REMOTOS:
                    continue
                try:
                    ftp.rmd(unir(raiz, carpeta))
                    print("   carpeta vacia eliminada {}/".format(carpeta))
                except Exception:
                    pass
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()
        guardar_manifiesto(manifiesto)

    print()
    print("Publicados {} archivos.".format(subidos))
    if fallos:
        print("Con errores: {}".format(len(fallos)))
        for rel, e in fallos:
            print("   {} -> {}".format(rel, e))
        sys.exit(1)
    print("Listo: https://elclimadecasa.com/")

    # Solo las paginas que han cambiado de verdad (el CSS o el db.js no se indexan)
    avisar_indexnow([ruta_a_url(rel) for rel in pendientes
                     if rel not in [f for f, _ in fallos]])

    if args.git:
        guardar_en_git()


def guardar_en_git():
    """Deja constancia en git de lo que se acaba de publicar."""
    import datetime
    import subprocess

    def correr(*orden):
        return subprocess.run(orden, cwd=BASE, capture_output=True, text=True)

    if correr("git", "rev-parse", "--git-dir").returncode != 0:
        print("Aviso: esto no es un repositorio git, me salto el guardado.")
        return

    if not correr("git", "status", "--porcelain").stdout.strip():
        print("Git: no hay cambios que guardar.")
        return

    correr("git", "add", "-A")
    mensaje = "Publicar sitio ({})".format(datetime.date.today().isoformat())
    commit = correr("git", "commit", "-m", mensaje)
    if commit.returncode != 0:
        print("Git: no se pudo hacer commit ->", (commit.stderr or commit.stdout).strip())
        return
    print("Git: commit hecho ({})".format(mensaje))

    push = correr("git", "push")
    if push.returncode == 0:
        print("Git: enviado a GitHub.")
    else:
        print("Git: commit guardado en local, pero el push ha fallado ->",
              (push.stderr or push.stdout).strip())


if __name__ == "__main__":
    main()
