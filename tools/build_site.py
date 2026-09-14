"""
build_site.py — Genera las páginas HTML desde datos/productos.json
Ejecutar: python tools/build_site.py
"""
import json, os, sys, html as htmlmod
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = datetime.now().strftime("%Y%m%d%H%M")

def esc(s):
    return htmlmod.escape(str(s)) if s is not None else ""

def load_products():
    with open(os.path.join(BASE, "datos", "productos.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def format_price(p):
    if p is None: return "—"
    return f"{p:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def bool_html(v):
    if v: return '<span class="spec-bool-yes">Sí</span>'
    return '<span class="spec-bool-no">No</span>'

def product_img(p, idx=0, cls="", depth=0):
    prefix = "../" * depth
    imgs = p.get("images", [])
    if imgs and idx < len(imgs):
        src = prefix + imgs[idx]
        alt = esc(p["name"])
        c = f' class="{cls}"' if cls else ""
        return f'<img src="{src}" alt="{alt}" loading="lazy" width="400" height="400"{c}>'
    icon = CATEGORY_CONFIG.get(p.get("category", ""), {}).get("icon", "🌡️")
    return f'<div class="img-placeholder">{icon}</div>'

def stars_html(rating):
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
    "cal-001": "rowenta-instant-comfort-aqua-so6510",
    "cal-002": "cecotec-ready-warm-10100-smart-ceramic",
    "cal-003": "pro-breeze-mini-ceramico-2000w",
    "cal-004": "delonghi-trrs-1225-radia-s",
    "cal-005": "orbegozo-rre-1310",
    "cal-006": "cecotec-ready-warm-5750-space-360",
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

SUBCATEGORIES_CAL = [
    ("ceramico", "Cerámicos"),
    ("radiador-aceite", "Radiadores de aceite"),
    ("panel", "Paneles / Convectores"),
    ("halogeno-cuarzo", "Halógenas / Cuarzo"),
]

CATEGORY_CONFIG = {
    "deshumidificadores": {
        "title": "Deshumidificadores",
        "icon": "💧",
        "slug": "deshumidificadores",
        "nav_key": "deshumidificadores",
        "spec_fields": SPEC_FIELDS_DH,
        "compare_specs": COMPARE_SPECS_DH,
        "guide_slug": "guia-deshumidificadores",
        "guide_title": "Guía de compra de deshumidificadores",
        "meta_desc": "Los mejores deshumidificadores del mercado. Compara modelos por capacidad, precio, ruido y más.",
        "category_desc": "Compara los mejores deshumidificadores del mercado. Filtros por precio, capacidad y nivel de ruido para encontrar el modelo perfecto para tu hogar.",
        "subcategories": [],
        "chips": lambda p: [
            f'{p.get("capacidad_litros_dia","—")} L/día',
            f'{p.get("cobertura_m2","—")} m²',
            f'{p.get("ruido_db","—")} dB',
        ],
    },
    "calefactores": {
        "title": "Calefactores",
        "icon": "🔥",
        "slug": "calefactores",
        "nav_key": "calefactores",
        "spec_fields": SPEC_FIELDS_CAL,
        "compare_specs": COMPARE_SPECS_CAL,
        "guide_slug": "guia-calefactores",
        "guide_title": "Guía de compra de calefactores",
        "meta_desc": "Los mejores calefactores para tu hogar: cerámicos, radiadores de aceite, paneles y estufas de cuarzo. Compara modelos y elige el tuyo.",
        "category_desc": "Compara los mejores calefactores del mercado. Filtros por precio, potencia y tipo para encontrar el calefactor perfecto para tu hogar.",
        "subcategories": SUBCATEGORIES_CAL,
        "chips": lambda p: [
            p.get("tipo_calefactor", "—"),
            f'{p.get("potencia_w","—")} W',
            f'{p.get("cobertura_m2","—")} m²',
        ],
    },
}

# ── Shared HTML builders ────────────────────────────────────

def nav_html(active="", depth=0):
    prefix = "../" * depth
    links = [
        ("index.html", "Inicio", "inicio"),
        ("deshumidificadores/index.html", "Deshumidificadores", "deshumidificadores"),
        ("calefactores/index.html", "Calefactores", "calefactores"),
        ("#", "Aires Acondicionados", "aires"),
        ("#", "Ventiladores", "ventiladores"),
        ("#", "Purificadores", "purificadores"),
        ("comparador.html", "Comparador", "comparador"),
    ]
    items = ""
    mob = ""
    for href, label, key in links:
        h = prefix + href if href != "#" else "#"
        cls = ' class="active"' if key == active else ""
        if key == "comparador":
            cls = ' class="nav-cta"'
        items += f'<li><a href="{h}"{cls}>{label}</a></li>\n'
        mob += f'<a href="{h}">{label}</a>\n'

    return f'''<nav class="nav" aria-label="Navegación principal">
  <div class="nav-inner">
    <a href="{prefix}index.html" class="nav-logo">
      <svg viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="14" cy="14" r="13" stroke="#2563eb" stroke-width="2"/><path d="M14 7v10M11 14l3 3 3-3" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="14" cy="21" r="2" fill="#2563eb"/></svg>
      El Clima <span>de Casa</span>
    </a>
    <ul class="nav-links">{items}</ul>
    <button class="nav-toggle" aria-label="Abrir menú"><span></span><span></span><span></span></button>
  </div>
</nav>
<div class="nav-mobile" aria-hidden="true">{mob}</div>'''

def footer_html(depth=0):
    prefix = "../" * depth
    return f'''<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h4>El Clima de Casa</h4>
        <p style="font-size:.88rem">Guías independientes de productos de climatización para tu hogar.</p>
      </div>
      <div>
        <h4>Categorías</h4>
        <ul class="footer-links">
          <li><a href="{prefix}deshumidificadores/index.html">Deshumidificadores</a></li>
          <li><a href="{prefix}calefactores/index.html">Calefactores</a></li>
          <li><a href="#">Aires Acondicionados</a></li>
          <li><a href="#">Ventiladores</a></li>
          <li><a href="#">Purificadores</a></li>
        </ul>
      </div>
      <div>
        <h4>Recursos</h4>
        <ul class="footer-links">
          <li><a href="{prefix}comparador.html">Comparador</a></li>
          <li><a href="{prefix}guia-deshumidificadores.html">Guía deshumidificadores</a></li>
          <li><a href="{prefix}guia-calefactores.html">Guía calefactores</a></li>
        </ul>
      </div>
      <div>
        <h4>Legal</h4>
        <ul class="footer-links">
          <li><a href="{prefix}aviso-afiliados.html">Aviso de afiliación</a></li>
          <li><a href="{prefix}privacidad.html">Política de privacidad</a></li>
          <li><a href="{prefix}aviso-legal.html">Aviso legal</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="affiliate-notice">
        <strong>Aviso de afiliación:</strong> elclimadecasa.com participa en el Programa de Afiliados de Amazon EU. Esto significa que cuando compras a través de nuestros enlaces, podemos recibir una pequeña comisión sin coste adicional para ti. Amazon y el logotipo de Amazon son marcas registradas de Amazon.com, Inc. o sus afiliados.
      </div>
      <p>&copy; 2026 El Clima de Casa. Todos los derechos reservados.</p>
    </div>
  </div>
</footer>'''

def head_html(title, desc, depth=0):
    prefix = "../" * depth
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} — El Clima de Casa</title>
  <meta name="description" content="{esc(desc)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
  <link rel="stylesheet" href="{prefix}styles.css?v={VER}">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌡️</text></svg>">
  <meta name="p:domain_verify" content="447a4061b72017eac6ae92ec67a035cb"/>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-DP24YW5N8Z"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-DP24YW5N8Z');
  </script>
</head>
<body>
<a href="#main" class="skip-link">Ir al contenido</a>'''

def scripts_html(depth=0):
    prefix = "../" * depth
    return f'''<script defer src="{prefix}lib/db.js?v={VER}"></script>
<script defer src="{prefix}main.js?v={VER}"></script>
</body>
</html>'''

# ── Spec table ──────────────────────────────────────────────

def spec_table_html(p):
    cat = p.get("category", "deshumidificadores")
    fields = CATEGORY_CONFIG.get(cat, {}).get("spec_fields", SPEC_FIELDS_DH)
    rows = ""
    for group_name, field_list in fields:
        rows += f'<tr class="spec-group-header"><td colspan="2">{esc(group_name)}</td></tr>\n'
        for label, key, unit in field_list:
            val = p.get(key)
            if unit is None:
                cell = bool_html(val)
            elif val is None or val == "":
                cell = "—"
            else:
                cell = f"{esc(val)}{unit}"
            rows += f'<tr><th>{esc(label)}</th><td>{cell}</td></tr>\n'
    extras = p.get("specs_extra", {})
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
    return SLUG_MAP.get(p["id"], p["id"])

# ── Product page (ficha) ───────────────────────────────────

def build_ficha(p, all_products):
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

    content = f'''{head_html(p["name"], p.get("description",""), depth=1)}
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
        {product_img(p, 0, "ficha-main-img", depth=1)}
      </div>
      <div class="ficha-info">
        <div class="ficha-brand">{esc(p["marca"])}</div>
        <h1>{esc(p["name"])}</h1>
        <div>
          <span class="stars">{stars_html(p.get("valoracion_media",0))}</span>
          <span class="stars-count">({p.get("resenas_cantidad",0)} valoraciones en Amazon)</span>
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

    <section class="radar-section reveal">
      <h2>Valoración del editor</h2>
      <div class="radar-wrap">
        <div data-ficha-radar="{p["id"]}"></div>
        <p class="radar-note">Puntuaciones del equipo editorial (0-10). No representan una medida oficial.</p>
      </div>
    </section>

    <section class="spec-table-wrap reveal">
      {spec_table_html(p)}
    </section>

    <section class="editorial-section reveal">
      <h2>Nuestro análisis</h2>
      <div class="editorial-body">{p.get("cuerpo_editorial","")}</div>
    </section>

    {pros_cons_html(p)}

    <a href="{esc(p["affiliate_url"])}" class="btn btn-amazon btn-lg btn-block" target="_blank" rel="nofollow noopener sponsored" style="margin-bottom:2rem">Ver en Amazon</a>

    <section class="reviews-section reveal">
      <h3>Lo que dicen los compradores</h3>
      <p>{esc(p.get("resenas_resumen",""))}</p>
    </section>

    {similar_html}

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
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Ficha: {cfg['slug']}/{slug}.html")

# ── Category index page ────────────────────────────────────

def build_category(products, cat_key):
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

        chips = cfg["chips"](p)
        chips_html = "".join(f'<span class="product-card-chip">{esc(c)}</span>' for c in chips)

        cards += f'''<article class="product-card reveal" data-product-id="{p["id"]}">
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
      <span class="stars">{stars_html(p.get("valoracion_media",0))} <span class="stars-count">({p.get("resenas_cantidad",0)})</span></span>
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

    content = f'''{head_html(cfg["title"], cfg["meta_desc"], depth=1)}
{nav_html(cfg["nav_key"], depth=1)}
<main id="main">
<section class="page-header">
  <div class="container">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>{esc(cfg["title"])}</span>
    </nav>
    <h1>{esc(cfg["title"])}</h1>
    <p style="color:var(--text-muted);max-width:600px">{esc(cfg["category_desc"])}</p>
  </div>
</section>

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
</main>
{footer_html(depth=1)}
{scripts_html(depth=1)}'''

    outdir = os.path.join(BASE, cfg["slug"])
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "index.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Categoría: {cfg['slug']}/index.html")

# ── Comparador ──────────────────────────────────────────────

def build_comparador():
    content = f'''{head_html("Comparador de productos", "Compara hasta 3 productos lado a lado: especificaciones, puntuaciones y precios.")}
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
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ comparador.html")

# ── Guide: deshumidificadores ──────────────────────────────

def build_guide_deshumidificadores():
    content = f'''{head_html("Cómo elegir el mejor deshumidificador para tu hogar", "Guía completa para elegir deshumidificador: capacidad, ruido, funciones, precio y más. Todo lo que necesitas saber antes de comprar.")}
{nav_html("")}
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
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ guia-deshumidificadores.html")

# ── Guide: calefactores ────────────────────────────────────

def build_guide_calefactores():
    content = f'''{head_html("Cómo elegir el mejor calefactor para tu hogar", "Guía completa para elegir calefactor: cerámicos, radiadores de aceite, paneles y estufas de cuarzo. Todo lo que necesitas saber antes de comprar.")}
{nav_html("")}
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

    <h3>🔥 Calefactores cerámicos</h3>
    <p>Calientan mediante una resistencia cerámica y un ventilador que distribuye el aire caliente. Son compactos, ligeros y calientan rápido, pero hacen algo de ruido por el ventilador. Ideales para calentar habitaciones pequeñas-medianas en minutos.</p>
    <p><strong>Mejor para:</strong> baños (con IP21), despachos, dormitorios, calor rápido.</p>

    <h3>🛢️ Radiadores de aceite</h3>
    <p>Calientan aceite térmico interno que irradia calor de forma constante y silenciosa. Tardan más en alcanzar temperatura pero mantienen el calor incluso después de apagados. Completamente silenciosos.</p>
    <p><strong>Mejor para:</strong> dormitorios, despachos, uso prolongado, quien no soporta el ruido.</p>

    <h3>📐 Paneles y convectores</h3>
    <p>Calientan el aire por convección natural (o forzada con turbo). Diseño slim que permite montaje en pared. Modernos, algunos con panel de cristal decorativo.</p>
    <p><strong>Mejor para:</strong> salones, pasillos, montaje en pared, quien valora el diseño.</p>

    <h3>☀️ Estufas halógenas / de cuarzo</h3>
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
      <li><strong>Para el baño:</strong> <a href="calefactores/rowenta-instant-comfort-aqua-so6510.html" style="color:var(--accent)">Rowenta Aqua SO6510</a> — 69,99 € (IP21)</li>
      <li><strong>Más smart:</strong> <a href="calefactores/cecotec-ready-warm-10100-smart-ceramic.html" style="color:var(--accent)">Cecotec Ready Warm 10100</a> — 59,99 € (Wi-Fi)</li>
      <li><strong>Mejor precio:</strong> <a href="calefactores/pro-breeze-mini-ceramico-2000w.html" style="color:var(--accent)">Pro Breeze Mini 2000W</a> — 44,99 €</li>
    </ul>

    <h3>Radiadores de aceite</h3>
    <ul>
      <li><strong>Premium silencioso:</strong> <a href="calefactores/delonghi-trrs-1225-radia-s.html" style="color:var(--accent)">De'Longhi TRRS 1225 Radia S</a> — 139,99 €</li>
      <li><strong>Más económico:</strong> <a href="calefactores/orbegozo-rre-1310.html" style="color:var(--accent)">Orbegozo RRE 1310</a> — 54,99 €</li>
    </ul>

    <h3>Paneles</h3>
    <ul>
      <li><strong>Con turbo:</strong> <a href="calefactores/rowenta-vectissimo-ii-co3030.html" style="color:var(--accent)">Rowenta Vectissimo II CO3030</a> — 69,99 €</li>
      <li><strong>Diseño premium:</strong> <a href="calefactores/cecotec-ready-warm-6650-crystal-connection.html" style="color:var(--accent)">Cecotec Crystal Connection</a> — 89,99 €</li>
    </ul>

    <h3>Cuarzo</h3>
    <ul>
      <li><strong>La más barata:</strong> <a href="calefactores/orbegozo-bp-5003.html" style="color:var(--accent)">Orbegozo BP 5003</a> — 24,99 €</li>
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
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ guia-calefactores.html")

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
    <p>Este sitio web no recopila datos personales directamente. Utilizamos Google Analytics para analíticas de tráfico y Google Fonts para la tipografía. Cuando haces clic en un enlace de afiliado, Amazon recopila datos según su propia política de privacidad.</p>
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
        content = f'''{head_html(title, f"{title} de elclimadecasa.com")}
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
        with open(outpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {filename}")

# ── DB.js ───────────────────────────────────────────────────

def rebuild_db_js(products):
    import json as j
    db_data = {
        "productos": products,
        "nichos": ["deshumidificadores", "calefactores"],
        "categorias": [
            {"id": "deshumidificadores", "nombre": "Deshumidificadores", "slug": "deshumidificadores", "activa": True},
            {"id": "calefactores", "nombre": "Calefactores", "slug": "calefactores", "activa": True},
            {"id": "aires-acondicionados", "nombre": "Aires Acondicionados", "slug": "aires-acondicionados", "activa": False},
            {"id": "ventiladores", "nombre": "Ventiladores", "slug": "ventiladores", "activa": False},
            {"id": "purificadores", "nombre": "Purificadores de Aire", "slug": "purificadores", "activa": False},
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
        },
        "updated": datetime.now().strftime("%Y-%m-%d")
    }
    js = '(function(){"use strict";window.__DB__=' + j.dumps(db_data, ensure_ascii=False) + ';})();'
    outpath = os.path.join(BASE, "lib", "db.js")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  ✅ lib/db.js (actualizado)")

# ── Main ────────────────────────────────────────────────────

def main():
    print("🏗️  Generando sitio elclimadecasa.com...")
    products = load_products()
    print(f"  📦 {len(products)} productos cargados")

    rebuild_db_js(products)

    for p in products:
        build_ficha(p, products)

    for cat_key in CATEGORY_CONFIG:
        build_category(products, cat_key)

    build_comparador()
    build_guide_deshumidificadores()
    build_guide_calefactores()
    build_legal_pages()

    dh_count = len([p for p in products if p["category"] == "deshumidificadores"])
    cal_count = len([p for p in products if p["category"] == "calefactores"])
    print(f"\n✅ Build completo. {dh_count} deshumidificadores + {cal_count} calefactores")
    print(f"   {dh_count + cal_count} fichas + 2 categorías + comparador + 2 guías + 3 legales")
    print(f"   Cache-buster: ?v={VER}")

if __name__ == "__main__":
    main()
