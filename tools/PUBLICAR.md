# Publicar elclimadecasa.com

Sustituye el ciclo de comprimir, subir el zip a cPanel y descomprimir. Ahora son
dos órdenes desde la carpeta del proyecto.

## Quién es quién (no son dos sitios donde subir lo mismo)

- **Esta carpeta** es el original. Aquí se trabaja.
- **cPanel / Namecheap** es donde vive la web: el dominio apunta ahí y lo que haya
  en `public_html` es lo que ve la gente. Es el único destino obligatorio.
- **GitHub** es el historial y la copia de seguridad. Nadie visita la web desde
  GitHub; sirve para poder volver a una versión anterior si algo se rompe.

El método antiguo (`deploy.sh`) sí usaba GitHub como intermediario: el servidor se
conectaba por SSH y se descargaba el repo. Con `publicar.py` ese rodeo desaparece.

## Cada vez que haya cambios

```bash
python tools/build_site.py
python tools/publicar.py
```

Y si además quieres dejar constancia en GitHub en el mismo paso:

```bash
python tools/publicar.py --git
```

`build_site.py` regenera el HTML desde `datos/productos.json` y `datos/guias.json`.
`publicar.py` sube por FTPS solo los archivos que han cambiado desde la última vez.

Opciones útiles:

| Orden | Qué hace |
|---|---|
| `python tools/publicar.py --dry-run` | Enseña qué subiría, sin tocar el servidor |
| `python tools/publicar.py --todo` | Sube los 80 archivos aunque no hayan cambiado |
| `python tools/publicar.py --borrar` | Además borra en el servidor lo que ya no existe en local |
| `python tools/publicar.py --git` | Tras publicar, hace commit y push a GitHub |

Lo que **no** se sube nunca: `tools/`, `datos/`, `.git/`, `.claude/`, `.gitignore`
y los `.bak`. En el servidor no queda ni el código del generador ni los datos en bruto.

## Configuración inicial (una sola vez)

### 1. Crear una cuenta FTP dedicada en cPanel

Entra en el cPanel de Namecheap → **Files → FTP Accounts** y crea una cuenta nueva:

- **Log In:** `claude` (quedará como `claude@elclimadecasa.com`)
- **Directory:** `public_html` — importante, así esta cuenta solo puede tocar la web
- **Quota:** Unlimited
- Contraseña: genera una con el botón *Password Generator* y guárdala

Usar una cuenta dedicada en vez de la principal (`elclksgy`) tiene dos ventajas:
no comparte la contraseña del hosting entero y se puede borrar en un clic si algún
día quieres cortar el acceso.

### 2. Rellenar las credenciales

Copia `tools/deploy.config.ejemplo.json` a `tools/deploy.config.json` y rellénalo:

```json
{
  "host": "ftp.elclimadecasa.com",
  "usuario": "claude@elclimadecasa.com",
  "password": "la-que-generaste",
  "carpeta_remota": "public_html",
  "tls": true,
  "puerto": 21
}
```

El `host` aparece en cPanel → FTP Accounts → *Configure FTP Client* de esa cuenta;
suele ser `ftp.elclimadecasa.com` o el nombre del servidor (`serverXXX.web-hosting.com`).

`tools/deploy.config.json` está en `.gitignore`: **no se sube nunca al repositorio.**
Si prefieres no dejar la contraseña en un archivo, el script también lee las variables
de entorno `ECDC_FTP_HOST`, `ECDC_FTP_USER`, `ECDC_FTP_PASS` y `ECDC_FTP_DIR`.

### 3. Primera publicación

```bash
python tools/publicar.py --dry-run
```

Si la lista tiene sentido, quita `--dry-run`.

## Detalles que conviene saber

- **Cada build cambia el `?v=` de todos los HTML**, así que en cada publicación se
  suben los 26 HTML aunque el texto no haya cambiado. Las imágenes (3,3 MB, el grueso)
  solo se suben la primera vez.
- El registro de lo ya publicado está en `tools/.publicado.json`. Si lo borras, la
  siguiente publicación sube todo otra vez (que tampoco pasa nada: son 3,6 MB).
- Si cambias de hosting, con ajustar `host`, `usuario` y `carpeta_remota` sigue valiendo.
- `tools/deploy.sh` es el método antiguo (SSH + git pull en el servidor). Se queda ahí
  por si algún día activas SSH, pero con `publicar.py` no hace falta.
