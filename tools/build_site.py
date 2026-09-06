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
    return '<div class="img-placeholder">💧</div>'

def stars_html(rating):
    full = int(rating)
    half = (rating - full) >= 0.25
    s = "★" * full
    if half: s += "½"
    return s

def nav_html(active="", depth=0):
    prefix = "../" * depth
    links = [
        ("index.html", "Inicio", "inicio"),
        ("deshumidificadores/index.html", "Deshumidificadores", "deshumidificadores"),
        ("#", "Aires Acondicionados", "aires"),
        ("#", "Calefactores", "calefactores"),
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
          <li><a href="#">Aires Acondicionados</a></li>
          <li><a href="#">Calefactores</a></li>
          <li><a href="#">Ventiladores</a></li>
          <li><a href="#">Purificadores</a></li>
        </ul>
      </div>
      <div>
        <h4>Recursos</h4>
        <ul class="footer-links">
          <li><a href="{prefix}comparador.html">Comparador</a></li>
          <li><a href="{prefix}guia-deshumidificadores.html">Guía de compra</a></li>
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

SPEC_FIELDS = [
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

def spec_table_html(p):
    rows = ""
    for group_name, fields in SPEC_FIELDS:
        rows += f'<tr class="spec-group-header"><td colspan="2">{esc(group_name)}</td></tr>\n'
        for label, key, unit in fields:
            val = p.get(key)
            if unit is None:
                cell = bool_html(val)
            elif val is None:
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

SLUG_MAP = {
    "dh-001": "pro-breeze-omnidry-20l",
    "dh-002": "pro-breeze-compacto-12l",
    "dh-003": "delonghi-ariadry-dexd216rf",
}

def product_slug(p):
    return SLUG_MAP.get(p["id"], p["id"])

def build_ficha(p, all_products):
    slug = product_slug(p)
    price = p.get("discountedPrice") or p.get("retailPrice")
    has_offer = p.get("discountedPrice") and p.get("retailPrice") and p["discountedPrice"] < p["retailPrice"]
    price_html_str = format_price(price)
    original = format_price(p["retailPrice"]) if has_offer else ""

    offer_badge = ""
    if has_offer:
        pct = round(100 * (1 - p["discountedPrice"] / p["retailPrice"]))
        offer_badge = f'<span class="badge badge-offer">-{pct}%</span>'

    similar = [x for x in all_products if x["id"] != p["id"] and x["category"] == p["category"]]

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
{nav_html("deshumidificadores", depth=1)}
<main id="main">
<section class="ficha">
  <div class="container">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <a href="index.html">Deshumidificadores</a> <span class="breadcrumb-sep">/</span>
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

    outpath = os.path.join(BASE, "deshumidificadores", f"{slug}.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Ficha: deshumidificadores/{slug}.html")

def build_category(products):
    dh = [p for p in products if p["category"] == "deshumidificadores"]
    cards = ""
    for p in dh:
        slug = product_slug(p)
        price = p.get("discountedPrice") or p.get("retailPrice")
        has_offer = p.get("discountedPrice") and p.get("retailPrice") and p["discountedPrice"] < p["retailPrice"]
        badge = ""
        if has_offer:
            pct = round(100 * (1 - p["discountedPrice"] / p["retailPrice"]))
            badge = f'<span class="badge badge-offer">-{pct}%</span>'

        cards += f'''<article class="product-card reveal" data-product-id="{p["id"]}">
  <div class="product-card-img">
    {badge}
    {product_img(p, depth=1)}
  </div>
  <div class="product-card-body">
    <div class="product-card-brand">{esc(p["marca"])}</div>
    <h3 class="product-card-name"><a href="{slug}.html">{esc(p["name"])}</a></h3>
    <div class="product-card-highlight">
      <span class="product-card-chip">{p.get("capacidad_litros_dia","—")} L/día</span>
      <span class="product-card-chip">{p.get("cobertura_m2","—")} m²</span>
      <span class="product-card-chip">{p.get("ruido_db","—")} dB</span>
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

    content = f'''{head_html("Deshumidificadores", "Los mejores deshumidificadores del mercado. Compara modelos por capacidad, precio, ruido y más.", depth=1)}
{nav_html("deshumidificadores", depth=1)}
<main id="main">
<section class="page-header">
  <div class="container">
    <nav class="breadcrumb">
      <a href="../index.html">Inicio</a> <span class="breadcrumb-sep">/</span>
      <span>Deshumidificadores</span>
    </nav>
    <h1>Deshumidificadores</h1>
    <p style="color:var(--text-muted);max-width:600px">Compara los mejores deshumidificadores del mercado. Filtros por precio, capacidad y nivel de ruido para encontrar el modelo perfecto para tu hogar.</p>
  </div>
</section>

<section style="padding:0 0 3rem">
  <div class="container">
    <div class="filters-bar">
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
      <span class="results-count">{len(dh)} productos</span>
    </div>

    <div class="product-grid" data-category-grid>
      {cards}
    </div>

    <div style="text-align:center;margin-top:2rem">
      <a href="../comparador.html" class="btn btn-primary">Comparar productos</a>
      <a href="../guia-deshumidificadores.html" class="btn btn-outline" style="margin-left:.5rem">Guía de compra</a>
    </div>
  </div>
</section>
</main>
{footer_html(depth=1)}
{scripts_html(depth=1)}'''

    outpath = os.path.join(BASE, "deshumidificadores", "index.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Categoría: deshumidificadores/index.html")

def build_comparador():
    content = f'''{head_html("Comparador de deshumidificadores", "Compara hasta 3 deshumidificadores lado a lado: especificaciones, puntuaciones y precios.")}
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

def build_guide():
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
    <p style="color:var(--text-muted);margin-bottom:2rem">Actualizado: agosto 2026 · Lectura: 8 minutos</p>

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
    <p>El nivel ideal de humedad interior está entre el 40% y el 55%. Un buen deshumidificador te permite mantener ese rango automáticamente.</p>

    <h2 id="capacidad">Capacidad de extracción: cuántos litros necesitas</h2>
    <p>La capacidad se mide en litros por día (L/día) y es el dato más importante. Pero cuidado: los fabricantes miden a 30°C y 80% de humedad relativa — condiciones que rara vez se dan en un hogar español medio. En la práctica, espera un rendimiento un 30-40% menor que el anunciado.</p>
    <ul>
      <li><strong>Hasta 10 L/día:</strong> baños, vestidores, habitaciones pequeñas (hasta 15 m²)</li>
      <li><strong>12-16 L/día:</strong> dormitorios, despachos, cocinas (15-30 m²)</li>
      <li><strong>20+ L/día:</strong> salones, sótanos, pisos completos (30-50 m²)</li>
      <li><strong>30+ L/día:</strong> grandes estancias, locales comerciales, garajes (50+ m²)</li>
    </ul>
    <p><strong>Consejo:</strong> es mejor pasarse un poco que quedarse corto. Un deshumidificador con más capacidad de la necesaria simplemente trabajará menos tiempo y consumirá menos, no más.</p>

    <div class="guide-product-insert">
      <img src="assets/img/dh-001-1.webp" alt="Pro Breeze OmniDry 20L" loading="lazy" width="80" height="80" style="width:80px;height:80px;border-radius:8px;flex:none;object-fit:contain">
      <div>
        <h4>Nuestra recomendación para 20 L/día</h4>
        <p>El Pro Breeze OmniDry 20L ofrece la mejor relación calidad-precio con Wi-Fi y 4L de depósito.</p>
        <a href="deshumidificadores/pro-breeze-omnidry-20l.html" class="btn btn-primary btn-sm">Ver ficha completa</a>
      </div>
    </div>

    <h2 id="ruido">Nivel de ruido: dB que importan</h2>
    <p>El ruido es el factor que más gente subestima al comprar. Un deshumidificador puede funcionar durante horas, y si suena demasiado, acabarás apagándolo — lo que anula su utilidad.</p>
    <ul>
      <li><strong>Menos de 40 dB:</strong> silencioso, apto para dormitorios</li>
      <li><strong>40-45 dB:</strong> moderado, equivale a una conversación en voz baja</li>
      <li><strong>Más de 45 dB:</strong> perceptible, mejor para estancias donde no duermes</li>
    </ul>
    <p>Si el silencio es tu prioridad absoluta, busca modelos con "modo nocturno" o "modo silencioso" que reduzcan activamente el compresor.</p>

    <h2 id="funciones">Funciones que marcan la diferencia</h2>
    <p>Más allá de la capacidad y el ruido, estas funciones pueden hacer tu día a día mucho más cómodo:</p>
    <ul>
      <li><strong>Higrostato automático:</strong> mide la humedad y se enciende/apaga solo. Imprescindible.</li>
      <li><strong>Temporizador:</strong> programar encendido/apagado ahorra electricidad.</li>
      <li><strong>Modo secado de ropa:</strong> ventilador a máxima potencia dirigido. Muy útil en invierno.</li>
      <li><strong>Desagüe continuo:</strong> manguera que conectas al desagüe más cercano. Olvídate de vaciar el depósito.</li>
      <li><strong>Control por app/Wi-Fi:</strong> cómodo pero no esencial. Útil si lo dejas encendido al salir de casa.</li>
      <li><strong>Filtro lavable:</strong> ahorra en recambios a largo plazo.</li>
    </ul>

    <h2 id="precio">¿Cuánto debería costar?</h2>
    <p>Los precios en Amazon España para deshumidificadores de calidad razonable van de los 130 € a los 400 €:</p>
    <ul>
      <li><strong>130-180 €:</strong> modelos básicos de 10-12 L/día. Funcionales pero limitados.</li>
      <li><strong>180-250 €:</strong> el <em>sweet spot</em>. Modelos de 20 L/día con buenas funciones.</li>
      <li><strong>250-400 €:</strong> gama alta. Más silenciosos, mejor cobertura, marcas premium.</li>
    </ul>
    <p>Nuestra experiencia: los modelos entre 180 € y 260 € ofrecen el mejor equilibrio. Por debajo, sacrificas capacidad o fiabilidad; por encima, pagas prima de marca.</p>

    <h2 id="recomendaciones">Nuestras recomendaciones</h2>
    <p>Después de analizar decenas de modelos, estos son los tres que recomendamos según diferentes perfiles:</p>
    <ul>
      <li><strong>Mejor relación calidad-precio:</strong> <a href="deshumidificadores/pro-breeze-20l.html" style="color:var(--accent)">Pro Breeze 20L</a> — 189,99 €</li>
      <li><strong>Más eficiente y con Wi-Fi:</strong> <a href="deshumidificadores/inventor-eva-ii-pro.html" style="color:var(--accent)">Inventor EVA II Pro</a> — 249,99 €</li>
      <li><strong>Más silencioso:</strong> <a href="deshumidificadores/delonghi-dex216f.html" style="color:var(--accent)">De'Longhi DEX216F</a> — 269,99 €</li>
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

def build_legal_pages():
    pages = {
        "aviso-afiliados.html": ("Aviso de afiliación", '''
    <h1>Aviso de afiliación</h1>
    <p>elclimadecasa.com participa en el <strong>Programa de Afiliados de Amazon EU</strong>, un programa de publicidad para afiliados diseñado para ofrecer a sitios web un modo de obtener comisiones por publicidad, publicitando e incluyendo enlaces a Amazon.es.</p>

    <h2>¿Qué significa esto para ti?</h2>
    <p>Cuando haces clic en uno de nuestros enlaces a Amazon y realizas una compra, nosotros recibimos una pequeña comisión. <strong>Esto no tiene ningún coste adicional para ti</strong> — el precio que pagas es exactamente el mismo que si hubieras llegado a Amazon directamente.</p>

    <h2>¿Afecta esto a nuestras recomendaciones?</h2>
    <p>No. Nuestras recomendaciones se basan únicamente en el análisis objetivo de las especificaciones, las valoraciones de los usuarios y nuestra propia evaluación editorial. Recomendamos productos que consideramos genuinamente buenos, independientemente de la comisión.</p>
    <p>Los ingresos de afiliación nos permiten mantener este sitio web, dedicar tiempo al análisis de productos y seguir ofreciendo contenido gratuito y de calidad.</p>

    <h2>Sobre los precios</h2>
    <p>Los precios que mostramos son <strong>orientativos</strong> y corresponden al momento en que se capturaron los datos de Amazon. Los precios pueden variar en cualquier momento. Te recomendamos consultar siempre el precio actual en Amazon antes de comprar.</p>

    <h2>Marca registrada</h2>
    <p>Amazon y el logotipo de Amazon son marcas registradas de Amazon.com, Inc. o sus afiliados. elclimadecasa.com no es operado por, patrocinado por, ni afiliado de manera especial a Amazon.</p>
'''),
        "privacidad.html": ("Política de privacidad", '''
    <h1>Política de privacidad</h1>
    <p>Última actualización: agosto 2026</p>

    <h2>Responsable del tratamiento</h2>
    <p>El responsable del tratamiento de los datos personales recogidos en este sitio web es <strong>Jordi Escoda Sirvent</strong> (hola@jordiescodasirvent.com).</p>

    <h2>Datos que recopilamos</h2>
    <p>Este sitio web no recopila datos personales directamente. No tenemos formularios de registro, cuentas de usuario ni comentarios.</p>
    <p>Sin embargo, utilizamos servicios de terceros que pueden recopilar información de navegación:</p>
    <ul>
      <li><strong>Google Fonts:</strong> para la tipografía del sitio. Google puede recopilar datos como tu dirección IP.</li>
      <li><strong>Amazon:</strong> cuando haces clic en un enlace de afiliado, Amazon recopila datos según su propia política de privacidad.</li>
    </ul>

    <h2>Cookies</h2>
    <p>Este sitio web no utiliza cookies propias. Los servicios de terceros mencionados anteriormente pueden establecer sus propias cookies según sus respectivas políticas.</p>

    <h2>Tus derechos</h2>
    <p>Tienes derecho a acceder, rectificar, suprimir, limitar y oponerte al tratamiento de tus datos personales conforme al RGPD. Para ejercer estos derechos, contacta con nosotros a través de los datos facilitados en el aviso legal.</p>
'''),
        "aviso-legal.html": ("Aviso legal", '''
    <h1>Aviso legal</h1>
    <p>Última actualización: agosto 2026</p>

    <h2>Información general</h2>
    <p>En cumplimiento de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y Comercio Electrónico (LSSI-CE), se informa que este sitio web es propiedad de <strong>Jordi Escoda Sirvent</strong>.</p>
    <ul>
      <li><strong>Titular:</strong> Jordi Escoda Sirvent</li>
      <li><strong>Sitio web:</strong> elclimadecasa.com</li>
      <li><strong>Correo de contacto:</strong> hola@jordiescodasirvent.com</li>
    </ul>

    <h2>Objeto del sitio web</h2>
    <p>elclimadecasa.com es un sitio web de información y comparativas de productos de climatización del hogar. El sitio contiene enlaces de afiliado a Amazon.es (ver <a href="aviso-afiliados.html" style="color:var(--accent)">aviso de afiliación</a>).</p>

    <h2>Propiedad intelectual</h2>
    <p>El contenido editorial de este sitio web (textos, análisis, comparativas, diseño) es propiedad de su titular. Los nombres de producto, marcas y logotipos pertenecen a sus respectivos propietarios.</p>

    <h2>Limitación de responsabilidad</h2>
    <p>La información publicada en este sitio web tiene carácter informativo y orientativo. No nos hacemos responsables de posibles inexactitudes en las especificaciones técnicas de los productos, que pueden ser modificadas por los fabricantes sin previo aviso. Los precios mostrados son orientativos y pueden variar.</p>

    <h2>Legislación aplicable</h2>
    <p>Este aviso legal se rige por la legislación española. Para cualquier controversia se someterán a los juzgados y tribunales del domicilio del titular.</p>
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

def rebuild_db_js(products):
    import json as j
    db_data = {
        "productos": products,
        "nichos": ["deshumidificadores"],
        "categorias": [
            {"id": "deshumidificadores", "nombre": "Deshumidificadores", "slug": "deshumidificadores", "activa": True},
            {"id": "aires-acondicionados", "nombre": "Aires Acondicionados", "slug": "aires-acondicionados", "activa": False},
            {"id": "calefactores", "nombre": "Calefactores", "slug": "calefactores", "activa": False},
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
        "updated": datetime.now().strftime("%Y-%m-%d")
    }
    js = '(function(){"use strict";window.__DB__=' + j.dumps(db_data, ensure_ascii=False) + ';})();'
    outpath = os.path.join(BASE, "lib", "db.js")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  ✅ lib/db.js (actualizado)")

def main():
    print("🏗️  Generando sitio elclimadecasa.com...")
    products = load_products()
    print(f"  📦 {len(products)} productos cargados")

    rebuild_db_js(products)

    for p in products:
        build_ficha(p, products)

    build_category(products)
    build_comparador()
    build_guide()
    build_legal_pages()

    print(f"\n✅ Build completo. {len(products)} fichas + categoría + comparador + guía + 3 páginas legales")
    print(f"   Cache-buster: ?v={VER}")

if __name__ == "__main__":
    main()
