(function () {
  "use strict";

  var DB = window.__DB__ || {};
  var productos = DB.productos || [];
  var scoreAxes = DB.scoreAxes || [];
  var scoreLabels = DB.scoreLabels || {};

  var $ = function (sel, scope) { return (scope || document).querySelector(sel); };
  var $$ = function (sel, scope) { return Array.from((scope || document).querySelectorAll(sel)); };
  var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var escHTML = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  };
  function safe(fn, name) {
    try { fn(); } catch (e) { console.warn("[" + name + "]", e); }
  }

  var IC = {
    check: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>',
    x: '<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>',
    star: '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>',
    starHalf: '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" opacity=".3"/><path d="M10 2.5l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-.588-.186V2.5z" fill="currentColor"/></svg>'
  };

  function formatPrice(p) {
    if (p == null) return "—";
    return p.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
  }

  function renderStars(rating) {
    var full = Math.floor(rating);
    var half = rating - full >= 0.25;
    var html = '<span class="stars">';
    for (var i = 0; i < full; i++) html += IC.star;
    if (half) html += IC.starHalf;
    html += "</span>";
    return html;
  }

  function getProduct(id) {
    for (var i = 0; i < productos.length; i++) {
      if (productos[i].id === id) return productos[i];
    }
    return null;
  }

  function imgOrPlaceholder(src, alt) {
    if (!src || src.indexOf("PLACEHOLDER") !== -1 || src === "")
      return '<div class="img-placeholder">💧</div>';
    return '<img src="' + escHTML(src) + '" alt="' + escHTML(alt) + '" loading="lazy" decoding="async">';
  }

  /* ---- Nav ---- */
  function initNav() {
    var nav = $(".nav");
    var toggle = $(".nav-toggle");
    var mobile = $(".nav-mobile");
    if (!nav) return;

    window.addEventListener("scroll", function () {
      nav.classList.toggle("scrolled", window.scrollY > 20);
    }, { passive: true });

    if (toggle && mobile) {
      toggle.addEventListener("click", function () {
        toggle.classList.toggle("open");
        mobile.classList.toggle("open");
        document.body.style.overflow = mobile.classList.contains("open") ? "hidden" : "";
      });
      $$("a", mobile).forEach(function (a) {
        a.addEventListener("click", function () {
          toggle.classList.remove("open");
          mobile.classList.remove("open");
          document.body.style.overflow = "";
        });
      });
    }
  }

  /* ---- Smooth scroll ---- */
  function initSmoothScroll() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest('a[href^="#"]');
      if (!a) return;
      var id = a.getAttribute("href");
      if (!id || id === "#") return;
      var el = document.querySelector(id);
      if (!el) return;
      e.preventDefault();
      var navOffset = 80;
      window.scrollTo({
        top: el.getBoundingClientRect().top + scrollY - navOffset,
        behavior: reduced ? "auto" : "smooth"
      });
    });
  }

  /* ---- Reveals ---- */
  function initReveals() {
    var els = $$(".reveal");
    if (!els.length) return;
    if (reduced) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.01, rootMargin: "0px 0px -2% 0px" });
    els.forEach(function (el) { io.observe(el); });
    setTimeout(function () {
      els.forEach(function (el) {
        if (!el.classList.contains("is-visible") &&
            el.getBoundingClientRect().top < window.innerHeight) {
          el.classList.add("is-visible");
        }
      });
    }, 6000);
  }

  /* ---- Radar chart (SVG) ---- */
  function drawRadar(container, scores, opts) {
    opts = opts || {};
    var size = opts.size || 300;
    var cx = size / 2;
    var cy = size / 2;
    var r = (size / 2) - 40;
    var axes = scoreAxes;
    var n = axes.length;
    if (!n) return;
    var colors = opts.colors || ["rgba(37,99,235,.35)"];
    var strokes = opts.strokeColors || ["#2563eb"];

    var angleStep = (2 * Math.PI) / n;
    var startAngle = -Math.PI / 2;

    function pointOnAxis(i, val) {
      var angle = startAngle + i * angleStep;
      var dist = (val / 10) * r;
      return [cx + dist * Math.cos(angle), cy + dist * Math.sin(angle)];
    }

    var svg = '<svg class="' + (opts.className || "radar-svg") + '" viewBox="0 0 ' + size + ' ' + size + '" xmlns="http://www.w3.org/2000/svg">';

    for (var ring = 2; ring <= 10; ring += 2) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var p = pointOnAxis(i, ring);
        pts.push(p[0] + "," + p[1]);
      }
      svg += '<polygon points="' + pts.join(" ") + '" fill="none" stroke="#e2e8f0" stroke-width="1"/>';
    }

    for (var i = 0; i < n; i++) {
      var p = pointOnAxis(i, 10);
      svg += '<line x1="' + cx + '" y1="' + cy + '" x2="' + p[0] + '" y2="' + p[1] + '" stroke="#e2e8f0" stroke-width="1"/>';
    }

    if (!Array.isArray(scores[0])) scores = [scores];

    for (var s = 0; s < scores.length; s++) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var val = scores[s][i] != null ? scores[s][i] : 0;
        var p = pointOnAxis(i, val);
        pts.push(p[0] + "," + p[1]);
      }
      svg += '<polygon points="' + pts.join(" ") + '" fill="' + (colors[s] || colors[0]) + '" stroke="' + (strokes[s] || strokes[0]) + '" stroke-width="2"/>';
    }

    for (var i = 0; i < n; i++) {
      var angle = startAngle + i * angleStep;
      var lx = cx + (r + 24) * Math.cos(angle);
      var ly = cy + (r + 24) * Math.sin(angle);
      var anchor = "middle";
      if (Math.cos(angle) < -0.1) anchor = "end";
      else if (Math.cos(angle) > 0.1) anchor = "start";
      svg += '<text x="' + lx + '" y="' + ly + '" text-anchor="' + anchor + '" dominant-baseline="central" fill="#5a6a7e" font-size="11" font-weight="500">' + escHTML(scoreLabels[axes[i]] || axes[i]) + '</text>';
    }

    svg += "</svg>";
    container.innerHTML = svg;
  }

  /* ---- Ficha radar ---- */
  function initFichaRadar() {
    var el = $("[data-ficha-radar]");
    if (!el) return;
    var pid = el.getAttribute("data-ficha-radar");
    var prod = getProduct(pid);
    if (!prod) return;
    var scores = scoreAxes.map(function (a) {
      return prod["score_" + a] != null ? prod["score_" + a] : 0;
    });
    drawRadar(el, scores);
  }

  /* ---- Category filters ---- */
  function initCategoryFilters() {
    var grid = $("[data-category-grid]");
    if (!grid) return;
    var cards = $$("[data-product-id]", grid);
    var countEl = $(".results-count");
    var category = grid.getAttribute("data-category") || "deshumidificadores";

    function applyFilters() {
      var sortBy = ($("#filter-sort") || {}).value || "relevancia";
      var maxPrice = parseFloat(($("#filter-price") || {}).value || "0");
      var minCap = parseFloat(($("#filter-capacity") || {}).value || "0");
      var maxNoise = parseFloat(($("#filter-noise") || {}).value || "0");
      var minPotencia = parseFloat(($("#filter-potencia") || {}).value || "0");
      var filterTipo = ($("#filter-tipo") || {}).value || "";

      var visible = 0;
      cards.forEach(function (card) {
        var id = card.getAttribute("data-product-id");
        var prod = getProduct(id);
        if (!prod) return;
        var show = true;
        var price = prod.discountedPrice || prod.retailPrice || 0;
        if (maxPrice > 0 && price > maxPrice) show = false;
        if (minCap > 0 && (prod.capacidad_litros_dia || 0) < minCap) show = false;
        if (maxNoise > 0 && (prod.ruido_db || 999) > maxNoise) show = false;
        if (minPotencia > 0 && (prod.potencia_w || 0) < minPotencia) show = false;
        if (filterTipo && (prod.subcategory || "") !== filterTipo) show = false;
        card.style.display = show ? "" : "none";
        if (show) visible++;
      });

      if (countEl) countEl.textContent = visible + " producto" + (visible !== 1 ? "s" : "");

      if (sortBy !== "relevancia") {
        var parent = grid;
        var items = cards.filter(function (c) { return c.style.display !== "none"; });
        items.sort(function (a, b) {
          var pa = getProduct(a.getAttribute("data-product-id")) || {};
          var pb = getProduct(b.getAttribute("data-product-id")) || {};
          if (sortBy === "precio-asc") return (pa.discountedPrice || pa.retailPrice || 0) - (pb.discountedPrice || pb.retailPrice || 0);
          if (sortBy === "precio-desc") return (pb.discountedPrice || pb.retailPrice || 0) - (pa.discountedPrice || pa.retailPrice || 0);
          if (sortBy === "capacidad") return (pb.capacidad_litros_dia || 0) - (pa.capacidad_litros_dia || 0);
          if (sortBy === "potencia") return (pb.potencia_w || 0) - (pa.potencia_w || 0);
          if (sortBy === "silencio") return (pa.ruido_db || 99) - (pb.ruido_db || 99);
          if (sortBy === "valoracion") return (pb.valoracion_media || 0) - (pa.valoracion_media || 0);
          return 0;
        });
        items.forEach(function (item) { parent.appendChild(item); });
      }
    }

    $$(".filter-select").forEach(function (sel) {
      sel.addEventListener("change", applyFilters);
    });
  }

  /* ---- Comparador ---- */
  function initComparador() {
    var page = $("[data-comparador]");
    if (!page) return;

    var compareColors = [
      { fill: "rgba(37,99,235,.3)", stroke: "#2563eb", swatch: "#2563eb" },
      { fill: "rgba(220,38,38,.25)", stroke: "#dc2626", swatch: "#dc2626" },
      { fill: "rgba(5,150,105,.25)", stroke: "#059669", swatch: "#059669" }
    ];

    var selected = [];
    var maxCompare = 3;

    var hash = window.location.hash.replace("#", "");
    if (hash) {
      hash.split(",").forEach(function (id) {
        var p = getProduct(id);
        if (p && selected.length < maxCompare) selected.push(p.id);
      });
    }

    function updateHash() {
      history.replaceState(null, "", selected.length ? "#" + selected.join(",") : window.location.pathname);
    }

    function render() {
      renderSlots();
      renderTable();
      renderRadar();
      updateHash();
    }

    function renderSlots() {
      var wrap = $(".compare-selector");
      if (!wrap) return;
      var html = "";
      for (var i = 0; i < maxCompare; i++) {
        if (i < selected.length) {
          var p = getProduct(selected[i]);
          html += '<div class="compare-slot filled">' +
            '<button class="remove-badge" data-remove="' + i + '">&times;</button>' +
            '<div class="compare-slot-img">' + imgOrPlaceholder((p.images || [])[0], p.name) + '</div>' +
            '<div class="compare-slot-name">' + escHTML(p.name) + '</div>' +
            '</div>';
        } else {
          html += '<div class="compare-slot">' +
            '<div class="compare-slot-img"><div class="img-placeholder" style="font-size:1.5rem">+</div></div>' +
            '<select class="compare-add-select" data-slot="' + i + '">' +
            '<option value="">Añadir producto...</option>';
          productos.forEach(function (p) {
            if (selected.indexOf(p.id) === -1) {
              html += '<option value="' + escHTML(p.id) + '">' + escHTML(p.name) + '</option>';
            }
          });
          html += '</select></div>';
        }
      }
      wrap.innerHTML = html;

      $$(".remove-badge", wrap).forEach(function (btn) {
        btn.addEventListener("click", function () {
          selected.splice(parseInt(btn.getAttribute("data-remove")), 1);
          render();
        });
      });
      $$(".compare-add-select", wrap).forEach(function (sel) {
        sel.addEventListener("change", function () {
          if (sel.value && selected.length < maxCompare) {
            selected.push(sel.value);
            render();
          }
        });
      });
    }

    function renderTable() {
      var wrap = $(".compare-table-wrap");
      if (!wrap) return;
      if (selected.length < 2) {
        wrap.innerHTML = '<p style="padding:2rem;text-align:center;color:var(--text-muted)">Selecciona al menos 2 productos para comparar</p>';
        return;
      }
      var prods = selected.map(getProduct).filter(Boolean);
      var html = '<table class="compare-table"><thead><tr><th></th>';
      prods.forEach(function (p) {
        html += '<th>' + escHTML(p.name) + '</th>';
      });
      html += '</tr></thead><tbody>';

      html += '<tr><td>Precio</td>';
      prods.forEach(function (p) {
        html += '<td>' + formatPrice(p.discountedPrice || p.retailPrice) + '</td>';
      });
      html += '</tr>';

      html += '<tr><td>Valoración</td>';
      prods.forEach(function (p) {
        html += '<td>' + renderStars(p.valoracion_media || 0) + ' ' + (p.valoracion_media || "—") + '</td>';
      });
      html += '</tr>';

      var dbSpecs = (DB.compareSpecs || {});
      var cats = prods.map(function(p){ return p.category; });
      var allSame = cats.every(function(c){ return c === cats[0]; });
      var specs = (allSame && dbSpecs[cats[0]]) ? dbSpecs[cats[0]] : [
        { label: "Potencia", key: "potencia_w", unit: " W", best: "max" },
        { label: "Cobertura", key: "cobertura_m2", unit: " m²", best: "max" },
        { label: "Peso", key: "peso_kg", unit: " kg", best: "min" },
        { label: "Temporizador", key: "temporizador", type: "bool" },
        { label: "Control app", key: "control_app", type: "bool" }
      ];

      html += '<tr class="spec-group-row"><td colspan="' + (prods.length + 1) + '">Especificaciones técnicas</td></tr>';

      specs.forEach(function (spec) {
        html += '<tr><td>' + escHTML(spec.label) + '</td>';
        if (spec.type === "bool") {
          prods.forEach(function (p) {
            var v = p[spec.key];
            html += '<td>' + (v ? '<span class="spec-bool-yes">Sí</span>' : '<span class="spec-bool-no">No</span>') + '</td>';
          });
        } else {
          var vals = prods.map(function (p) { return p[spec.key]; });
          var bestVal = spec.best === "max" ? Math.max.apply(null, vals.filter(function(v){return v!=null;})) : Math.min.apply(null, vals.filter(function(v){return v!=null;}));
          prods.forEach(function (p) {
            var v = p[spec.key];
            var cls = (v != null && v === bestVal && prods.length > 1) ? ' class="best-value"' : '';
            html += '<td' + cls + '>' + (v != null ? v + (spec.unit || "") : "—") + '</td>';
          });
        }
        html += '</tr>';
      });

      html += '<tr class="spec-group-row"><td colspan="' + (prods.length + 1) + '">Puntuaciones del editor</td></tr>';
      scoreAxes.forEach(function (axis) {
        html += '<tr><td>' + escHTML(scoreLabels[axis] || axis) + '</td>';
        var vals = prods.map(function (p) { return p["score_" + axis]; });
        var best = Math.max.apply(null, vals.filter(function(v){return v!=null;}));
        prods.forEach(function (p) {
          var v = p["score_" + axis];
          var cls = (v != null && v === best && prods.length > 1) ? ' class="best-value"' : '';
          html += '<td' + cls + '>' + (v != null ? v + "/10" : "—") + '</td>';
        });
        html += '</tr>';
      });

      html += '<tr><td></td>';
      prods.forEach(function (p) {
        html += '<td><a href="' + escHTML(p.affiliate_url) + '" class="btn btn-amazon btn-sm" target="_blank" rel="nofollow noopener">Ver en Amazon</a></td>';
      });
      html += '</tr>';

      html += '</tbody></table>';
      wrap.innerHTML = html;
    }

    function renderRadar() {
      var wrap = $(".compare-radar-wrap");
      if (!wrap) return;
      if (selected.length < 2) {
        wrap.style.display = "none";
        return;
      }
      wrap.style.display = "";

      var prods = selected.map(getProduct).filter(Boolean);
      var allScores = prods.map(function (p) {
        return scoreAxes.map(function (a) {
          return p["score_" + a] != null ? p["score_" + a] : 0;
        });
      });

      var radarEl = $(".compare-radar-target", wrap);
      if (!radarEl) {
        radarEl = document.createElement("div");
        radarEl.className = "compare-radar-target";
        wrap.insertBefore(radarEl, wrap.firstChild);
      }

      drawRadar(radarEl, allScores, {
        size: 350,
        className: "compare-radar-svg",
        colors: compareColors.map(function (c) { return c.fill; }),
        strokeColors: compareColors.map(function (c) { return c.stroke; })
      });

      var legend = $(".compare-radar-legend", wrap);
      if (legend) {
        legend.innerHTML = prods.map(function (p, i) {
          return '<span class="compare-radar-legend-item"><span class="compare-legend-swatch" style="background:' + compareColors[i].swatch + '"></span>' + escHTML(p.name) + '</span>';
        }).join("");
      }
    }

    render();
  }

  /* ---- Boot ---- */
  function boot() {
    safe(initNav, "initNav");
    safe(initSmoothScroll, "initSmoothScroll");
    safe(initReveals, "initReveals");
    safe(initFichaRadar, "initFichaRadar");
    safe(initCategoryFilters, "initCategoryFilters");
    safe(initComparador, "initComparador");
    document.documentElement.classList.add("is-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
