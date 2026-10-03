"""
build_site.py — Genera las páginas HTML desde datos/productos.json
Ejecutar: python tools/build_site.py
"""
import json, os, re, sys, html as htmlmod
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _version_estaticos():
    """Cache-buster por CONTENIDO de styles.css y main.js, no por hora del build.
    Asi una pagina solo cambia si cambia de verdad: el FTP sube solo eso y
    IndexNow solo avisa de lo que es nuevo."""
    import hashlib
    h = hashlib.sha1()
    for nombre in ("styles.css", "main.js"):
        ruta = os.path.join(BASE, nombre)
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                h.update(f.read())
    return h.hexdigest()[:10]

VER = _version_estaticos()

def esc(s):
    return htmlmod.escape(str(s)) if s is not None else ""

def vacio(v):
    """Dato que no conocemos: no se pinta nunca (ni 'None' ni 'No especificado')."""
    if v is None:
        return True
    if isinstance(v, str) and v.strip().lower() in ("", "none", "null", "n/d", "no especificado", "-", "—"):
        return True
    if isinstance(v, (list, dict)) and not v:
        return True
    return False

def chip(p, key, unit=""):
    v = p.get(key)
    return None if vacio(v) else f"{v}{unit}"

def resenas_txt(p, plantilla="({n})"):
    n = p.get("resenas_cantidad")
    return "" if vacio(n) else plantilla.format(n=n)

# ── Datos estructurados (JSON-LD) ──────────────────────────────

SCORE_KEYS = ("score_eficiencia", "score_silencio", "score_facilidad_uso",
              "score_capacidad", "score_calidad_precio")

def nota_editor(p):
    """Media de las puntuaciones del editor (1-10), o None si no hay."""
    notas = [p[k] for k in SCORE_KEYS if isinstance(p.get(k), (int, float))]
    return round(sum(notas) / len(notas), 1) if notas else None

def abs_url(ruta):
    return ruta if (ruta or "").startswith("http") else "{}/{}".format(SITE_URL, (ruta or "").lstrip("/"))

def jsonld(*objetos):
    """<script type=application/ld+json> por objeto; escapa '</' para no romper el HTML."""
    salida = ""
    for o in objetos:
        if o:
            txt = json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
            salida += '  <script type="application/ld+json">' + txt + '</script>\n'
    return salida

def autor_ld():
    return {"@type": "Person", "name": "Jordi Escoda Sirvent",
            "url": SITE_URL + "/sobre-nosotros.html"}

def editor_ld():
    return {"@type": "Organization", "name": "El Clima de Casa", "url": SITE_URL + "/"}

def migas_ld(migas):
    """migas: [(nombre, ruta_relativa)]; la ruta '' es la portada."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n,
                                 "item": abs_url(r) if r else SITE_URL + "/"}
                                for i, (n, r) in enumerate(migas)]}

def producto_ld(p, url_rel):
    o = {"@context": "https://schema.org", "@type": "Product",
         "name": p["name"], "url": abs_url(url_rel),
         "image": [abs_url(i) for i in (p.get("images") or [])[:3]],
         "description": p.get("description", "")}
    if not vacio(p.get("marca")):
        o["brand"] = {"@type": "Brand", "name": p["marca"]}
    if not vacio(p.get("asin")):
        o["sku"] = p["asin"]
    nota = nota_editor(p)
    if nota is not None:
        review = {"@type": "Review", "author": autor_ld(), "publisher": editor_ld(),
                  "reviewRating": {"@type": "Rating", "ratingValue": nota,
                                   "bestRating": 10, "worstRating": 1}}
        pros = [x for x in (p.get("pros") or []) if not vacio(x)]
        contras = [x for x in (p.get("contras") or []) if not vacio(x)]
        if pros:
            review["positiveNotes"] = {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": t} for i, t in enumerate(pros)]}
        if contras:
            review["negativeNotes"] = {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": t} for i, t in enumerate(contras)]}
        o["review"] = review
    return o

def articulo_ld(titulo, desc, url_rel, imagen="", fecha=None, fecha_mod=None):
    o = {"@context": "https://schema.org", "@type": "Article",
         "headline": titulo[:110], "description": desc,
         "mainEntityOfPage": abs_url(url_rel), "author": autor_ld(), "publisher": editor_ld(),
         "inLanguage": "es-ES"}
    if imagen:
        o["image"] = [abs_url(imagen)]
    if fecha:
        o["datePublished"] = fecha
        o["dateModified"] = fecha_mod or fecha
    return o

def load_products():
    with open(os.path.join(BASE, "datos", "productos.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def format_price(p):
    if p is None: return "—"
    return f"{p:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def bool_html(v):
    if v: return '<span class="spec-bool-yes">Sí</span>'
    return '<span class="spec-bool-no">No</span>'

def product_img(p, idx=0, cls="", depth=0, lazy=True):
    prefix = "../" * depth
    imgs = p.get("images", [])
    if imgs and idx < len(imgs):
        src = imgs[idx] if imgs[idx].startswith("http") else prefix + imgs[idx]
        alt = esc(p["name"])
        c = f' class="{cls}"' if cls else ""
        carga = 'loading="lazy"' if lazy else 'fetchpriority="high"'
        return f'<img src="{src}" alt="{alt}" {carga} width="400" height="400"{c}>'
    return '<div class="img-placeholder">Sin imagen</div>'

def stars_html(rating):
    if vacio(rating):
        return ""
    full = int(rating)
    half = (rating - full) >= 0.25
    s = "★" * full
    if half: s += "½"
    return s

# ── Category configuration ─────────────────────────────────

SLUG_MAP = {
    "dh-001": "pro-breeze-omnidry-20l",
    "dh-002": "pro-breeze-compacto-12l",
    "dh-003": "delonghi-ariadry-dexd216rf",
    "cal-001": "jata-tc73-calefactor-ceramico-1200w",
    "cal-002": "cecotec-ready-warm-10100-smart-ceramic",
    "cal-003": "pro-breeze-mini-ceramico-2000w",
    "cal-004": "delonghi-trrs-0920-radia-s",
    "cal-005": "orbegozo-rre-1310",
    "cal-006": "orbegozo-rf-2000-radiador-aceite",
    "cal-007": "rowenta-vectissimo-ii-co3030",
    "cal-008": "cecotec-ready-warm-6650-crystal-connection",
    "cal-009": "orbegozo-bp-5003",
}

SPEC_FIELDS_DH = [
    ("Rendimiento", [
        ("Capacidad de extracción", "capacidad_litros_dia", " L/día"),
        ("Potencia", "potencia_w", " W"),
        ("Cobertura máxima", "cobertura_m2", " m²"),
        ("Nivel de ruido", "ruido_db", " dB"),
    ]),
    ("Depósito y drenaje", [
        ("Capacidad del depósito", "deposito_litros", " L"),
        ("Desagüe continuo", "desague_continuo", None),
    ]),
    ("Funciones", [
        ("Modos de funcionamiento", "modos_funcionamiento", ""),
        ("Temporizador", "temporizador", None),
        ("Control remoto", "control_remoto", None),
        ("Control por app", "control_app", None),
        ("Filtro lavable", "filtro_lavable", None),
    ]),
    ("Dimensiones", [
        ("Peso", "peso_kg", " kg"),
        ("Dimensiones", "dimensiones_cm", " cm"),
        ("Refrigerante", "refrigerante", ""),
    ]),
]

SPEC_FIELDS_CAL = [
    ("Rendimiento", [
        ("Tipo de calefactor", "tipo_calefactor", ""),
        ("Potencia máxima", "potencia_w", " W"),
        ("Niveles de potencia", "niveles_potencia", ""),
        ("Cobertura estimada", "cobertura_m2", " m²"),
    ]),
    ("Funciones", [
        ("Termostato", "termostato", None),
        ("Temporizador", "temporizador", None),
        ("Oscilación", "oscilacion", None),
        ("Control remoto", "control_remoto", None),
        ("Control por app", "control_app", None),
        ("Protección baño", "proteccion_bano", ""),
        ("Antivuelco", "antivuelco", None),
        ("Anti-heladas", "anti_heladas", None),
    ]),
    ("Dimensiones", [
        ("Peso", "peso_kg", " kg"),
        ("Dimensiones", "dimensiones_cm", " cm"),
    ]),
]

COMPARE_SPECS_DH = [
    {"label": "Capacidad", "key": "capacidad_litros_dia", "unit": " L/día", "best": "max"},
    {"label": "Potencia", "key": "potencia_w", "unit": " W", "best": "min"},
    {"label": "Cobertura", "key": "cobertura_m2", "unit": " m²", "best": "max"},
    {"label": "Ruido", "key": "ruido_db", "unit": " dB", "best": "min"},
    {"label": "Depósito", "key": "deposito_litros", "unit": " L", "best": "max"},
    {"label": "Peso", "key": "peso_kg", "unit": " kg", "best": "min"},
    {"label": "Temporizador", "key": "temporizador", "type": "bool"},
    {"label": "Control app", "key": "control_app", "type": "bool"},
    {"label": "Desagüe continuo", "key": "desague_continuo", "type": "bool"},
]

COMPARE_SPECS_CAL = [
    {"label": "Tipo", "key": "tipo_calefactor", "unit": ""},
    {"label": "Potencia", "key": "potencia_w", "unit": " W", "best": "max"},
    {"label": "Cobertura", "key": "cobertura_m2", "unit": " m²", "best": "max"},
    {"label": "Peso", "key": "peso_kg", "unit": " kg", "best": "min"},
    {"label": "Termostato", "key": "termostato", "type": "bool"},
    {"label": "Temporizador", "key": "temporizador", "type": "bool"},
    {"label": "Oscilación", "key": "oscilacion", "type": "bool"},
    {"label": "Control remoto", "key": "control_remoto", "type": "bool"},
    {"label": "Control app", "key": "control_app", "type": "bool"},
    {"label": "Antivuelco", "key": "antivuelco", "type": "bool"},
]

SPEC_FIELDS_PUR = [
    ("Rendimiento", [
        ("Cobertura máxima", "cobertura_m2", " m²"),
        ("CADR (aire limpio/hora)", "cadr", " m³/h"),
        ("Nivel de ruido", "ruido_db", " dB"),
        ("Potencia", "potencia_w", " W"),
        ("Velocidades", "niveles_velocidad", ""),
    ]),
    ("Filtración", [
        ("Tipo de filtro", "tipo_filtro", ""),
        ("Filtro HEPA", "filtro_hepa", None),
        ("Carbón activo", "carbon_activo", None),
        ("Prefiltro lavable", "prefiltro_lavable", None),
        ("Vida útil del filtro", "vida_filtro_meses", " meses"),
    ]),
    ("Funciones", [
        ("Sensor de calidad del aire", "sensor_calidad", None),
        ("Modo automático", "modo_auto", None),
        ("Modo noche", "modo_noche", None),
        ("Temporizador", "temporizador", None),
        ("Control por app", "control_app", None),
        ("Aviso de cambio de filtro", "indicador_filtro", None),
    ]),
    ("Dimensiones", [
        ("Peso", "peso_kg", " kg"),
        ("Dimensiones", "dimensiones_cm", " cm"),
    ]),
]

COMPARE_SPECS_PUR = [
    {"label": "Cobertura", "key": "cobertura_m2", "unit": " m²", "best": "max"},
    {"label": "CADR", "key": "cadr", "unit": " m³/h", "best": "max"},
    {"label": "Ruido", "key": "ruido_db", "unit": " dB", "best": "min"},
    {"label": "Tipo de filtro", "key": "tipo_filtro", "unit": ""},
    {"label": "Peso", "key": "peso_kg", "unit": " kg", "best": "min"},
    {"label": "Sensor de calidad", "key": "sensor_calidad", "type": "bool"},
    {"label": "Modo noche", "key": "modo_noche", "type": "bool"},
    {"label": "Control app", "key": "control_app", "type": "bool"},
]

SUBCATEGORIES_CAL = [
    ("ceramico", "Cerámicos"),
    ("radiador-aceite", "Radiadores de aceite"),
    ("panel", "Paneles / Convectores"),
    ("halogeno-cuarzo", "Halógenas / Cuarzo"),
]

CATEGORY_CONFIG = {
    "deshumidificadores": {
        "title": "Deshumidificadores",
        "slug": "deshumidificadores",
        "nav_key": "deshumidificadores",
        "spec_fields": SPEC_FIELDS_DH,
        "compare_specs": COMPARE_SPECS_DH,
        "guide_slug": "guia-deshumidificadores",
        "guide_title": "Guía de compra de deshumidificadores",
        "seo_title": "Mejores deshumidificadores {año}: comparativa y opiniones",
        "h1": "Los mejores deshumidificadores de {año}",
        "intro_titulo": "Cómo elegir un deshumidificador",
        "intro": '<p>Lo primero es la capacidad, en litros al día. Para un dormitorio o un baño suelen bastar 10-12 litros; para un salón o un piso con humedad de verdad, 16-20. Ten en cuenta que esa cifra se mide a 30 °C y 80 % de humedad: en un invierno normal sacará bastante menos.</p><p>Después, el ruido. Si va a estar en el dormitorio, busca 40 dB o menos y un modo noche. Y el depósito: con 2-3 litros lo vaciarás a diario; si quieres olvidarte, que admita desagüe continuo con manguera.</p><p>Si en casa hace frío (por debajo de 15 °C), los de compresor rinden mal; ahí funcionan mejor los desecantes. Lo explicamos con más detalle en la <a href="../guia-deshumidificadores.html">guía de compra de deshumidificadores</a>.</p>',
        "meta_desc": "Los mejores deshumidificadores del mercado. Compara modelos por capacidad, precio, ruido y más.",
        "category_desc": "Compara los mejores deshumidificadores del mercado. Filtros por precio, capacidad y nivel de ruido para encontrar el modelo perfecto para tu hogar.",
        "subcategories": [],
        "chips": lambda p: [
            chip(p, "capacidad_litros_dia", " L/día"),
            chip(p, "cobertura_m2", " m²"),
            chip(p, "ruido_db", " dB"),
        ],
    },
    "calefactores": {
        "title": "Calefactores",
        "slug": "calefactores",
        "nav_key": "calefactores",
        "spec_fields": SPEC_FIELDS_CAL,
        "compare_specs": COMPARE_SPECS_CAL,
        "guide_slug": "guia-calefactores",
        "guide_title": "Guía de compra de calefactores",
        "seo_title": "Mejores calefactores {año}: comparativa y opiniones",
        "h1": "Los mejores calefactores de {año}",
        "intro_titulo": "Cómo elegir un calefactor",
        "intro": '<p>Todos los calefactores eléctricos convierten cada kilovatio que consumen en la misma cantidad de calor: no hay ninguno que gaste menos a igualdad de potencia. Lo que cambia la factura es cuánto tiempo está encendido, y ahí ayudan el termostato, el temporizador y una potencia acorde a la habitación.</p><p>Para calentar rápido un baño o un despacho durante un rato, un cerámico de 1.500-2.000 W es lo más práctico. Para mantener una habitación templada muchas horas, un radiador de aceite o un emisor térmico dan un calor más estable y silencioso. En el baño, que esté pensado para ese uso (con protección contra salpicaduras, por ejemplo IP24) y que se apague si vuelca.</p><p>Lo comparamos con números en la <a href="../guia-calefactores.html">guía de compra de calefactores</a> y en <a href="../guias/consumo-real-calefactor-electrico.html">cuánto gasta de verdad un calefactor eléctrico</a>.</p>',
        "meta_desc": "Los mejores calefactores para tu hogar: cerámicos, radiadores de aceite, paneles y estufas de cuarzo. Compara modelos y elige el tuyo.",
        "category_desc": "Compara los mejores calefactores del mercado. Filtros por precio, potencia y tipo para encontrar el calefactor perfecto para tu hogar.",
        "subcategories": SUBCATEGORIES_CAL,
        "chips": lambda p: [
            chip(p, "tipo_calefactor"),
            chip(p, "potencia_w", " W"),
            chip(p, "cobertura_m2", " m²"),
        ],
    },
    "purificadores": {
        "title": "Purificadores",
        "slug": "purificadores",
        "nav_key": "purificadores",
        "spec_fields": SPEC_FIELDS_PUR,
        "compare_specs": COMPARE_SPECS_PUR,
        "guide_slug": "guia-purificadores",
        "guide_title": "Guía de compra de purificadores de aire",
        "seo_title": "Mejores purificadores de aire {año}: comparativa y opiniones",
        "h1": "Los mejores purificadores de aire de {año}",
        "intro_titulo": "Cómo elegir un purificador de aire",
        "intro": '<p>Fíjate primero en el CADR (los metros cúbicos de aire limpio por hora), más que en los metros cuadrados que anuncia la caja. Como referencia, para un dormitorio de 12-15 m² valen 150-200 m³/h; para un salón de 30 m², unos 300 m³/h si lo quieres por alergias.</p><p>El filtro tiene que ser HEPA de verdad (H13 o mejor) para retener polen, ácaros y caspa de mascotas; si te preocupan los olores o el humo, que lleve también carbón activo. Y mira cuánto cuesta el recambio: es el gasto que tendrás cada 6-12 meses.</p><p>Si lo vas a usar de noche, busca un modo silencioso por debajo de 30 dB. Un purificador no quita la humedad: si tu problema es el moho o la condensación, lo que necesitas es un <a href="../deshumidificadores/">deshumidificador</a>. Más detalles en la <a href="../guia-purificadores.html">guía de compra de purificadores</a>.</p>',
        "meta_desc": "Los mejores purificadores de aire para tu hogar. Compara modelos por cobertura, CADR, filtro HEPA y nivel de ruido.",
        "category_desc": "Compara los mejores purificadores de aire del mercado. Filtros por precio, cobertura y nivel de ruido para encontrar el modelo ideal contra alergias, mascotas, humo o polvo.",
        "subcategories": [],
        "chips": lambda p: [
            chip(p, "cobertura_m2", " m²"),
            chip(p, "cadr", " m³/h"),
            chip(p, "ruido_db", " dB"),
        ],
    },
}

def enlace_canonico(html):
    """href="algo/index.html" -> href="algo/" para no enlazar a URLs que redirigen."""
    def repl(m):
        prefijo = m.group(1)
        return 'href="{}"'.format(prefijo if prefijo else "./")
    return re.sub(r'href="((?:[^"]*/)?)index\.html"', repl, html)


def escribir(ruta, contenido):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(enlace_canonico(contenido))


# ── Shared HTML builders ────────────────────────────────────

SITE_URL = "https://elclimadecasa.com"

TAGLINE = "Guías independientes de climatización para tu hogar."

NAV_LINKS = [
    ("index.html", "Inicio", "inicio"),
    ("guias/index.html", "Guías", "guias"),
    ("deshumidificadores/index.html", "Deshumidificadores", "deshumidificadores"),
    ("calefactores/index.html", "Calefactores", "calefactores"),
    ("purificadores/index.html", "Purificadores", "purificadores"),
    ("comparador.html", "Comparador", "comparador"),
    ("sobre-nosotros.html", "Sobre nosotros", "sobre-nosotros"),
]

NL = chr(10)


def nav_html(active="", depth=0):
    prefix = "../" * depth
    items = ""
    mob = ""
    for href, label, key in NAV_LINKS:
        h = prefix + href
        cls = ' class="active"' if key == active else ""
        items += '<li><a href="{}"{}>{}</a></li>'.format(h, cls, label) + NL
        mob += '<a href="{}">{}</a>'.format(h, label) + NL

    return f"""<header>
<nav class="nav" aria-label="Navegación principal">
  <div class="nav-inner">
    <a href="{prefix}index.html" class="nav-logo">El Clima <span>de Casa</span></a>
    <ul class="nav-links">{items}</ul>
    <button class="nav-toggle" aria-label="Abrir menú" aria-expanded="false"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="nav-mobile" aria-hidden="true">{mob}</div>
<div class="site-tagline"><p>{TAGLINE}</p></div>
</header>"""


def footer_html(depth=0):
    prefix = "../" * depth
    return f"""<footer class="footer">
  <div class="container">
    <ul class="footer-nav">
      <li><a href="{prefix}index.html">Inicio</a></li>
      <li><a href="{prefix}guias/index.html">Guías</a></li>
      <li><a href="{prefix}deshumidificadores/index.html">Deshumidificadores</a></li>
      <li><a href="{prefix}calefactores/index.html">Calefactores</a></li>
      <li><a href="{prefix}purificadores/index.html">Purificadores</a></li>
      <li><a href="{prefix}comparador.html">Comparador</a></li>
      <li><a href="{prefix}test-humedad.html">Test de humedad</a></li>
      <li><a href="{prefix}sobre-nosotros.html">Sobre nosotros</a></li>
      <li><a href="{prefix}aviso-afiliados.html">Aviso de afiliación</a></li>
      <li><a href="{prefix}privacidad.html">Privacidad</a></li>
      <li><a href="{prefix}aviso-legal.html">Aviso legal</a></li>
    </ul>
    <p class="affiliate-notice">elclimadecasa.com participa en el Programa de Afiliados de Amazon EU. Cuando compras a través de nuestros enlaces recibimos una pequeña comisión, sin coste adicional para ti. Amazon y el logotipo de Amazon son marcas registradas de Amazon.com, Inc. o sus afiliados.</p>
    <div class="footer-bottom"><p>&copy; 2026 El Clima de Casa</p></div>
  </div>
</footer>"""


FAVICON = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='5' fill='%231b4965'/>"
    "<path d='M16 7v12' stroke='%23ffffff' stroke-width='2' stroke-linecap='round'/>"
    "<circle cx='16' cy='23' r='3' fill='%23ffffff'/></svg>"
)


def head_html(title, desc, depth=0, canonical=None, og_image="", og_type="website", full_title=None, extra_head=""):
    prefix = "../" * depth
    page_title = full_title if full_title else "{} — El Clima de Casa".format(title)
    og = ""
    if canonical is not None:
        og += '  <link rel="canonical" href="{}/{}">'.format(SITE_URL, canonical) + NL
        og += '  <meta property="og:url" content="{}/{}">'.format(SITE_URL, canonical) + NL
    og += '  <meta property="og:type" content="{}">'.format(og_type) + NL
    og += '  <meta property="og:site_name" content="El Clima de Casa">' + NL
    og += '  <meta property="og:title" content="{}">'.format(esc(page_title)) + NL
    og += '  <meta property="og:description" content="{}">'.format(esc(desc)) + NL
    if og_image:
        img = og_image if og_image.startswith("http") else "{}/{}".format(SITE_URL, og_image)
        og += '  <meta property="og:image" content="{}">'.format(img) + NL

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(desc)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="twitter:card" content="summary_large_image">
{og}  <link rel="stylesheet" href="{prefix}styles.css?v={VER}">
  <link rel="icon" href="{FAVICON}">
  <meta name="p:domain_verify" content="447a4061b72017eac6ae92ec67a035cb"/>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-DP24YW5N8Z"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-DP24YW5N8Z');
  </script>
{extra_head}</head>
<body>
<a href="#main" class="skip-link">Ir al contenido</a>"""


def scripts_html(depth=0):
    prefix = "../" * depth
    # db.js va sin version: el .htaccess le pone no-cache, asi que el navegador
    # siempre revalida, y un cambio de precio no obliga a reescribir todas las paginas.
    return f"""<script defer src="{prefix}lib/db.js"></script>
<script defer src="{prefix}main.js?v={VER}"></script>
</body>
</html>"""


# ── Spec table ──────────────────────────────────────────────

def spec_table_html(p):
    cat = p.get("category", "deshumidificadores")
    fields = CATEGORY_CONFIG.get(cat, {}).get("spec_fields", SPEC_FIELDS_DH)
    rows = ""
    for group_name, field_list in fields:
        group_rows = ""
        for label, key, unit in field_list:
            val = p.get(key)
            if vacio(val):
                continue  # dato desconocido: mejor no enseñarlo que poner "None" o un "No" falso
            cell = bool_html(val) if unit is None else f"{esc(val)}{unit}"
            group_rows += f'<tr><th>{esc(label)}</th><td>{cell}</td></tr>\n'
        if group_rows:
            rows += f'<tr class="spec-group-header"><td colspan="2">{esc(group_name)}</td></tr>\n' + group_rows
    extras = {k: v for k, v in (p.get("specs_extra") or {}).items() if not vacio(v)}
    if extras:
        rows += '<tr class="spec-group-header"><td colspan="2">Otros datos</td></tr>\n'
        for k, v in extras.items():
            rows += f'<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>\n'
    return f'<table class="spec-table"><caption>Especificaciones técnicas</caption><tbody>{rows}</tbody></table>'

def pros_cons_html(p):
    pros = p.get("pros", [])
    cons = p.get("contras", [])
    check = '<svg viewBox="0 0 20 20" fill="currentColor" style="width:1em;height:1em;flex:none"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>'
    xmark = '<svg viewBox="0 0 20 20" fill="currentColor" style="width:1em;height:1em;flex:none"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>'
    pros_li = "".join(f"<li>{check} {esc(x)}</li>" for x in pros)
    cons_li = "".join(f"<li>{xmark} {esc(x)}</li>" for x in cons)
    return f'''<div class="pc-grid">
  <div class="pc-col pros">
    <h3>{check} Ventajas</h3>
    <ul>{pros_li}</ul>
  </div>
  <div class="pc-col cons">
    <h3>{xmark} Inconvenientes</h3>
    <ul>{cons_li}</ul>
  </div>
</div>'''

# ── Slug ────────────────────────────────────────────────────

def product_slug(p):
    # El slug viaja dentro de la propia ficha (datos/productos.json). SLUG_MAP
    # se mantiene como respaldo para las fichas antiguas que aun no lo llevan.
    return p.get("slug") or SLUG_MAP.get(p["id"], p["id"])

# ── Product page (ficha) ───────────────────────────────────

def build_ficha(p, all_products, guias=None):
    guias = guias or []
    cat = p.get("category", "deshumidificadores")
    cfg = CATEGORY_CONFIG.get(cat, CATEGORY_CONFIG["deshumidificadores"])
    slug = product_slug(p)
    price = p.get("discountedPrice") or p.get("retailPrice")
    has_offer = p.get("discountedPrice") and p.get("retailPrice") and p["discountedPrice"] < p["retailPrice"]
    price_html_str = format_price(price)
    original = format_price(p["retailPrice"]) if has_offer else ""

    offer_badge = ""
    if has_offer:
        pct = round(100 * (1 - p["discountedPrice"] / p["retailPrice"]))
        offer_badge = f'<span class="badge badge-offer">-{pct}%</span>'

    similar = [x for x in all_products if x["id"] != p["id"] and x["category"] == cat]

    similar_html = ""
    if similar:
        cards = ""
        for s in similar[:3]:
            cards += f'''<article class="product-card" style="flex:none;width:250px">
  <div class="product-card-img">{product_img(s, depth=1)}</div>
  <div class="product-card-body">
    <div class="product-card-brand">{esc(s["marca"])}</div>
    <h3 class="product-card-name"><a href="{product_slug(s)}.html">{esc(s["name"])}</a></h3>
    <div class="product-card-footer">
      <span class="price-current">{format_price(s.get("discountedPrice") or s.get("retailPrice"))}</span>
    </div>
  </div>
</article>'''
        similar_html = f'''<section class="similar-section">
  <h3>Productos similares</h3>
  <div class="similar-scroll">{cards}</div>
</section>'''

    pie_guias = (f'<p class="related-more"><a href="../{cfg["guide_slug"]}.html">'
                 f'Guía de compra de {esc(cfg["title"].lower())}</a></p>')
    guias_html = guias_relacionadas_html(
        guias_para_producto(guias, p, limit=3), depth=1,
        titulo="Guías relacionadas", pie_html=pie_guias)

    url_ficha = f'{cfg["slug"]}/{slug}.html'
    ld_ficha = jsonld(
        producto_ld(p, url_ficha),
        migas_ld([("Inicio", ""), (cfg["title"], f'{cfg["slug"]}/'), (p["name"], url_ficha)]))
    nota = nota_editor(p)
    nota_html = (f'<p class="editor-score">Nota del editor: <strong>{str(nota).replace(".", ",")}/10</strong></p>'
                 if nota is not None else "")

    titulo_ficha = f'{p["name"]}: opiniones y análisis'
    if len(titulo_ficha) + len(" — El Clima de Casa") <= 65:
        titulo_ficha += " — El Clima de Casa"
    content = f'''{head_html(p["name"], p.get("description",""), depth=1, canonical=url_ficha, full_title=titulo_ficha, og_image=(p.get("images") or [""])[0], og_type="product", extra_head=ld_ficha)}
{nav_html(cfg["nav_key"], depth=1)}
<main id="main">
<section class="ficha">
  <div class="container">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <a href="index.html">{esc(cfg["title"])}</a> <span class="breadcrumb-sep">/</span>
      <span>{esc(p["name"])}</span>
    </nav>

    <div class="ficha-top">
      <div class="ficha-gallery">
        {offer_badge}
        {product_img(p, 0, "ficha-main-img", depth=1, lazy=False)}
      </div>
      <div class="ficha-info">
        <div class="ficha-brand">{esc(p["marca"])}</div>
        <h1>{esc(p["name"])}</h1>
        <div>
          <span class="stars">{stars_html(p.get("valoracion_media"))}</span>
          <span class="stars-count">{resenas_txt(p, "({n} valoraciones en Amazon)")}</span>
        </div>
        <div class="ficha-buy-block">
          <div class="price-block">
            <span class="price-current">{price_html_str}</span>
            {"<span class='price-original'>" + original + "</span>" if original else ""}
          </div>
          <span class="price-note">Precio orientativo · Consulta en Amazon · {p.get("precio_fecha","")}</span>
          <a href="{esc(p["affiliate_url"])}" class="btn btn-amazon btn-lg btn-block" target="_blank" rel="nofollow noopener sponsored">Ver en Amazon</a>
        </div>
        <div class="ficha-ideal">
          <strong>Ideal para</strong>
          {esc(p.get("ideal_para",""))}
        </div>
      </div>
    </div>

    <section class="radar-section">
      <h2>Valoración del editor</h2>
      {nota_html}
      <div class="radar-wrap">
        <div data-ficha-radar="{p["id"]}"></div>
        <p class="radar-note">Puntuaciones del equipo editorial (0-10). No representan una medida oficial.</p>
      </div>
    </section>

    <section class="spec-table-wrap">
      {spec_table_html(p)}
    </section>

    <section class="editorial-section">
      <h2>Nuestro análisis</h2>
      <div class="editorial-body">{p.get("cuerpo_editorial","")}</div>
    </section>

    {pros_cons_html(p)}

    <a href="{esc(p["affiliate_url"])}" class="btn btn-amazon btn-lg btn-block" target="_blank" rel="nofollow noopener sponsored" style="margin-bottom:2rem">Ver en Amazon</a>

    <section class="reviews-section">
      <h3>Lo que dicen los compradores</h3>
      <p>{esc(p.get("resenas_resumen",""))}</p>
    </section>

    {similar_html}

    {guias_html}

    <div style="text-align:center;margin:2rem 0">
      <a href="../comparador.html#{p["id"]}" class="btn btn-outline">Añadir al comparador</a>
    </div>

  </div>
</section>
</main>
{footer_html(depth=1)}
{scripts_html(depth=1)}'''

    outdir = os.path.join(BASE, cfg["slug"])
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{slug}.html")
    escribir(outpath, content)
    print(f"  - Ficha: {cfg['slug']}/{slug}.html")

# ── Category index page ────────────────────────────────────

def precio_de(p):
    return p.get("discountedPrice") or p.get("retailPrice")


def seleccion_rapida(cat_products):
    """Picks calculados con los datos, solo entre productos con nota >= 7."""
    import math
    buenos = [p for p in cat_products if (nota_editor(p) or 0) >= 7 and precio_de(p)]
    if len(buenos) < 3:
        return []

    def popularidad(p):
        return (p.get("valoracion_media") or 0) * math.log10(10 + (p.get("resenas_cantidad") or 0))

    criterios = [
        ("Mejor en general", lambda p: (nota_editor(p), popularidad(p))),
        ("Mejor calidad-precio", lambda p: (p.get("score_calidad_precio") or 0, nota_editor(p), -precio_de(p))),
        ("El más económico", lambda p: (-precio_de(p), nota_editor(p))),
        ("El más silencioso", lambda p: (-(p.get("ruido_db") or 999), nota_editor(p))),
        ("Para estancias grandes", lambda p: (p.get("cobertura_m2") or 0, nota_editor(p))),
    ]
    usados, picks = set(), []
    for etiqueta, clave in criterios:
        if etiqueta == "El más silencioso" and sum(1 for p in buenos if not vacio(p.get("ruido_db"))) < 3:
            continue
        for p in sorted(buenos, key=clave, reverse=True):
            if p["id"] not in usados:
                usados.add(p["id"])
                picks.append((etiqueta, p))
                break
    return picks


def build_category(products, cat_key, guias=None):
    guias = guias or []
    cfg = CATEGORY_CONFIG[cat_key]
    cat_products = [p for p in products if p["category"] == cat_key]

    cards = ""
    for p in cat_products:
        slug = product_slug(p)
        price = p.get("discountedPrice") or p.get("retailPrice")
        has_offer = p.get("discountedPrice") and p.get("retailPrice") and p["discountedPrice"] < p["retailPrice"]
        badge = ""
        if has_offer:
            pct = round(100 * (1 - p["discountedPrice"] / p["retailPrice"]))
            badge = f'<span class="badge badge-offer">-{pct}%</span>'

        chips = [c for c in cfg["chips"](p) if c]
        chips_html = "".join(f'<span class="product-card-chip">{esc(c)}</span>' for c in chips)

        cards += f'''<article class="product-card" data-product-id="{p["id"]}">
  <div class="product-card-img">
    {badge}
    {product_img(p, depth=1)}
  </div>
  <div class="product-card-body">
    <div class="product-card-brand">{esc(p["marca"])}</div>
    <h3 class="product-card-name"><a href="{slug}.html">{esc(p["name"])}</a></h3>
    <div class="product-card-highlight">
      {chips_html}
    </div>
    <p class="product-card-desc">{esc(p.get("description",""))}</p>
    <div class="product-card-footer">
      <div class="price-block">
        <span class="price-current">{format_price(price)}</span>
        {"<span class='price-original'>" + format_price(p["retailPrice"]) + "</span>" if has_offer else ""}
      </div>
      <span class="stars">{stars_html(p.get("valoracion_media"))} <span class="stars-count">{resenas_txt(p)}</span></span>
    </div>
    <div class="price-note">Precio orientativo · Consulta en Amazon · {p.get("precio_fecha","")}</div>
  </div>
</article>\n'''

    # Filters
    if cat_key == "deshumidificadores":
        filters_html = f'''<div class="filters-bar">
      <div class="filter-group">
        <label for="filter-sort">Ordenar:</label>
        <select id="filter-sort" class="filter-select">
          <option value="relevancia">Relevancia</option>
          <option value="precio-asc">Precio: menor a mayor</option>
          <option value="precio-desc">Precio: mayor a menor</option>
          <option value="capacidad">Mayor capacidad</option>
          <option value="silencio">Más silencioso</option>
          <option value="valoracion">Mejor valorado</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-price">Precio máx:</label>
        <select id="filter-price" class="filter-select">
          <option value="0">Todos</option>
          <option value="200">Hasta 200 €</option>
          <option value="250">Hasta 250 €</option>
          <option value="300">Hasta 300 €</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-capacity">Capacidad mín:</label>
        <select id="filter-capacity" class="filter-select">
          <option value="0">Todas</option>
          <option value="16">16+ L/día</option>
          <option value="20">20+ L/día</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-noise">Ruido máx:</label>
        <select id="filter-noise" class="filter-select">
          <option value="0">Todos</option>
          <option value="40">Hasta 40 dB</option>
          <option value="45">Hasta 45 dB</option>
        </select>
      </div>
      <span class="results-count">{len(cat_products)} productos</span>
    </div>'''
    elif cat_key == "purificadores":
        filters_html = f'''<div class="filters-bar">
      <div class="filter-group">
        <label for="filter-sort">Ordenar:</label>
        <select id="filter-sort" class="filter-select">
          <option value="relevancia">Relevancia</option>
          <option value="precio-asc">Precio: menor a mayor</option>
          <option value="precio-desc">Precio: mayor a menor</option>
          <option value="cobertura">Mayor cobertura</option>
          <option value="cadr">Mayor CADR</option>
          <option value="silencio">Más silencioso</option>
          <option value="valoracion">Mejor valorado</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-price">Precio máx:</label>
        <select id="filter-price" class="filter-select">
          <option value="0">Todos</option>
          <option value="100">Hasta 100 €</option>
          <option value="200">Hasta 200 €</option>
          <option value="300">Hasta 300 €</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-coverage">Cobertura mín:</label>
        <select id="filter-coverage" class="filter-select">
          <option value="0">Todas</option>
          <option value="20">20+ m²</option>
          <option value="40">40+ m²</option>
          <option value="60">60+ m²</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-noise">Ruido máx:</label>
        <select id="filter-noise" class="filter-select">
          <option value="0">Todos</option>
          <option value="40">Hasta 40 dB</option>
          <option value="50">Hasta 50 dB</option>
        </select>
      </div>
      <span class="results-count">{len(cat_products)} productos</span>
    </div>'''
    else:
        subcat_options = '<option value="">Todos</option>\n'
        for sc_key, sc_label in cfg.get("subcategories", []):
            subcat_options += f'          <option value="{sc_key}">{esc(sc_label)}</option>\n'
        filters_html = f'''<div class="filters-bar">
      <div class="filter-group">
        <label for="filter-sort">Ordenar:</label>
        <select id="filter-sort" class="filter-select">
          <option value="relevancia">Relevancia</option>
          <option value="precio-asc">Precio: menor a mayor</option>
          <option value="precio-desc">Precio: mayor a menor</option>
          <option value="potencia">Mayor potencia</option>
          <option value="valoracion">Mejor valorado</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-price">Precio máx:</label>
        <select id="filter-price" class="filter-select">
          <option value="0">Todos</option>
          <option value="50">Hasta 50 €</option>
          <option value="80">Hasta 80 €</option>
          <option value="100">Hasta 100 €</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-potencia">Potencia mín:</label>
        <select id="filter-potencia" class="filter-select">
          <option value="0">Todas</option>
          <option value="1500">1500+ W</option>
          <option value="2000">2000+ W</option>
          <option value="2400">2400+ W</option>
        </select>
      </div>
      <div class="filter-group">
        <label for="filter-tipo">Tipo:</label>
        <select id="filter-tipo" class="filter-select">
          {subcat_options}
        </select>
      </div>
      <span class="results-count">{len(cat_products)} productos</span>
    </div>'''

    cat_guias = guias_de_categoria(guias, cat_key)
    guias_cat_html = ""
    if cat_guias:
        guias_cat_html = '''<section class="home-section">
  <div class="container">
    <h2>Guías de {t}</h2>
    <ul class="guide-list">
{items}    </ul>
  </div>
</section>'''.format(t=esc(cfg["title"].lower()),
                     items=guide_list_items(cat_guias, depth=1))

    ld_lista = {"@context": "https://schema.org", "@type": "ItemList",
                "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                     "url": abs_url(f'{cfg["slug"]}/{product_slug(p)}.html'),
                                     "name": p["name"]} for i, p in enumerate(cat_products)]}
    ld_cat = jsonld(migas_ld([("Inicio", ""), (cfg["title"], f'{cfg["slug"]}/')]),
                    ld_lista if cat_products else None)
    picks = seleccion_rapida(cat_products)
    picks_html = ""
    if picks:
        items = ""
        for etiqueta, pk in picks:
            nota = nota_editor(pk)
            motivo = pk.get("destacado_editorial") or ""
            items += ('<li><strong>{e}:</strong> <a href="{h}.html">{nm}</a> · {pr} · nota {no}/10'
                      '{m}</li>\n').format(e=esc(etiqueta), h=product_slug(pk), nm=esc(pk["name"]),
                                           pr=format_price(precio_de(pk)),
                                           no=str(nota).replace(".", ","),
                                           m=(". " + esc(motivo)) if motivo else "")
        picks_html = ('<section class="quick-picks"><div class="container">'
                      '<h2>Selección rápida</h2><ul>' + items + '</ul>'
                      '<p class="price-note">Precios orientativos de Amazon; pueden cambiar.</p>'
                      '</div></section>')
    intro_html = ""
    if cfg.get("intro"):
        intro_html = ('<section class="home-section category-intro"><div class="container container-narrow">'
                      '<h2>' + esc(cfg.get("intro_titulo", "Cómo elegir")) + '</h2>' + cfg["intro"] +
                      '</div></section>')
    año = datetime.now().year
    content = f'''{head_html(cfg["title"], cfg["meta_desc"], depth=1, canonical=f'{cfg["slug"]}/', extra_head=ld_cat, full_title=cfg["seo_title"].format(año=año))}
{nav_html(cfg["nav_key"], depth=1)}
<main id="main">
<section class="page-header">
  <div class="container">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>{esc(cfg["title"])}</span>
    </nav>
    <h1>{esc(cfg["h1"].format(año=año))}</h1>
    <p style="color:var(--text-muted);max-width:600px">{esc(cfg["category_desc"])}</p>
  </div>
</section>
{picks_html}

<section style="padding:0 0 3rem">
  <div class="container">
    {filters_html}

    <div class="product-grid" data-category-grid data-category="{cat_key}">
      {cards}
    </div>

    <div style="text-align:center;margin-top:2rem">
      <a href="../comparador.html" class="btn btn-primary">Comparar productos</a>
      <a href="../{cfg["guide_slug"]}.html" class="btn btn-outline" style="margin-left:.5rem">Guía de compra</a>
    </div>
  </div>
</section>
{intro_html}
{guias_cat_html}
</main>
{footer_html(depth=1)}
{scripts_html(depth=1)}'''

    outdir = os.path.join(BASE, cfg["slug"])
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "index.html")
    escribir(outpath, content)
    print(f"  - Categoría: {cfg['slug']}/index.html")

# ── Comparador ──────────────────────────────────────────────

def build_comparador():
    content = f'''{head_html("Comparador de productos", "Compara hasta 3 productos lado a lado: especificaciones, puntuaciones y precios.", canonical="comparador.html")}
{nav_html("comparador")}
<main id="main">
<section class="comparador" data-comparador>
  <div class="container">
    <h1 class="section-title">Comparador</h1>
    <p class="section-subtitle">Selecciona hasta 3 productos para compararlos lado a lado</p>

    <div class="compare-selector"></div>

    <div class="compare-radar-wrap" style="display:none">
      <div class="compare-radar-target"></div>
      <div class="compare-radar-legend"></div>
    </div>

    <div class="compare-table-wrap">
      <p style="padding:2rem;text-align:center;color:var(--text-muted)">Selecciona al menos 2 productos para comparar</p>
    </div>
  </div>
</section>
</main>
{footer_html()}
{scripts_html()}'''

    outpath = os.path.join(BASE, "comparador.html")
    escribir(outpath, content)
    print(f"  - comparador.html")

# ── Guide: deshumidificadores ──────────────────────────────

def build_guide_deshumidificadores():
    content = f'''{head_html("Cómo elegir el mejor deshumidificador para tu hogar", "Guía completa para elegir deshumidificador: capacidad, ruido, funciones, precio y más. Todo lo que necesitas saber antes de comprar.", canonical="guia-deshumidificadores.html", og_type="article", extra_head=jsonld(articulo_ld("Cómo elegir el mejor deshumidificador para tu hogar", "Guía completa para elegir deshumidificador: capacidad, ruido, funciones, precio y más. Todo lo que necesitas saber antes de comprar.", "guia-deshumidificadores.html"), migas_ld([("Inicio", ""), ("Cómo elegir el mejor deshumidificador para tu hogar", "guia-deshumidificadores.html")])))}
{nav_html("guias")}
<main id="main">
<section class="guide">
  <div class="container guide-content">
    <nav class="breadcrumb">
      <a href="index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Guía de compra</span>
    </nav>
    <h1>Cómo elegir el mejor deshumidificador para tu hogar</h1>
    <p style="color:var(--text-muted);margin-bottom:2rem">Actualizado: septiembre 2026 · Lectura: 8 minutos</p>

    <div class="guide-toc">
      <h3>En esta guía</h3>
      <ol>
        <li><a href="#por-que">¿Por qué necesitas un deshumidificador?</a></li>
        <li><a href="#capacidad">Capacidad de extracción: cuántos litros necesitas</a></li>
        <li><a href="#ruido">Nivel de ruido: dB que importan</a></li>
        <li><a href="#funciones">Funciones que marcan la diferencia</a></li>
        <li><a href="#precio">¿Cuánto debería costar?</a></li>
        <li><a href="#recomendaciones">Nuestras recomendaciones</a></li>
      </ol>
    </div>

    <h2 id="por-que">¿Por qué necesitas un deshumidificador?</h2>
    <p>La humedad excesiva en el hogar no es solo una cuestión de confort. Cuando la humedad relativa supera el 60% de forma constante, aparecen problemas reales: moho en paredes y techos, condensación en ventanas, olores persistentes e incluso problemas respiratorios, especialmente en personas con alergias o asma.</p>
    <p>En España, las zonas costeras y las viviendas con mala ventilación son las más afectadas. Si ves gotas de agua en las ventanas por las mañanas, manchas oscuras en las esquinas o notas un olor a humedad al entrar en casa, un deshumidificador puede resolver el problema de raíz.</p>

    <h2 id="capacidad">Capacidad de extracción: cuántos litros necesitas</h2>
    <p>La capacidad se mide en litros por día (L/día) y es el dato más importante. Pero cuidado: los fabricantes miden a 30°C y 80% de humedad relativa — condiciones que rara vez se dan en un hogar español medio.</p>
    <ul>
      <li><strong>Hasta 10 L/día:</strong> baños, vestidores, habitaciones pequeñas (hasta 15 m²)</li>
      <li><strong>12-16 L/día:</strong> dormitorios, despachos, cocinas (15-30 m²)</li>
      <li><strong>20+ L/día:</strong> salones, sótanos, pisos completos (30-50 m²)</li>
    </ul>

    <h2 id="ruido">Nivel de ruido: dB que importan</h2>
    <p>El ruido es el factor que más gente subestima al comprar. Un deshumidificador puede funcionar durante horas, y si suena demasiado, acabarás apagándolo.</p>
    <ul>
      <li><strong>Menos de 40 dB:</strong> silencioso, apto para dormitorios</li>
      <li><strong>40-45 dB:</strong> moderado, equivale a una conversación en voz baja</li>
      <li><strong>Más de 45 dB:</strong> perceptible, mejor para estancias donde no duermes</li>
    </ul>

    <h2 id="funciones">Funciones que marcan la diferencia</h2>
    <ul>
      <li><strong>Higrostato automático:</strong> mide la humedad y se enciende/apaga solo. Imprescindible.</li>
      <li><strong>Temporizador:</strong> programar encendido/apagado ahorra electricidad.</li>
      <li><strong>Modo secado de ropa:</strong> ventilador a máxima potencia. Muy útil en invierno.</li>
      <li><strong>Desagüe continuo:</strong> olvídate de vaciar el depósito.</li>
      <li><strong>Control por app/Wi-Fi:</strong> cómodo si lo dejas encendido al salir de casa.</li>
    </ul>

    <h2 id="precio">¿Cuánto debería costar?</h2>
    <ul>
      <li><strong>130-180 €:</strong> modelos básicos de 10-12 L/día.</li>
      <li><strong>180-250 €:</strong> el <em>sweet spot</em>. Modelos de 20 L/día con buenas funciones.</li>
      <li><strong>250-400 €:</strong> gama alta. Más silenciosos, mejor cobertura, marcas premium.</li>
    </ul>

    <h2 id="recomendaciones">Nuestras recomendaciones</h2>
    <ul>
      <li><strong>Mejor relación calidad-precio:</strong> <a href="deshumidificadores/pro-breeze-omnidry-20l.html" style="color:var(--accent)">Pro Breeze OmniDry 20L</a> — 199,99 €</li>
      <li><strong>Más económico:</strong> <a href="deshumidificadores/pro-breeze-compacto-12l.html" style="color:var(--accent)">Pro Breeze Compacto 12L</a> — 132,99 €</li>
      <li><strong>Marca premium:</strong> <a href="deshumidificadores/delonghi-ariadry-dexd216rf.html" style="color:var(--accent)">De'Longhi AriaDry DEXD216RF</a> — 233,00 €</li>
    </ul>

    <div style="text-align:center;margin:2.5rem 0">
      <a href="comparador.html" class="btn btn-primary btn-lg">Comparar los 3 modelos</a>
    </div>
  </div>
</section>
</main>
{footer_html()}
{scripts_html()}'''

    outpath = os.path.join(BASE, "guia-deshumidificadores.html")
    escribir(outpath, content)
    print(f"  - guia-deshumidificadores.html")

# ── Guide: purificadores ───────────────────────────────────

def build_guide_purificadores():
    content = f'''{head_html("Cómo elegir el mejor purificador de aire para tu hogar", "Guía para elegir purificador de aire: cobertura, CADR, filtro HEPA, ruido y precio. Todo lo que conviene saber antes de comprar.", canonical="guia-purificadores.html", og_type="article", extra_head=jsonld(articulo_ld("Cómo elegir el mejor purificador de aire para tu hogar", "Guía para elegir purificador de aire: cobertura, CADR, filtro HEPA, ruido y precio. Todo lo que conviene saber antes de comprar.", "guia-purificadores.html"), migas_ld([("Inicio", ""), ("Cómo elegir el mejor purificador de aire para tu hogar", "guia-purificadores.html")])))}
{nav_html("guias")}
<main id="main">
<section class="guide">
  <div class="container guide-content">
    <nav class="breadcrumb">
      <a href="index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Guía de compra</span>
    </nav>
    <h1>Cómo elegir el mejor purificador de aire para tu hogar</h1>
    <p style="color:var(--text-muted);margin-bottom:2rem">Actualizado: septiembre 2026 · Lectura: 8 minutos</p>

    <div class="guide-toc">
      <h3>En esta guía</h3>
      <ol>
        <li><a href="#por-que">¿Para qué sirve de verdad un purificador?</a></li>
        <li><a href="#cobertura">Cobertura y CADR: el dato que importa</a></li>
        <li><a href="#filtros">Filtros: HEPA, carbón activo y prefiltro</a></li>
        <li><a href="#ruido">Nivel de ruido: los dB que importan de noche</a></li>
        <li><a href="#funciones">Funciones que marcan la diferencia</a></li>
        <li><a href="#precio">¿Cuánto debería costar?</a></li>
        <li><a href="#recomendaciones">Nuestra selección</a></li>
      </ol>
    </div>

    <h2 id="por-que">¿Para qué sirve de verdad un purificador?</h2>
    <p>Un purificador de aire hace pasar el aire de la habitación por uno o varios filtros y retiene partículas que no ves: polvo fino, polen, pelo y caspa de mascotas, esporas de moho, humo y parte de los olores. No ventila ni sustituye a abrir la ventana, pero en una casa cerrada —con alergias, animales o una calle con mucho tráfico— reduce de forma notable lo que respiras.</p>
    <p>Conviene tener claras sus limitaciones: no elimina el CO2 ni la humedad, y contra los virus su efecto es parcial. Si tu problema es la condensación o el moho por exceso de humedad, lo que necesitas es un <a href="deshumidificadores/index.html" style="color:var(--accent)">deshumidificador</a>, no un purificador.</p>

    <h2 id="cobertura">Cobertura y CADR: el dato que importa</h2>
    <p>Los fabricantes anuncian una cobertura en metros cuadrados, pero esa cifra suele calcularse para una sola renovación de aire por hora, que es poco. El dato honesto es el <strong>CADR</strong> (Clean Air Delivery Rate, en m³/h): cuánto aire limpio entrega por hora. A más CADR, antes limpia la sala y mejor la mantiene.</p>
    <ul>
      <li><strong>CADR de 150-250 m³/h:</strong> dormitorios y despachos (hasta 20-30 m²).</li>
      <li><strong>CADR de 250-400 m³/h:</strong> salones y salas de estar (30-50 m²).</li>
      <li><strong>Más de 400 m³/h:</strong> estancias grandes o diáfanas.</li>
    </ul>
    <p>Una regla práctica: elige un modelo cuya cobertura supere con holgura tu habitación, para que funcione en velocidad baja (silenciosa) la mayor parte del tiempo.</p>

    <h2 id="filtros">Filtros: HEPA, carbón activo y prefiltro</h2>
    <ul>
      <li><strong>Filtro HEPA (H13 o superior):</strong> es el que retiene las partículas finas. Imprescindible; sin HEPA real, no es un purificador serio.</li>
      <li><strong>Carbón activo:</strong> absorbe olores y gases (cocina, tabaco, mascotas). Si te importan los olores, que no falte.</li>
      <li><strong>Prefiltro lavable:</strong> atrapa pelo y polvo grueso y alarga la vida del HEPA. Que se pueda lavar te ahorra dinero.</li>
      <li><strong>Coste de recambios:</strong> el filtro es un gasto recurrente. Mira antes cuánto cuesta el repuesto y cada cuánto se cambia (suele ser cada 6-12 meses).</li>
    </ul>

    <h2 id="ruido">Nivel de ruido: los dB que importan de noche</h2>
    <p>Un purificador se deja encendido muchas horas, a veces toda la noche. Si en velocidad baja suena demasiado, acabarás apagándolo.</p>
    <ul>
      <li><strong>Menos de 35 dB:</strong> apenas se oye, perfecto para dormir.</li>
      <li><strong>35-45 dB:</strong> ruido de fondo suave, aceptable en el salón.</li>
      <li><strong>Más de 50 dB (velocidad alta):</strong> normal solo para limpiar rápido; no para tenerlo así de continuo.</li>
    </ul>

    <h2 id="funciones">Funciones que marcan la diferencia</h2>
    <ul>
      <li><strong>Sensor de calidad del aire:</strong> mide las partículas y ajusta la velocidad solo. La función más útil.</li>
      <li><strong>Modo automático:</strong> sube cuando el aire empeora y baja cuando mejora, sin que estés pendiente.</li>
      <li><strong>Modo noche:</strong> velocidad mínima y luces apagadas.</li>
      <li><strong>Aviso de cambio de filtro:</strong> te avisa cuando toca, para no respirar por un filtro saturado.</li>
      <li><strong>Control por app:</strong> cómodo para programarlo o encenderlo antes de llegar a casa.</li>
    </ul>

    <h2 id="precio">¿Cuánto debería costar?</h2>
    <ul>
      <li><strong>60-120 €:</strong> modelos para habitación, con HEPA y poco más.</li>
      <li><strong>120-250 €:</strong> el punto dulce. Buena cobertura, sensor automático y modo noche.</li>
      <li><strong>250-400 €:</strong> gama alta, para salas grandes, más silenciosos y con mejores sensores.</li>
    </ul>

    <h2 id="recomendaciones">Nuestra selección</h2>
    <p>Estamos analizando los primeros modelos de esta categoría. Puedes ver los que ya hemos revisado —con su tabla de especificaciones, puntuaciones y precio— en la página de purificadores.</p>

    <div style="text-align:center;margin:2.5rem 0">
      <a href="purificadores/index.html" class="btn btn-primary btn-lg">Ver los purificadores analizados</a>
    </div>
  </div>
</section>
</main>
{footer_html()}
{scripts_html()}'''

    outpath = os.path.join(BASE, "guia-purificadores.html")
    escribir(outpath, content)
    print(f"  - guia-purificadores.html")

# ── Guide: calefactores ────────────────────────────────────

def build_guide_calefactores():
    content = f'''{head_html("Cómo elegir el mejor calefactor para tu hogar", "Guía completa para elegir calefactor: cerámicos, radiadores de aceite, paneles y estufas de cuarzo. Todo lo que necesitas saber antes de comprar.", canonical="guia-calefactores.html", og_type="article", extra_head=jsonld(articulo_ld("Cómo elegir el mejor calefactor para tu hogar", "Guía completa para elegir calefactor: cerámicos, radiadores de aceite, paneles y estufas de cuarzo. Todo lo que necesitas saber antes de comprar.", "guia-calefactores.html"), migas_ld([("Inicio", ""), ("Cómo elegir el mejor calefactor para tu hogar", "guia-calefactores.html")])))}
{nav_html("guias")}
<main id="main">
<section class="guide">
  <div class="container guide-content">
    <nav class="breadcrumb">
      <a href="index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Guía de calefactores</span>
    </nav>
    <h1>Cómo elegir el mejor calefactor para tu hogar</h1>
    <p style="color:var(--text-muted);margin-bottom:2rem">Actualizado: septiembre 2026 · Lectura: 10 minutos</p>

    <div class="guide-toc">
      <h3>En esta guía</h3>
      <ol>
        <li><a href="#tipos">Tipos de calefactores: cuál es el tuyo</a></li>
        <li><a href="#potencia">Potencia: cuántos vatios necesitas</a></li>
        <li><a href="#silencio">Ruido: cerámicos vs. radiadores de aceite</a></li>
        <li><a href="#seguridad">Seguridad: lo que debes exigir</a></li>
        <li><a href="#consumo">Consumo eléctrico: la cuenta que nadie hace</a></li>
        <li><a href="#funciones">Funciones que merecen la pena</a></li>
        <li><a href="#recomendaciones">Nuestras recomendaciones por tipo</a></li>
      </ol>
    </div>

    <h2 id="tipos">Tipos de calefactores: cuál es el tuyo</h2>
    <p>No todos los calefactores funcionan igual ni sirven para lo mismo. Elegir el tipo correcto es la decisión más importante:</p>

    <h3>Calefactores cerámicos</h3>
    <p>Calientan mediante una resistencia cerámica y un ventilador que distribuye el aire caliente. Son compactos, ligeros y calientan rápido, pero hacen algo de ruido por el ventilador. Ideales para calentar habitaciones pequeñas-medianas en minutos.</p>
    <p><strong>Mejor para:</strong> baños (con IP21), despachos, dormitorios, calor rápido.</p>

    <h3>Radiadores de aceite</h3>
    <p>Calientan aceite térmico interno que irradia calor de forma constante y silenciosa. Tardan más en alcanzar temperatura pero mantienen el calor incluso después de apagados. Completamente silenciosos.</p>
    <p><strong>Mejor para:</strong> dormitorios, despachos, uso prolongado, quien no soporta el ruido.</p>

    <h3>Paneles y convectores</h3>
    <p>Calientan el aire por convección natural (o forzada con turbo). Diseño slim que permite montaje en pared. Modernos, algunos con panel de cristal decorativo.</p>
    <p><strong>Mejor para:</strong> salones, pasillos, montaje en pared, quien valora el diseño.</p>

    <h3>Estufas halógenas / de cuarzo</h3>
    <p>Producen calor radiante instantáneo mediante barras de cuarzo o halógenas. No calientan el aire sino los objetos y personas que tienen delante. Muy baratas pero solo para calor puntual.</p>
    <p><strong>Mejor para:</strong> calor inmediato, bajo el escritorio, complemento a la calefacción central.</p>

    <h2 id="potencia">Potencia: cuántos vatios necesitas</h2>
    <p>La regla general es <strong>100 W por m²</strong> en una vivienda con aislamiento normal. En la práctica:</p>
    <ul>
      <li><strong>Hasta 1000 W:</strong> baños pequeños, uso puntual (5-10 m²)</li>
      <li><strong>1000-1500 W:</strong> dormitorios, despachos (10-15 m²)</li>
      <li><strong>1500-2000 W:</strong> salones pequeños, habitaciones amplias (15-20 m²)</li>
      <li><strong>2000-2500 W:</strong> salones grandes, estancias diáfanas (20-25 m²)</li>
    </ul>
    <p><strong>Importante:</strong> un calefactor eléctrico de 2000 W encendido 8 horas consume unos 16 kWh, que a tarifa media española (~0,15 €/kWh) supone <strong>~2,40 € al día</strong>. Usar el termostato y elegir el nivel de potencia adecuado reduce mucho el consumo real.</p>

    <h2 id="silencio">Ruido: cerámicos vs. radiadores de aceite</h2>
    <p>Si el silencio es prioridad, la elección es clara: los <strong>radiadores de aceite son completamente silenciosos</strong> (0 dB). No tienen ventilador ni partes móviles.</p>
    <p>Los calefactores cerámicos y convectores con turbo generan ruido por el ventilador, típicamente entre 40-55 dB. Para dormitorios donde duermes, un radiador de aceite es siempre mejor opción.</p>

    <h2 id="seguridad">Seguridad: lo que debes exigir</h2>
    <ul>
      <li><strong>Protección antivuelco:</strong> se apaga si se cae. Imprescindible si hay niños o mascotas.</li>
      <li><strong>Protección contra sobrecalentamiento:</strong> se apaga si alcanza temperatura peligrosa. Todos los modelos buenos la incluyen.</li>
      <li><strong>IP21 o superior:</strong> obligatorio si vas a usarlo en el baño. Sin esta certificación, usar un calefactor en el baño es peligroso.</li>
      <li><strong>Temporizador:</strong> no es seguridad directa, pero evita dejarlo encendido por olvido.</li>
    </ul>

    <h2 id="consumo">Consumo eléctrico: la cuenta que nadie hace</h2>
    <p>Todos los calefactores eléctricos convierten electricidad en calor con eficiencia del ~100%. La diferencia está en <strong>cómo y cuánto tiempo</strong> necesitan funcionar:</p>
    <ul>
      <li><strong>Cerámicos:</strong> calientan rápido pero consumen a máxima potencia. Buenos para uso corto e intenso.</li>
      <li><strong>Radiadores de aceite:</strong> tardan más pero mantienen el calor residual. Mejores para uso prolongado.</li>
      <li><strong>Estufas de cuarzo:</strong> calor instantáneo pero solo direccional. Consumen poco si solo quieres calentar a una persona.</li>
    </ul>
    <p><strong>Consejo:</strong> usa siempre el termostato y el nivel de potencia mínimo que necesites. Un calefactor de 2500 W usado a 1000 W consume menos de la mitad.</p>

    <h2 id="funciones">Funciones que merecen la pena</h2>
    <ul>
      <li><strong>Termostato:</strong> mantiene la temperatura sin que tengas que estar pendiente. Básico.</li>
      <li><strong>Varios niveles de potencia:</strong> permiten ajustar consumo al tamaño de la habitación.</li>
      <li><strong>Temporizador:</strong> programar apagado ahorra electricidad y añade seguridad.</li>
      <li><strong>Oscilación:</strong> en cerámicos, distribuye el calor más uniformemente.</li>
      <li><strong>Wi-Fi / App:</strong> útil para encenderlo antes de llegar a casa. No esencial.</li>
      <li><strong>Anti-heladas:</strong> se enciende solo si la temperatura baja de 0 °C. Genial para segundas residencias.</li>
    </ul>

    <h2 id="recomendaciones">Nuestras recomendaciones por tipo</h2>

    <h3>Cerámicos</h3>
    <ul>
      <li><strong>Chollo compacto:</strong> <a href="calefactores/jata-tc73-calefactor-ceramico-1200w.html" style="color:var(--accent)">Jata TC73</a> — 31,90 € (silencioso, ventilador)</li>
      <li><strong>Más smart:</strong> <a href="calefactores/cecotec-ready-warm-10100-smart-ceramic.html" style="color:var(--accent)">Cecotec Ready Warm 10100</a> — 49,90 € (Wi-Fi)</li>
      <li><strong>Mejor precio:</strong> <a href="calefactores/pro-breeze-mini-ceramico-2000w.html" style="color:var(--accent)">Pro Breeze Mini 2000W</a> — 37,99 €</li>
    </ul>

    <h3>Radiadores de aceite</h3>
    <ul>
      <li><strong>Premium silencioso:</strong> <a href="calefactores/delonghi-trrs-0920-radia-s.html" style="color:var(--accent)">De'Longhi TRRS 0920 Radia S</a> — 128,00 €</li>
      <li><strong>Mejor precio:</strong> <a href="calefactores/orbegozo-rf-2000-radiador-aceite.html" style="color:var(--accent)">Orbegozo RF 2000</a> — 60,30 €</li>
    </ul>

    <h3>Paneles y emisores</h3>
    <ul>
      <li><strong>Emisor de pared:</strong> <a href="calefactores/orbegozo-rre-1310.html" style="color:var(--accent)">Orbegozo RRE 1310</a> — 158,50 €</li>
      <li><strong>Con turbo:</strong> <a href="calefactores/rowenta-vectissimo-ii-co3030.html" style="color:var(--accent)">Rowenta Vectissimo II CO3030</a> — 71,94 €</li>
      <li><strong>Diseño premium:</strong> <a href="calefactores/cecotec-ready-warm-6650-crystal-connection.html" style="color:var(--accent)">Cecotec Crystal Connection</a> — 79,90 €</li>
    </ul>

    <h3>Cuarzo</h3>
    <ul>
      <li><strong>La más barata:</strong> <a href="calefactores/orbegozo-bp-5003.html" style="color:var(--accent)">Orbegozo BP 5003</a> — 19,98 €</li>
    </ul>

    <div style="text-align:center;margin:2.5rem 0">
      <a href="calefactores/index.html" class="btn btn-primary btn-lg">Ver todos los calefactores</a>
      <a href="comparador.html" class="btn btn-outline btn-lg" style="margin-left:.5rem">Comparar modelos</a>
    </div>
  </div>
</section>
</main>
{footer_html()}
{scripts_html()}'''

    outpath = os.path.join(BASE, "guia-calefactores.html")
    escribir(outpath, content)
    print(f"  - guia-calefactores.html")

# ── Legal pages ─────────────────────────────────────────────

def build_legal_pages():
    pages = {
        "aviso-afiliados.html": ("Aviso de afiliación", '''
    <h1>Aviso de afiliación</h1>
    <p>elclimadecasa.com participa en el <strong>Programa de Afiliados de Amazon EU</strong>, un programa de publicidad para afiliados diseñado para ofrecer a sitios web un modo de obtener comisiones por publicidad, publicitando e incluyendo enlaces a Amazon.es.</p>
    <h2>¿Qué significa esto para ti?</h2>
    <p>Cuando haces clic en uno de nuestros enlaces a Amazon y realizas una compra, nosotros recibimos una pequeña comisión. <strong>Esto no tiene ningún coste adicional para ti</strong>.</p>
    <h2>¿Afecta esto a nuestras recomendaciones?</h2>
    <p>No. Nuestras recomendaciones se basan únicamente en el análisis objetivo de las especificaciones, las valoraciones de los usuarios y nuestra propia evaluación editorial.</p>
    <h2>Sobre los precios</h2>
    <p>Los precios que mostramos son <strong>orientativos</strong> y corresponden al momento en que se capturaron los datos de Amazon. Los precios pueden variar en cualquier momento.</p>
    <h2>Marca registrada</h2>
    <p>Amazon y el logotipo de Amazon son marcas registradas de Amazon.com, Inc. o sus afiliados.</p>
'''),
        "privacidad.html": ("Política de privacidad", '''
    <h1>Política de privacidad</h1>
    <p>Última actualización: septiembre 2026</p>
    <h2>Responsable del tratamiento</h2>
    <p>El responsable del tratamiento de los datos personales es <strong>Jordi Escoda Sirvent</strong> (hola@jordiescodasirvent.com).</p>
    <h2>Datos que recopilamos</h2>
    <p>Este sitio web no recopila datos personales directamente. Utilizamos Google Analytics para analíticas de tráfico. Cuando haces clic en un enlace de afiliado, Amazon recopila datos según su propia política de privacidad.</p>
    <h2>Cookies</h2>
    <p>Este sitio web utiliza cookies de Google Analytics para analíticas de tráfico. Los servicios de terceros pueden establecer sus propias cookies según sus respectivas políticas.</p>
    <h2>Tus derechos</h2>
    <p>Tienes derecho a acceder, rectificar, suprimir, limitar y oponerte al tratamiento de tus datos personales conforme al RGPD.</p>
'''),
        "aviso-legal.html": ("Aviso legal", '''
    <h1>Aviso legal</h1>
    <p>Última actualización: septiembre 2026</p>
    <h2>Información general</h2>
    <p>En cumplimiento de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y Comercio Electrónico (LSSI-CE):</p>
    <ul>
      <li><strong>Titular:</strong> Jordi Escoda Sirvent</li>
      <li><strong>Sitio web:</strong> elclimadecasa.com</li>
      <li><strong>Correo de contacto:</strong> hola@jordiescodasirvent.com</li>
    </ul>
    <h2>Objeto del sitio web</h2>
    <p>elclimadecasa.com es un sitio web de información y comparativas de productos de climatización del hogar. El sitio contiene enlaces de afiliado a Amazon.es (ver <a href="aviso-afiliados.html" style="color:var(--accent)">aviso de afiliación</a>).</p>
    <h2>Propiedad intelectual</h2>
    <p>El contenido editorial de este sitio web es propiedad de su titular. Los nombres de producto, marcas y logotipos pertenecen a sus respectivos propietarios.</p>
    <h2>Limitación de responsabilidad</h2>
    <p>La información publicada tiene carácter informativo y orientativo. Los precios y especificaciones son orientativos y pueden variar.</p>
'''),
    }

    for filename, (title, body) in pages.items():
        content = f'''{head_html(title, f"{title} de elclimadecasa.com", canonical=filename)}
{nav_html("")}
<main id="main">
<section class="legal">
  <div class="container legal-content">
    {body}
  </div>
</section>
</main>
{footer_html()}
{scripts_html()}'''

        outpath = os.path.join(BASE, filename)
        escribir(outpath, content)
        print(f"  - {filename}")

# ── DB.js ───────────────────────────────────────────────────

def rebuild_db_js(products):
    import json as j
    db_data = {
        "productos": products,
        "nichos": ["deshumidificadores", "calefactores", "purificadores"],
        "categorias": [
            {"id": "deshumidificadores", "nombre": "Deshumidificadores", "slug": "deshumidificadores", "activa": True},
            {"id": "calefactores", "nombre": "Calefactores", "slug": "calefactores", "activa": True},
            {"id": "purificadores", "nombre": "Purificadores", "slug": "purificadores", "activa": True},
            {"id": "aires-acondicionados", "nombre": "Aires Acondicionados", "slug": "aires-acondicionados", "activa": False},
            {"id": "ventiladores", "nombre": "Ventiladores", "slug": "ventiladores", "activa": False},
        ],
        "scoreAxes": ["eficiencia", "silencio", "facilidad_uso", "capacidad", "calidad_precio"],
        "scoreLabels": {
            "eficiencia": "Eficiencia",
            "silencio": "Silencio",
            "facilidad_uso": "Facilidad de uso",
            "capacidad": "Capacidad",
            "calidad_precio": "Calidad/Precio"
        },
        "compareSpecs": {
            "deshumidificadores": COMPARE_SPECS_DH,
            "calefactores": COMPARE_SPECS_CAL,
            "purificadores": COMPARE_SPECS_PUR,
        },
        "updated": datetime.now().strftime("%Y-%m-%d")
    }
    js = '(function(){"use strict";window.__DB__=' + j.dumps(db_data, ensure_ascii=False) + ';})();'
    outpath = os.path.join(BASE, "lib", "db.js")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  - lib/db.js (actualizado)")


# ── Guías editoriales ─────────────────────────────

HOME_FEATURED = ["dh-001", "cal-003", "cal-004", "dh-002"]

CATEGORY_ORDER = ["deshumidificadores", "calefactores", "purificadores"]

PROXIMAMENTE = ["Aires acondicionados", "Ventiladores"]


def load_guias():
    path = os.path.join(BASE, "datos", "guias.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def product_by_id(products, pid):
    for p in products:
        if p["id"] == pid:
            return p
    return None


def product_href(p, depth=1):
    """Ruta a la ficha del producto desde una página a profundidad `depth`."""
    prefix = "../" * depth
    cat = CATEGORY_CONFIG.get(p.get("category", ""), {}).get("slug", p.get("category", ""))
    return "{}{}/{}.html".format(prefix, cat, product_slug(p))


def expand_tokens(body, products, depth=1):
    """Sustituye [[ficha:id|texto]], [[enlace:id|texto]] y [[figura:id|pie]]."""

    def repl(m):
        kind, pid, text = m.group(1), m.group(2), (m.group(3) or "").strip()
        p = product_by_id(products, pid)
        if not p:
            return text or ""
        if kind == "ficha":
            return '<a href="{}">{}</a>'.format(product_href(p, depth), esc(text or p["name"]))
        if kind == "enlace":
            return '<a href="{}" target="_blank" rel="nofollow noopener sponsored">{}</a>'.format(
                esc(p["affiliate_url"]), esc(text or p["name"]))
        if kind == "figura":
            caption = ""
            if text:
                caption = "<figcaption>{}</figcaption>".format(esc(text))
            return '<figure class="article-figure"><a href="{}">{}</a>{}</figure>'.format(
                product_href(p, depth), product_img(p, 0, depth=depth), caption)
        return text or ""

    return re.sub(r"\[\[(ficha|enlace|figura):([a-z0-9-]+)\|?([^\]]*)\]\]", repl, body)


def mentioned_block(guia, products, depth=1):
    ids = guia.get("productos", [])
    if not ids:
        return ""
    cards = ""
    for pid in ids:
        p = product_by_id(products, pid)
        if not p:
            continue
        price = p.get("discountedPrice") or p.get("retailPrice")
        cards += """<article class="mentioned-card">
  <div class="product-card-img">{img}</div>
  <div class="product-card-brand">{marca}</div>
  <h3><a href="{href}">{name}</a></h3>
  <span class="price-current">{price}</span>
  <p class="mentioned-links"><a href="{href}">Ver análisis</a><a href="{aff}" target="_blank" rel="nofollow noopener sponsored">Ver en Amazon</a></p>
</article>
""".format(img=product_img(p, 0, depth=depth), marca=esc(p["marca"]), href=product_href(p, depth),
           name=esc(p["name"]), price=format_price(price), aff=esc(p["affiliate_url"]))

    return """<section class="mentioned">
  <h2>Productos mencionados en esta guía</h2>
  <div class="mentioned-grid">
{cards}  </div>
  <p class="price-note">Precios orientativos, consultados en Amazon. Pueden cambiar en cualquier momento.</p>
</section>""".format(cards=cards)


def guide_og_image(guia, products):
    for pid in guia.get("productos", []):
        p = product_by_id(products, pid)
        if p and p.get("images"):
            return p["images"][0]
    return ""


def build_guia(guia, products, guias=None):
    guias = guias or []
    body = expand_tokens(guia.get("cuerpo", ""), products, depth=1)
    canonical = "guias/{}.html".format(guia["slug"])

    cat_key = cat_key_por_titulo(guia.get("categoria", ""))
    otras = []
    pie_guias = ""
    if cat_key:
        cfg_g = CATEGORY_CONFIG[cat_key]
        otras = [g for g in guias_de_categoria(guias, cat_key)
                 if g["slug"] != guia["slug"]][:3]
        pie_guias = ('<p class="related-more">'
                     '<a href="../{slug}/index.html">Ver todos los {t}</a> · '
                     '<a href="../{gs}.html">Guía de compra</a></p>').format(
                        slug=cfg_g["slug"], t=esc(cfg_g["title"].lower()),
                        gs=cfg_g["guide_slug"])
    sigue_leyendo = guias_relacionadas_html(
        otras, depth=1, titulo="Sigue leyendo", pie_html=pie_guias)

    content = """{head}
{nav}
<main id="main">
<article class="article">
  <div class="container article-content">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <a href="index.html">Guías</a> <span class="breadcrumb-sep">/</span>
      <span>{cat}</span>
    </nav>
    <header class="article-header">
      <h1>{title}</h1>
      <p class="article-meta">{fecha} · Lectura: {lectura}</p>
    </header>
    <p class="article-lead">{lead}</p>
    <div class="article-body">
{body}
    </div>
    {mentioned}
    {sigue}
  </div>
</article>
</main>
{footer}
{scripts}""".format(
        head=head_html(guia["title"], guia["meta_desc"], depth=1, canonical=canonical,
                       og_image=guide_og_image(guia, products), og_type="article",
                       extra_head=jsonld(
                           articulo_ld(guia["title"], guia["meta_desc"], canonical,
                                       guide_og_image(guia, products), guia.get("fecha")),
                           migas_ld([("Inicio", ""), ("Guías", "guias/"), (guia["title"], canonical)]))),
        nav=nav_html("guias", depth=1),
        cat=esc(guia.get("categoria", "Guía")),
        title=esc(guia["title"]),
        fecha=esc(guia.get("fecha_texto", "")),
        lectura=esc(guia.get("lectura", "")),
        lead=esc(guia.get("lead", "")),
        body=body,
        mentioned=mentioned_block(guia, products, depth=1),
        sigue=sigue_leyendo,
        footer=footer_html(depth=1),
        scripts=scripts_html(depth=1),
    )

    outdir = os.path.join(BASE, "guias")
    os.makedirs(outdir, exist_ok=True)
    escribir(os.path.join(outdir, guia["slug"] + ".html"), content)
    print("  - Guía: guias/{}.html".format(guia["slug"]))


def guide_list_items(guias, depth=1, limit=None):
    prefix = "../" * depth
    items = ""
    for g in (guias[:limit] if limit else guias):
        items += """<li class="guide-item">
  <p class="article-meta">{fecha} · {cat}</p>
  <h3><a href="{prefix}guias/{slug}.html">{title}</a></h3>
  <p>{extracto}</p>
  <a class="guide-item-link" href="{prefix}guias/{slug}.html">Leer la guía</a>
</li>
""".format(prefix=prefix, slug=g["slug"], title=esc(g["title"]),
           extracto=esc(g.get("extracto", "")), fecha=esc(g.get("fecha_texto", "")),
           cat=esc(g.get("categoria", "")))
    return items


# ── Enlazado interno: guías relacionadas ──────────────────────

def cat_key_por_titulo(titulo):
    """De 'Deshumidificadores'/'Calefactores' a su clave de categoría."""
    for k, c in CATEGORY_CONFIG.items():
        if c["title"] == titulo:
            return k
    return None


def guias_de_categoria(guias, cat_key):
    titulo = CATEGORY_CONFIG.get(cat_key, {}).get("title", "")
    return [g for g in guias if g.get("categoria") == titulo]


def guias_para_producto(guias, product, limit=3):
    """Guías que mencionan este producto primero; luego, las de su categoría."""
    pid = product["id"]
    mencionan = [g for g in guias if pid in g.get("productos", [])]
    vistos = {g["slug"] for g in mencionan}
    resto = [g for g in guias_de_categoria(guias, product.get("category", ""))
             if g["slug"] not in vistos]
    return (mencionan + resto)[:limit]


def guias_relacionadas_html(subset, depth, titulo="Guías relacionadas", pie_html=""):
    if not subset and not pie_html:
        return ""
    lista = ""
    if subset:
        lista = '<ul class="guide-list">\n{}    </ul>'.format(
            guide_list_items(subset, depth=depth))
    return '''<section class="home-section related-guides">
      <h2>{titulo}</h2>
      {lista}
      {pie}
    </section>'''.format(titulo=esc(titulo), lista=lista, pie=pie_html)


def build_guias_index(guias):
    items = guide_list_items(guias, depth=1)

    content = """{head}
{nav}
<main id="main">
<section class="page-header">
  <div class="container container-narrow">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Guías</span>
    </nav>
    <h1>Guías</h1>
    <p>Artículos sobre humedad, calefacción y confort en casa: cómo detectar un problema, qué opciones hay y qué aparato tiene sentido en cada caso.</p>
  </div>
</section>
<section class="home-section">
  <div class="container container-narrow">
    <ul class="guide-list">
{items}    </ul>
  </div>
</section>
<section class="home-section">
  <div class="container container-narrow">
    <h2>Guías de compra por categoría</h2>
    <ul>
      <li><a href="../guia-deshumidificadores.html">Cómo elegir el mejor deshumidificador para tu hogar</a></li>
      <li><a href="../guia-calefactores.html">Cómo elegir el mejor calefactor para tu hogar</a></li>
    </ul>
  </div>
</section>
</main>
{footer}
{scripts}""".format(
        head=head_html("Guías", "Guías prácticas sobre humedad, calefacción y climatización del hogar: cómo detectar problemas y qué soluciones funcionan de verdad.", depth=1, canonical="guias/"),
        nav=nav_html("guias", depth=1),
        items=items,
        footer=footer_html(depth=1),
        scripts=scripts_html(depth=1),
    )

    outdir = os.path.join(BASE, "guias")
    os.makedirs(outdir, exist_ok=True)
    escribir(os.path.join(outdir, "index.html"), content)
    print("  - guias/index.html")


# ── Portada ───────────────────────────────────

def home_card(p):
    price = p.get("discountedPrice") or p.get("retailPrice")
    return """<article class="product-card">
  <div class="product-card-img">{img}</div>
  <div class="product-card-body">
    <div class="product-card-brand">{marca}</div>
    <h3 class="product-card-name"><a href="{href}">{name}</a></h3>
    <p class="product-card-desc">{desc}</p>
    <div class="product-card-footer">
      <div class="price-block"><span class="price-current">{price}</span></div>
      <span class="stars">{stars} <span class="stars-count">{res}</span></span>
    </div>
  </div>
</article>
""".format(img=product_img(p, 0, depth=0), marca=esc(p["marca"]), href=product_href(p, depth=0),
           name=esc(p["name"]), desc=esc(p.get("description", "")), price=format_price(price),
           stars=stars_html(p.get("valoracion_media")), res=resenas_txt(p))


def build_home(products, guias):
    cards = ""
    for pid in HOME_FEATURED:
        p = product_by_id(products, pid)
        if p:
            cards += home_card(p)

    cats = ""
    for key in CATEGORY_ORDER:
        cfg = CATEGORY_CONFIG[key]
        n = len([p for p in products if p["category"] == key])
        cats += '      <li><a href="{slug}/index.html">{title}</a> <span class="cat-count">{n} productos analizados</span></li>\n'.format(
            slug=cfg["slug"], title=esc(cfg["title"]), n=n)
    cats += '      <li class="cat-soon">{} <span>(en preparación)</span></li>\n'.format(", ".join(PROXIMAMENTE))

    content = """{head}
{nav}
<main id="main">
<div class="container">

  <section class="home-intro">
    <h1>Guías y análisis de climatización para el hogar</h1>
    <p>Analizamos aparatos de climatización para casa — deshumidificadores, calefactores y todo lo que ayuda a estar cómodo dentro — y contamos cuál tiene sentido en cada situación. Leemos las opiniones de compradores reales, comparamos las especificaciones y explicamos lo que no aparece en la caja.</p>
  </section>

  <section class="home-section">
    <div class="home-section-head">
      <h2>Últimas guías</h2>
      <a href="guias/index.html">Ver todas las guías</a>
    </div>
    <ul class="guide-list">
{guias}    </ul>
  </section>

  <section class="home-section">
    <div class="home-section-head">
      <h2>Categorías</h2>
    </div>
    <ul class="cat-list">
{cats}    </ul>
  </section>

  <section class="home-section">
    <div class="home-section-head">
      <h2>Productos destacados</h2>
      <a href="comparador.html">Comparar modelos</a>
    </div>
    <div class="product-grid featured-grid">
{cards}    </div>
    <p class="price-note">Precios orientativos, consultados en Amazon. Pueden cambiar en cualquier momento.</p>
  </section>

</div>
</main>
{footer}
{scripts}""".format(
        head=head_html("El Clima de Casa", "Guías y comparativas independientes de deshumidificadores y calefactores para el hogar. Qué comprar, cuándo hace falta y qué modelo conviene en cada caso.",
                       canonical="", full_title="El Clima de Casa — Guías de climatización para tu hogar",
                       extra_head=jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": "El Clima de Casa", "url": SITE_URL + "/", "inLanguage": "es-ES"},
                                         dict(editor_ld(), **{"@context": "https://schema.org", "founder": autor_ld(), "sameAs": ["https://www.pinterest.es/elclimadecasa/"]}))),
        nav=nav_html("inicio"),
        guias=guide_list_items(guias, depth=0, limit=3),
        cats=cats,
        cards=cards,
        footer=footer_html(),
        scripts=scripts_html(),
    )

    escribir(os.path.join(BASE, "index.html"), content)
    print("  - index.html")


# ── Sobre nosotros ────────────────────────────

def build_sobre_nosotros():
    content = """{head}
{nav}
<main id="main">
<section class="article">
  <div class="container article-content">
    <nav class="breadcrumb">
      <a href="index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Sobre nosotros</span>
    </nav>
    <h1>Sobre El Clima de Casa</h1>
    <div class="article-body">
      <h2>Quién está detrás</h2>
      <p><img src="assets/img/jordi.jpg" alt="Jordi Escoda Sirvent" width="160" height="160" style="border-radius:50%;float:left;margin:0 24px 12px 0;object-fit:cover"></p>
      <p>Me llamo <strong>Jordi Escoda Sirvent</strong> y escribo este sitio desde Xixona, un pueblo del interior de Alicante donde en invierno hace frío de verdad y en verano la humedad de la costa se nota a treinta kilómetros. Empecé <em>El Clima de Casa</em> porque cada vez que un familiar me preguntaba qué calefactor comprar terminaba mandándole capturas de Amazon y notas por WhatsApp: tenía sentido ordenarlo en un sitio.</p>
      <p>Trabajo en el mundo digital desde hace años — llevo también, junto a mi hermano Mario, la pequeña agencia <a href="https://escodaproject.com" rel="noopener">Escoda Project</a>, y tengo mi propia web en <a href="https://jordiescodasirvent.com" rel="noopener">jordiescodasirvent.com</a>. Este proyecto lo llevo yo solo.</p>

      <h2>Cómo analizamos los productos</h2>
      <p>La idea es sencilla: que puedas decidir qué comprar en diez minutos y sin dudas. Para cada producto leo cientos de opiniones de compradores reales, comparo las especificaciones con las de modelos parecidos y señalo lo que no se ve en la ficha del fabricante: si hace ruido de verdad, si el depósito se queda corto, si esa función «smart» sirve para algo.</p>
      <p>También escribo guías, porque muchas veces la pregunta no es qué modelo comprar, sino si hace falta comprar algo. Si tu problema de humedad se arregla ventilando diez minutos al día, prefiero decírtelo.</p>

      <h2>Cómo se financia el sitio</h2>
      <p>No vendo nada ni tengo acuerdos con las marcas. Cuando compras a través de mis enlaces de Amazon recibo una pequeña comisión, sin coste adicional para ti, y eso es lo que mantiene el sitio en marcha. La comisión es la misma se elija el modelo que se elija, así que no hay ningún motivo para recomendarte el más caro: lo puedes comprobar en el <a href="aviso-afiliados.html">aviso de afiliación</a>.</p>
      <p>Los precios que ves son los del día en que consultamos Amazon y cambian a menudo; siempre indicamos la fecha.</p>

      <h2>Contacto</h2>
      <p>Si encuentras un dato mal, un producto que ha cambiado de versión, quieres proponer un tema o algo se me ha escapado, escríbeme a <a href="mailto:hola@jordiescodasirvent.com">hola@jordiescodasirvent.com</a>. Respondo yo mismo, normalmente en el mismo día.</p>
      <p style="color:#666;font-size:0.9em;margin-top:32px">Jordi Escoda Sirvent · Xixona, Alicante (España) · <a href="https://jordiescodasirvent.com" rel="noopener">jordiescodasirvent.com</a></p>
    </div>
  </div>
</section>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "AboutPage",
  "url": "https://elclimadecasa.com/sobre-nosotros.html",
  "mainEntity": {{
    "@type": "Person",
    "name": "Jordi Escoda Sirvent",
    "url": "https://jordiescodasirvent.com",
    "email": "hola@jordiescodasirvent.com",
    "image": "https://elclimadecasa.com/assets/img/jordi.jpg",
    "jobTitle": "Editor de El Clima de Casa",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "Xixona",
      "addressRegion": "Alicante",
      "addressCountry": "ES"
    }},
    "worksFor": {{
      "@type": "Organization",
      "name": "Escoda Project",
      "url": "https://escodaproject.com"
    }}
  }}
}}
</script>
</main>
{footer}
{scripts}""".format(
        head=head_html("Sobre nosotros", "Jordi Escoda Sirvent, desde Xixona (Alicante), analiza productos de climatización para el hogar. Cómo trabajamos, cómo se financia el sitio y cómo contactar.", canonical="sobre-nosotros.html"),
        nav=nav_html("sobre-nosotros"),
        footer=footer_html(),
        scripts=scripts_html(),
    )

    escribir(os.path.join(BASE, "sobre-nosotros.html"), content)
    print("  - sobre-nosotros.html")


# ── Sitemap ──────────────────────────────────

# ── Test de humedad ─────────────────────────────────────────

# (pregunta, [(etiqueta, puntos, clave), ...])
TEST_PREGUNTAS = [
    ("Por las mañanas, ¿hay agua en los cristales de las ventanas?", "condensacion", [
        ("No, nunca", 0, ""),
        ("Solo algún día de mucho frío", 1, ""),
        ("Varias mañanas por semana", 3, "condensa"),
        ("Casi todos los días, y el agua cae al alféizar", 5, "condensa_mucho"),
    ]),
    ("¿Notas olor a cerrado o a humedad?", "olor", [
        ("No, la casa huele normal", 0, ""),
        ("Solo dentro de un armario o de un cuarto que uso poco", 2, "olor_armario"),
        ("Se nota al entrar en casa después de unas horas fuera", 4, "olor_casa"),
        ("Siempre, y la ropa guardada coge ese olor", 6, "olor_fuerte"),
    ]),
    ("¿Hay manchas, moho o pintura levantada en alguna pared o techo?", "manchas", [
        ("Nada de eso", 0, ""),
        ("Alguna mancha pequeña en el techo del baño", 2, "mancha_bano"),
        ("Manchas oscuras en esquinas o detrás de los muebles", 5, "moho"),
        ("Pintura abombada, papel despegado o la pared mancha al tocarla", 7, "estructural"),
    ]),
    ("¿Cómo ventilas y dónde tiendes la ropa?", "habitos", [
        ("Abro las ventanas a diario y tiendo fuera", 0, ""),
        ("Ventilo casi todos los días", 1, ""),
        ("En invierno apenas abro las ventanas", 3, "poca_ventilacion"),
        ("Tiendo dentro de casa y casi nunca ventilo", 5, "tiende_dentro"),
    ]),
    ("¿Cómo es la vivienda?", "vivienda", [
        ("Piso en altura, soleado y con ventanas modernas", 0, ""),
        ("Un piso normal, ni especialmente bueno ni malo", 1, ""),
        ("Bajo o entresuelo, o con habitaciones que dan a un patio interior", 3, "planta_baja"),
        ("Casa antigua, planta baja o con semisótano", 4, "antigua"),
    ]),
    ("¿En qué zona vives?", "zona", [
        ("Interior seco: Madrid, Castilla, Aragón, Extremadura", 0, ""),
        ("Zona intermedia, o no sabría decirlo", 1, ""),
        ("Costa mediterránea o Andalucía", 2, "costa"),
        ("Norte atlántico: Galicia, Asturias, Cantabria, País Vasco", 3, "norte"),
    ]),
]

# (clave, limite_superior, titulo, color, texto)
TEST_NIVELES = [
    ("ok", 5, "Sin problema de humedad",
     "Por lo que cuentas, tu casa está dentro de lo normal. No necesitas comprar "
     "nada: con seguir ventilando como hasta ahora es suficiente."),
    ("leve", 10, "Humedad leve",
     "Hay alguna señal, pero de momento es cosa de hábitos más que de aparatos. "
     "Antes de gastar dinero, mide: un higrómetro cuesta unos diez euros y te dice "
     "si de verdad pasas del 60 %."),
    ("moderado", 18, "Humedad moderada",
     "Tu casa tiene un problema real de exceso de humedad. A este nivel ventilar "
     "ayuda pero ya no basta, sobre todo en invierno, y es cuando un "
     "deshumidificador compensa de verdad."),
    ("grave", 99, "Humedad alta",
     "Las señales que marcas apuntan a un exceso de humedad importante y mantenido "
     "en el tiempo. Aquí hay dos cosas que hacer: bajar la humedad del aire y "
     "averiguar de dónde sale el agua, porque si solo haces lo primero el problema "
     "vuelve."),
]

# Fuera de la escala de puntos: si la pared está dañada, el problema no es el aire.
TEST_ESTRUCTURAL = (
    "estructural", "Esto no parece condensación",
    "Has marcado que hay pintura abombada, papel despegado o una pared que mancha al "
    "tocarla. Eso ya no es vapor condensando en una superficie fría: es agua líquida "
    "metiéndose en el muro, por capilaridad desde el suelo, por una filtración desde "
    "fuera o por una fuga. Te lo digo claro porque cambia qué tienes que hacer.")


def test_opciones_html():
    """Las preguntas van en HTML de verdad para que Google las lea."""
    out = ""
    for i, (texto, clave, opciones) in enumerate(TEST_PREGUNTAS):
        ops = ""
        for j, (etiqueta, puntos, marca) in enumerate(opciones):
            ops += (
                '<label class="quiz-option">'
                '<input type="radio" name="q{i}" value="{p}" data-mark="{m}">'
                '<span>{t}</span></label>'
            ).format(i=i, p=puntos, m=esc(marca), t=esc(etiqueta)) + NL
        out += (
            '<fieldset class="quiz-q" data-q="{i}">'
            '<legend><span class="quiz-num">{n}</span> {q}</legend>'
            '<div class="quiz-options">{ops}</div>'
            '</fieldset>'
        ).format(i=i, n=i + 1, q=esc(texto), ops=ops) + NL
    return out


TEST_JS = """
(function () {
  var form = document.getElementById('quiz-form');
  if (!form) return;
  var box = document.getElementById('quiz-resultado');
  var btn = document.getElementById('quiz-enviar');
  var aviso = document.getElementById('quiz-aviso');
  var total = TEST_NUM_PREGUNTAS;
  var empezado = false;

  function track(nombre, params) {
    if (typeof window.gtag === 'function') { window.gtag('event', nombre, params || {}); }
  }

  form.addEventListener('change', function () {
    if (!empezado) { empezado = true; track('test_humedad_inicio'); }
    if (aviso) { aviso.textContent = ''; }
    var hechas = form.querySelectorAll('input[type=radio]:checked').length;
    btn.textContent = hechas < total
      ? 'Ver resultado (' + hechas + ' de ' + total + ')'
      : 'Ver resultado';
  });

  btn.addEventListener('click', function () {
    var puntos = 0, marcas = [], faltan = [];
    for (var i = 0; i < total; i++) {
      var sel = form.querySelector('input[name=q' + i + ']:checked');
      if (!sel) { faltan.push(i); continue; }
      puntos += parseInt(sel.value, 10);
      if (sel.getAttribute('data-mark')) { marcas.push(sel.getAttribute('data-mark')); }
    }
    if (faltan.length) {
      aviso.textContent = faltan.length === 1
        ? 'Te falta la pregunta ' + (faltan[0] + 1) + '.'
        : 'Te faltan ' + faltan.length + ' preguntas por responder.';
      var primera = form.querySelector('[data-q="' + faltan[0] + '"]');
      if (primera) { primera.scrollIntoView({ block: 'center' }); }
      return;
    }

    var nivel = NIVELES[NIVELES.length - 1];
    for (var k = 0; k < NIVELES.length; k++) {
      if (puntos <= NIVELES[k].max) { nivel = NIVELES[k]; break; }
    }
    // Una pared danada no se mide con la escala de humedad ambiental.
    if (marcas.indexOf('estructural') !== -1) { nivel = NIVEL_ESTRUCTURAL; }

    var notas = [];
    function tiene(m) { return marcas.indexOf(m) !== -1; }
    if (tiene('tiende_dentro')) {
      notas.push('Tender la ropa dentro suelta entre dos y tres litros de agua al aire por colada. ' +
        'Es, casi siempre, la mayor fuente de humedad de una casa, y lo que m\u00e1s r\u00e1pido se nota al cambiarlo.');
    }
    if (tiene('olor_fuerte') || tiene('moho')) {
      notas.push('El olor a cerrado y las manchas oscuras significan que ya hay moho creciendo en alg\u00fan ' +
        'sitio, aunque no lo veas entero. Limpiar la mancha sin bajar la humedad solo lo retrasa.');
    }
    if (tiene('condensa_mucho') && !tiene('estructural')) {
      notas.push('Que el agua llegue a caer al alf\u00e9izar casi siempre apunta a ventanas fr\u00edas, no a una ' +
        'pared mala: el aire caliente de dentro suelta el agua al tocar el cristal.');
    }
    if (tiene('norte')) {
      notas.push('En la cornisa cant\u00e1brica la humedad del aire exterior ya es alta de por s\u00ed, as\u00ed que ' +
        'ventilar ayuda menos que en el interior y el deshumidificador trabaja m\u00e1s horas.');
    }
    if (tiene('poca_ventilacion') && !tiene('tiende_dentro')) {
      notas.push('Diez minutos de ventana abierta en cruz, dos veces al d\u00eda, renuevan el aire sin enfriar ' +
        'las paredes. Enfr\u00eda el aire, que se recalienta en seguida, no los muros.');
    }

    var html = '';
    html += '<div class="quiz-result-head quiz-' + nivel.id + '">';
    html += '<p class="quiz-result-label">Resultado</p>';
    html += '<p class="quiz-result-title">' + nivel.titulo + '</p>';
    if (!nivel.sinPuntos) {
      html += '<p class="quiz-result-score">' + puntos + ' puntos sobre ' + MAX_PUNTOS + '</p>';
    }
    html += '</div>';
    html += '<div class="quiz-result-body">';
    html += '<p>' + nivel.texto + '</p>';
    for (var n = 0; n < notas.length; n++) { html += '<p>' + notas[n] + '</p>'; }
    html += nivel.recomendacion;
    html += '<div class="quiz-share"><p class="quiz-share-t">Comparte tu resultado</p><div class="quiz-share-btns">';
    var txt = encodeURIComponent('Mi casa ha salido con "' + nivel.titulo.toLowerCase() +
      '" en este test de humedad. \u00bfY la tuya?');
    var url = encodeURIComponent(PAGINA_URL);
    html += '<a class="quiz-share-b" rel="nofollow noopener" target="_blank" href="https://api.whatsapp.com/send?text=' + txt + '%20' + url + '">WhatsApp</a>';
    html += '<a class="quiz-share-b" rel="nofollow noopener" target="_blank" href="https://twitter.com/intent/tweet?text=' + txt + '&url=' + url + '">X</a>';
    html += '<a class="quiz-share-b" rel="nofollow noopener" target="_blank" href="https://pinterest.com/pin/create/button/?url=' + url + '&description=' + txt + '">Pinterest</a>';
    html += '<button type="button" class="quiz-share-b" id="quiz-copiar">Copiar enlace</button>';
    html += '</div></div>';
    html += '<p class="quiz-redo"><button type="button" id="quiz-repetir">Volver a hacer el test</button></p>';
    html += '</div>';

    box.innerHTML = html;
    box.hidden = false;
    box.scrollIntoView({ block: 'start' });
    track('test_humedad_resultado', { nivel: nivel.id, puntos: puntos });

    var copiar = document.getElementById('quiz-copiar');
    if (copiar) {
      copiar.addEventListener('click', function () {
        if (navigator.clipboard) {
          navigator.clipboard.writeText(PAGINA_URL).then(function () {
            copiar.textContent = 'Enlace copiado';
          }, function () { copiar.textContent = PAGINA_URL; });
        } else { copiar.textContent = PAGINA_URL; }
      });
    }
    var repetir = document.getElementById('quiz-repetir');
    if (repetir) {
      repetir.addEventListener('click', function () {
        form.reset();
        box.hidden = true;
        box.innerHTML = '';
        btn.textContent = 'Ver resultado';
        form.scrollIntoView({ block: 'start' });
      });
    }
  });
})();
"""


def test_recomendacion(nivel_id, products):
    """El bloque de producto de cada nivel. En 'ok' no se recomienda nada."""
    def ficha(pid, texto):
        p = product_by_id(products, pid)
        if not p:
            return ""
        return '<li><a href="{}">{}</a> — {}</li>'.format(
            product_href(p, depth=0), esc(p["name"]), texto)

    if nivel_id == "estructural":
        return ('<p>Lo que yo haría, por este orden:</p><ol>'
                '<li>Mirar qué hay justo al otro lado de esa pared: la calle, un baño, '
                'un patio, el piso de arriba. Casi siempre la pista está ahí.</li>'
                '<li>Fijarte en la forma de la mancha. Si sube desde el rodapié en una '
                'franja horizontal, suele ser capilaridad. Si baja desde el techo o sale '
                'de un punto concreto, suele ser una fuga.</li>'
                '<li>Que lo vea alguien en persona antes de gastar en aparatos. Si es una '
                'fuga, arreglarla cuesta mucho menos que convivir con ella.</li>'
                '<li>Si eres inquilino, avisar por escrito al propietario: los daños '
                'estructurales le corresponden a él.</li>'
                '</ol><p>Un deshumidificador te hará la casa más llevadera mientras tanto y '
                'frenará el moho, pero no va a parar el agua que entra. Para distinguir qué '
                'tienes, te sirve <a href="guias/condensacion-o-capilaridad-diagnostico.html">'
                'condensación o capilaridad: cómo distinguirlas</a>; y si ya hay manchas '
                'negras, <a href="guias/moho-armario-muebles-sin-obra.html">cómo tratar el '
                'moho</a>.</p>')

    if nivel_id == "ok":
        return ('<p class="quiz-nobuy">No te hace falta ningún aparato. Si alguna vez '
                'cambian las cosas, en la <a href="guias/senales-exceso-humedad.html">guía '
                'de señales de exceso de humedad</a> tienes qué vigilar.</p>')

    if nivel_id == "leve":
        return ('<p>Lo que haría yo en tu caso, por orden:</p><ol>'
                '<li>Comprar un higrómetro barato y mirar qué marca por la mañana.</li>'
                '<li>Ventilar diez minutos en cruz al levantarte.</li>'
                '<li>Si tiendes dentro, probar un mes a tender fuera o con extractor.</li>'
                '</ol><p>Si pasado un mes el higrómetro sigue por encima del 60 %, entonces '
                'sí toca mirar un <a href="deshumidificadores/index.html">deshumidificador</a>. '
                'Te lo explico en '
                '<a href="guias/que-capacidad-deshumidificador-litros-necesito.html">qué '
                'capacidad necesitas</a>.</p>')

    if nivel_id == "moderado":
        items = (ficha("dh-002", "compacto, suficiente para un dormitorio o un salón pequeño")
                 + ficha("dh-004", "para cubrir una vivienda de tamaño medio")
                 + ficha("dh-008", "con control desde el móvil, útil si quieres programarlo"))
        return ('<p>Para este nivel va bien un equipo de 12 a 16 litros al día. Estos tres '
                'son los que mejor encajan de los que he analizado:</p><ul class="quiz-prods">'
                + items + '</ul>'
                '<p>Antes de elegir, mira '
                '<a href="guias/que-capacidad-deshumidificador-litros-necesito.html">qué '
                'capacidad necesitas según los metros</a> y '
                '<a href="guias/donde-colocar-deshumidificador-casa.html">dónde colocarlo</a>.</p>')

    items = (ficha("dh-001", "20 L/día y Wi-Fi, para toda la vivienda")
             + ficha("dh-007", "20 L/día, la opción más ajustada de precio")
             + ficha("dh-009", "20 L/día con desagüe continuo, para no vaciar el depósito"))
    return ('<p>A este nivel se queda corto cualquier aparato pequeño: hace falta un equipo '
            'de 20 litros al día o más, y probablemente funcionando muchas horas las primeras '
            'semanas.</p><ul class="quiz-prods">' + items + '</ul>'
            '<p>Y en paralelo, lo importante: averiguar de dónde viene el agua. Te ayuda '
            '<a href="guias/condensacion-o-capilaridad-diagnostico.html">distinguir condensación '
            'de capilaridad</a>, que son problemas distintos con soluciones distintas.</p>')


def build_test_humedad(products):
    canonical = "test-humedad.html"
    titulo = "Test: ¿tu casa tiene un problema de humedad?"
    desc = ("Seis preguntas para saber si la humedad de tu casa es normal o se te está "
            "yendo de las manos, y qué hacer en cada caso. Sin registro y en un minuto.")

    niveles_js = []
    for nid, mx, tit, txt in TEST_NIVELES:
        niveles_js.append(
            '{{id:"{id}",max:{mx},titulo:{tit},texto:{txt},recomendacion:{rec}}}'.format(
                id=nid, mx=mx, tit=json.dumps(tit, ensure_ascii=False),
                txt=json.dumps(txt, ensure_ascii=False),
                rec=json.dumps(test_recomendacion(nid, products), ensure_ascii=False)))

    eid, etit, etxt = TEST_ESTRUCTURAL
    estructural_js = '{{id:"{id}",titulo:{tit},texto:{txt},recomendacion:{rec},sinPuntos:true}}'.format(
        id=eid, tit=json.dumps(etit, ensure_ascii=False),
        txt=json.dumps(etxt, ensure_ascii=False),
        rec=json.dumps(test_recomendacion(eid, products), ensure_ascii=False))

    max_puntos = sum(max(o[1] for o in q[2]) for q in TEST_PREGUNTAS)

    datos_js = (
        "var TEST_NUM_PREGUNTAS = {n};" + NL +
        "var MAX_PUNTOS = {mx};" + NL +
        "var PAGINA_URL = {url};" + NL +
        "var NIVELES = [{niv}];" + NL +
        "var NIVEL_ESTRUCTURAL = {est};"
    ).format(n=len(TEST_PREGUNTAS), mx=max_puntos,
             url=json.dumps(SITE_URL + "/" + canonical),
             niv=",".join(niveles_js), est=estructural_js)

    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question",
             "name": "¿Cuál es el nivel de humedad normal en una casa?",
             "acceptedAnswer": {"@type": "Answer", "text":
                "Entre el 40 % y el 60 % de humedad relativa. Por debajo del 40 % el aire "
                "reseca las vías respiratorias; por encima del 60 % empiezan a aparecer "
                "condensación, ácaros y moho."}},
            {"@type": "Question",
             "name": "¿Cómo sé si tengo humedad por condensación o por capilaridad?",
             "acceptedAnswer": {"@type": "Answer", "text":
                "La condensación aparece arriba: en cristales, en esquinas de techo y "
                "detrás de muebles pegados a paredes exteriores, y empeora en invierno. La "
                "capilaridad sube desde el suelo, deja una franja horizontal en la parte "
                "baja de la pared y no depende tanto de la estación."}},
            {"@type": "Question",
             "name": "¿Un deshumidificador quita el moho de las paredes?",
             "acceptedAnswer": {"@type": "Answer", "text":
                "No. Un deshumidificador baja la humedad del aire, que es lo que alimenta al "
                "moho, pero no limpia la mancha que ya existe. Hay que limpiar el moho aparte "
                "y después mantener la humedad entre el 40 % y el 60 % para que no vuelva."}},
        ],
    }

    content = """{head}
{nav}
<main id="main">
<article class="article">
  <div class="container article-content">
    <nav class="breadcrumb">
      <a href="index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Test de humedad</span>
    </nav>
    <header class="article-header">
      <h1>¿Tu casa tiene un problema de humedad?</h1>
    </header>
    <p class="article-lead">La humedad no avisa: se nota cuando ya hay una mancha en la
    esquina o la ropa del armario huele raro. Estas seis preguntas son las mismas que haría
    yo si me escribieras preguntándome qué comprar. Tardas un minuto, no hay que registrarse
    y a veces la respuesta es que no te hace falta nada.</p>

    <form id="quiz-form" class="quiz">
{preguntas}
      <p class="quiz-aviso" id="quiz-aviso" role="status"></p>
      <button type="button" class="btn btn-cta quiz-enviar" id="quiz-enviar">Ver resultado</button>
    </form>

    <div id="quiz-resultado" class="quiz-result" hidden></div>

    <div class="article-body">
      <h2>Qué significa cada señal</h2>
      <p>Las seis preguntas no son al azar: cada una mide algo distinto. Te cuento qué hay
      detrás, porque entenderlo vale más que el resultado del test.</p>

      <h3>El agua en los cristales</h3>
      <p>Es la señal más temprana y la más fácil de ver. El aire caliente de dentro de casa
      lleva vapor de agua; cuando toca un cristal frío lo suelta ahí, igual que un vaso de
      agua fría «suda» en verano. Que pase algún día de mucho frío es normal. Que pase casi
      todas las mañanas significa que hay demasiado vapor dando vueltas por la casa.</p>

      <h3>El olor a cerrado</h3>
      <p>Ese olor característico no lo produce la humedad en sí, lo producen los hongos
      creciendo en algún sitio: detrás de un armario, bajo un rodapié, dentro de un colchón.
      Si lo notas al volver a casa después de unas horas fuera, es que está extendido; dentro
      de casa dejas de percibirlo en pocos minutos.</p>

      <h3>Las manchas y la pintura</h3>
      <p>Aquí está la pregunta que más pesa en el resultado, porque distingue dos problemas
      muy distintos. Manchas oscuras en esquinas altas y detrás de muebles: condensación, se
      arregla bajando la humedad del aire. Pintura abombada, papel que se despega o pared que
      mancha los dedos: ahí hay agua líquida entrando por el muro, y eso no lo arregla ningún
      aparato.</p>

      <h3>Ventilar y tender</h3>
      <p>Una colada tendida dentro de casa suelta al aire entre dos y tres litros de agua.
      Cocinar y ducharse suman otro par de litros al día, y las personas que viven en la casa
      aportan alrededor de un litro cada una solo por respirar y sudar. Todo eso tiene que
      salir por algún sitio.</p>

      <h3>La vivienda y la zona</h3>
      <p>Una planta baja, un semisótano o una habitación que da a un patio interior parten con
      desventaja: menos sol, menos corriente de aire y paredes más frías. Y la zona importa
      más de lo que parece: en Galicia o Asturias el aire de la calle ya viene cargado, así
      que abrir la ventana no seca tanto como en Madrid.</p>

      <h2>El rango que deberías mantener</h2>
      <p>Entre el <strong>40 % y el 60 % de humedad relativa</strong>. Por debajo del 40 % el
      aire reseca la garganta y la piel. Por encima del 60 % empiezan a vivir cómodos los
      ácaros, y pasado el 70 % ya crece moho en cualquier superficie fría. Un higrómetro de
      diez euros te lo dice, y es la compra más rentable que puedes hacer antes de gastarte
      nada en un aparato.</p>

      <h2>Preguntas frecuentes</h2>
      <h3>¿El test guarda mis respuestas?</h3>
      <p>No. Todo el cálculo se hace en tu navegador y no se envía nada a ningún sitio. Si
      cierras la página, no queda nada.</p>

      <h3>¿Un deshumidificador quita el moho que ya tengo?</h3>
      <p>No. Baja la humedad del aire, que es lo que alimenta al moho, pero la mancha que ya
      está en la pared hay que limpiarla aparte. Lo que evita es que vuelva a salir.</p>

      <h3>¿Y si me sale «sin problema» pero yo noto humedad?</h3>
      <p>Hazle caso a lo que ves antes que al test. Seis preguntas no cubren todos los casos:
      una fuga lenta en una tubería o una filtración desde el piso de arriba pueden dar pocos
      síntomas de los que pregunto aquí y ser un problema serio igualmente.</p>
    </div>

    {relacionadas}
  </div>
</article>
</main>
{footer}
<script>{datos}{js}</script>
{scripts}""".format(
        head=head_html(titulo, desc, depth=0, canonical=canonical,
                       full_title="Test: ¿tu casa tiene problema de humedad?",
                       extra_head=jsonld(faq_ld, migas_ld([
                           ("Inicio", ""), ("Test de humedad", canonical)]))),
        nav=nav_html("", depth=0),
        preguntas=test_opciones_html(),
        relacionadas="",
        footer=footer_html(depth=0),
        datos=datos_js,
        js=TEST_JS,
        scripts=scripts_html(depth=0),
    )

    escribir(os.path.join(BASE, "test-humedad.html"), content)
    print("  - test-humedad.html")


def build_sitemap(products, guias):
    today = datetime.now().strftime("%Y-%m-%d")
    urls = [("", today, "weekly", "1.0")]
    urls.append(("guias/", today, "weekly", "0.9"))
    for g in guias:
        urls.append(("guias/{}.html".format(g["slug"]), g.get("fecha", today), "monthly", "0.8"))
    for key in CATEGORY_ORDER:
        cfg = CATEGORY_CONFIG[key]
        cat_prods = [x for x in products if x["category"] == key]
        fechas = [x.get("precio_fecha") for x in cat_prods if not vacio(x.get("precio_fecha"))]
        urls.append(("{}/".format(cfg["slug"]), max(fechas) if fechas else today, "weekly", "0.9"))
        for p in cat_prods:
            urls.append(("{}/{}.html".format(cfg["slug"], product_slug(p)),
                         p.get("precio_fecha") or today, "weekly", "0.8"))
    urls.append(("comparador.html", today, "weekly", "0.6"))
    urls.append(("guia-deshumidificadores.html", today, "monthly", "0.7"))
    urls.append(("guia-calefactores.html", today, "monthly", "0.7"))
    urls.append(("guia-purificadores.html", today, "monthly", "0.7"))
    urls.append(("test-humedad.html", today, "monthly", "0.8"))
    urls.append(("sobre-nosotros.html", today, "yearly", "0.5"))
    for f in ("aviso-afiliados.html", "privacidad.html", "aviso-legal.html"):
        urls.append((f, today, "yearly", "0.3"))

    body = ""
    for loc, lastmod, freq, prio in urls:
        body += """  <url>
    <loc>{site}/{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>
""".format(site=SITE_URL, loc=loc, lastmod=lastmod, freq=freq, prio=prio)

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}</urlset>
""".format(body=body)

    with open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print("  - sitemap.xml ({} URLs)".format(len(urls)))


# ── Main ────────────────────────────────────────────────────

def main():
    print("Generando sitio elclimadecasa.com...")
    products = load_products()
    guias = load_guias()
    print("  {} productos y {} guías cargadas".format(len(products), len(guias)))

    rebuild_db_js(products)

    for p in products:
        build_ficha(p, products, guias)

    for cat_key in CATEGORY_CONFIG:
        build_category(products, cat_key, guias)

    build_comparador()
    build_guide_deshumidificadores()
    build_guide_calefactores()
    build_guide_purificadores()
    build_legal_pages()

    for g in guias:
        build_guia(g, products, guias)
    build_guias_index(guias)

    build_home(products, guias)
    build_sobre_nosotros()
    build_test_humedad(products)
    build_sitemap(products, guias)

    print("\nBuild completo: {} fichas, {} categorías, {} guías, comparador, portada y legales".format(
        len(products), len(CATEGORY_CONFIG), len(guias)))
    print("   Cache-buster: ?v={}".format(VER))


if __name__ == "__main__":
    main()
