# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""Render the three page types: index (overview), catalog (filterable), paper (reproduction doc).

Pure formatting over the :class:`~nirs4all_papers.model.PaperView` view models via
:mod:`components` + :mod:`charts` + :mod:`assets` + the provenance sidecars. No recomputation.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import __version__, provenance
from ..model import Catalog, PaperView
from . import assets
from . import components as C
from .charts import spectra_preview
from .escape import Safe, cell, esc, inline_json, locator_link, num, safe_url
from .theme import SITE_URL, page

# Build date stamp (constant within a build process, so output stays idempotent per run).
BUILD_STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# =============================================================================
# INDEX
# =============================================================================
def _index_kpis(catalog: Catalog) -> list[tuple[str, str]]:
    methods = {r.id for p in catalog.papers for r in p.references}
    datasets = {p.dataset.get("name") for p in catalog.papers if p.dataset.get("name")}
    steps = sum(len([s for s in p.steps if s.info.kind != "split"]) for p in catalog.papers)
    replays = sum(1 for p in catalog.papers if p.replay)
    return [
        (num(len(catalog.papers)), "papers"),
        (num(len(methods)), "methods cited"),
        (num(len(datasets)), "datasets"),
        (num(steps), "pipeline steps"),
        (num(replays), "live replays"),
    ]


def _how_it_works() -> str:
    cards = [
        ("&#129513;", "Methods &amp; bibliography", "Every preprocessing step and model is named, parametrised, and cross-referenced to the literature — a real reference list, auto-built from the pipeline."),
        ("&#9654;", "Live in-browser replay", "Re-run the published pipeline on the included dataset — leakage-safe cross-validation, parity and residual plots recomputed in your browser, no install."),
        ("&#128230;", "Deposit-ready sidecars", "Each paper ships CITATION.cff, BibTeX, an RO-Crate, and the deposited <code>.n4a</code> — fingerprinted and citable."),
    ]
    items = "".join(
        f'<div class="kpi" style="--accent:var(--teal);text-align:left;padding:22px 24px">'
        f'<div style="font-size:1.6rem;margin-bottom:8px">{ic}</div>'
        f'<div style="font-family:var(--display);font-weight:600;font-size:1.05rem;margin-bottom:6px">{title}</div>'
        f'<div style="font-size:.9rem;color:var(--text-2);line-height:1.6">{body}</div></div>'
        for ic, title, body in cards
    )
    return f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px">{items}</div>'


def render_index(catalog: Catalog) -> str:
    methods = {r.id for p in catalog.papers for r in p.references}
    body = f"""
{C.nav("", "index")}
{C.hero(len(catalog.papers), len(methods))}
<section class="section section-paper">
  <div class="container">
    {C.section_head("The archive at a glance", "Reproducible by <em>construction</em>")}
    {C.kpi_strip(_index_kpis(catalog))}
  </div>
</section>
<section class="section section-aurora">
  <div class="container">
    {C.section_head("How it works", "From a <em>.n4a</em> to a paper", "Point the publisher at a deposited bundle and a short metadata file; it emits the reproduction document, the bibliography, the replay, and the deposit sidecars.")}
    {_how_it_works()}
  </div>
</section>
<section class="section">
  <div class="container" style="text-align:center">
    {C.section_head("Browse", "Every <em>published</em> pipeline", "Open a paper to read its methods, see its scores, and re-run it live.")}
    <a class="btn btn-primary" href="catalog.html">Open the paper archive &rarr;</a>
  </div>
</section>
{C.footer("")}
"""
    return page(title="nirs4all-papers — reproducible deposited pipelines", rel="", body=body, scripts=C.HERO_SCRIPT, canonical="")


# =============================================================================
# CATALOG
# =============================================================================
def render_catalog(catalog: Catalog) -> str:
    cards = "".join(C.paper_card(p) for p in catalog.papers) or '<div class="empty">No papers deposited yet.</div>'
    models = sorted({(p.model_step.info.short_name if p.model_step else "") for p in catalog.papers if p.model_step})
    statuses = sorted({p.status for p in catalog.papers})

    def opts(values: list[str]) -> str:
        return "".join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in values if x)

    body = f"""
{C.nav("", "catalog")}
<section class="section-tight section-paper" style="padding-top:84px">
  <div class="container">
    {C.section_head("Browse", "The <em>paper</em> archive", "Filter and search every deposited reproduction document.")}
  </div>
</section>
<section class="section" style="padding-top:32px">
  <div class="container">
    <div class="controls">
      <input id="q" type="search" placeholder="Search title, author, method…" aria-label="Search papers">
      <select id="f-status" aria-label="Filter by status"><option value="">all statuses</option>{opts(statuses)}</select>
      <select id="f-model" aria-label="Filter by model"><option value="">all models</option>{opts(models)}</select>
      <select id="f-sort" aria-label="Sort"><option value="name">A → Z</option><option value="year">newest</option><option value="refs">most references</option></select>
      <button class="btn-reset" id="reset">reset</button>
      <span class="count" id="count"></span>
    </div>
    <div class="cards" id="cards">{cards}</div>
    <div class="empty hidden" id="empty">No paper matches these filters.</div>
  </div>
</section>
{C.footer("")}
"""
    return page(title="Papers — nirs4all-papers", rel="", body=body, scripts=_CATALOG_JS, canonical="catalog.html")


_CATALOG_JS = """
<script>
(function(){
  var cards=[].slice.call(document.querySelectorAll('.p-card'));
  var q=document.getElementById('q'),count=document.getElementById('count'),empty=document.getElementById('empty'),grid=document.getElementById('cards');
  var fs=document.getElementById('f-status'),fm=document.getElementById('f-model'),sort=document.getElementById('f-sort');
  function apply(){var t=(q.value||'').trim().toLowerCase();var n=0;
    cards.forEach(function(c){var ok=true;
      if(t&&c.getAttribute('data-name').indexOf(t)<0)ok=false;
      if(fs.value&&c.getAttribute('data-status')!==fs.value)ok=false;
      if(fm.value&&c.getAttribute('data-model')!==fm.value)ok=false;
      c.classList.toggle('hidden',!ok);if(ok)n++;});
    count.textContent=n+' / '+cards.length+' papers';empty.classList.toggle('hidden',n>0);}
  function resort(){var key=sort.value,vis=cards.slice();
    vis.sort(function(a,b){if(key==='name')return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent);
      return (+b.getAttribute('data-'+key))-(+a.getAttribute('data-'+key));});
    vis.forEach(function(c){grid.appendChild(c);});}
  q.addEventListener('input',apply);fs.addEventListener('change',apply);fm.addEventListener('change',apply);
  sort.addEventListener('change',function(){resort();apply();});
  document.getElementById('reset').addEventListener('click',function(){q.value='';fs.value='';fm.value='';sort.value='name';resort();apply();});
  resort();apply();
})();
</script>
"""


# =============================================================================
# PAPER (reproduction document)
# =============================================================================
def _authors_html(view: PaperView) -> str:
    parts = []
    for a in view.authors:
        name = esc(a.name)
        if a.orcid:
            orcid = a.orcid if a.orcid.startswith("http") else f"https://orcid.org/{a.orcid}"
            href = safe_url(orcid)
            if href:
                name = f'<a href="{href}" target="_blank" rel="noopener">{name}</a>'
        parts.append(name)
    affils = sorted({a.affiliation for a in view.authors if a.affiliation})
    affil_html = f'<div class="paper-affil">{esc("; ".join(affils))}</div>' if affils else ""
    return f'<div class="paper-authors">{", ".join(parts)}</div>{affil_html}' if parts else ""


def _paper_badges(view: PaperView) -> str:
    badges = [C.status_badge(view.status)]
    if view.venue:
        badges.append(C.badge(str(view.venue), "neutral"))
    if view.year:
        badges.append(C.badge(str(view.year), "neutral"))
    if view.doi:
        badges.append(C.badge(f"DOI {view.doi}", "info"))
    badges.append(C.badge(f"nirs4all {view.bundle.nirs4all_version}", "neutral"))
    return "".join(badges)


def _protocol_panel(view: PaperView) -> str:
    proto = view.protocol
    rows = [
        ("Split", proto.get("split")),
        ("Cross-validation", proto.get("cv")),
        ("Scoring metric", proto.get("metric")),
        ("Fold strategy", proto.get("fold_strategy") or view.bundle.manifest.get("fold_strategy")),
    ]
    if view.bundle.fold_weights:
        weights = ", ".join(f"fold {k}: {num(v)}" for k, v in sorted(view.bundle.fold_weights.items()))
        rows.append(("Fold weights", weights))
    body = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows if v)
    if not body:
        body = '<tr><td colspan="2" class="dl-note">Protocol not recorded — add it to paper.yaml.</td></tr>'
    return f'<section class="panel"><h2>Protocol</h2><div class="panel-body"><table class="kv"><tbody>{body}</tbody></table></div></section>'


def _results_panel(view: PaperView) -> str:
    if not view.metrics:
        return (
            '<section class="panel"><h2>Results</h2><div class="panel-body">'
            '<p class="dl-note">No published scores recorded in paper.yaml. The live replay below recomputes scores from the included dataset.</p></div></section>'
        )
    def _cell(m: object) -> str:
        part = f'<div class="m-p">{esc(m.partition)}</div>' if m.partition else ""  # type: ignore[attr-defined]
        return (
            f'<div class="metric-cell"><div class="m-v">{esc(C.metric_value(m.value))}</div>'  # type: ignore[attr-defined]
            f'<div class="m-n">{esc(m.name)}</div>{part}</div>'  # type: ignore[attr-defined]
        )

    cells = "".join(_cell(m) for m in view.metrics)
    return f'<section class="panel"><h2>Results<span class="h2-tag">as published</span></h2><div class="panel-body"><div class="metric-grid">{cells}</div></div></section>'


def _dataset_panel(view: PaperView) -> str:
    ds = view.dataset
    rows = [
        ("Dataset", ds.get("name")),
        ("DOI", locator_link(ds.get("doi")) if ds.get("doi") else None),
        ("Target", ds.get("target")),
        ("Samples", num(ds.get("n_samples")) if ds.get("n_samples") else None),
        ("Wavelengths", num(ds.get("n_features")) if ds.get("n_features") else None),
        ("Note", ds.get("note")),
    ]
    body = "".join(f"<tr><th>{esc(k)}</th><td>{cell(v)}</td></tr>" for k, v in rows if v)
    preview = ""
    if view.replay and view.replay.get("axis") and view.replay.get("X"):
        svg = spectra_preview(view.replay["axis"], view.replay["X"], title="included spectra", unit=view.replay.get("axis_unit") or "", width=520)
        preview = f'<div class="chart" tabindex="0" role="button" style="margin-top:14px">{svg}</div>'
    inner = f'<table class="kv"><tbody>{body}</tbody></table>{preview}' if body else (preview or '<p class="dl-note">No dataset metadata.</p>')
    return f'<section class="panel"><h2>Dataset</h2><div class="panel-body">{inner}</div></section>'


def _methods_narrative(view: PaperView) -> str:
    def cite(sv) -> str:
        if sv.reference and sv.reference.number:
            return f'<sup><a href="#ref-{sv.reference.number}">[{sv.reference.number}]</a></sup>'
        return ""

    pre = [s for s in view.steps if s.info.kind == "preprocessing"]
    tgt = next((s for s in view.steps if s.info.kind == "target"), None)
    model = view.model_step
    paras: list[str] = []
    if pre:
        phrases = ", then ".join(
            f"{esc(s.reference.label if s.reference else s.info.short_name)}{cite(s)}" for s in pre
        )
        paras.append(f"<p>Spectra were preprocessed by {phrases}.</p>")
    if tgt:
        paras.append(f"<p>The regression target was {esc(tgt.reference.label if tgt.reference else tgt.info.short_name)}{cite(tgt)} prior to modelling.</p>")
    if model:
        ncomp = model.info.params.get("n_components")
        lv = f" with {ncomp} latent variables" if ncomp is not None else ""
        proto = view.protocol.get("cv")
        proto_txt = f", evaluated by {esc(proto)}" if proto else ""
        paras.append(
            f"<p>A {esc(model.reference.label if model.reference else model.info.short_name)}{cite(model)} model{lv} was then calibrated{proto_txt}. "
            "The fitted pipeline and per-fold artifacts are bundled in the deposited <code>.n4a</code>.</p>"
        )
    if not paras:
        return ""
    return f'<section class="panel wide"><h2>Methods</h2><div class="panel-body methods-narrative">{"".join(paras)}</div></section>'


def _provenance_panel(view: PaperView, rel: str) -> str:
    b = view.bundle
    rows: list[tuple[str, object]] = [
        ("Pipeline UID", Safe(f"<code>{esc(b.pipeline_uid)}</code>") if b.pipeline_uid else None),
        ("Bundle fingerprint", Safe(f"<code>{esc(b.fingerprint[:24])}…</code>")),
        ("nirs4all version", b.nirs4all_version),
        ("Created", b.manifest.get("created_at")),
        ("Source type", b.manifest.get("source_type")),
    ]
    prov = view.provenance
    if prov.get("source_repo"):
        commit = f" @ {esc(prov.get('source_commit'))}" if prov.get("source_commit") else ""
        rows.append(("Source", Safe(f"{esc(prov.get('source_repo'))}{commit}")))
    kv = "".join(f"<tr><th>{esc(k)}</th><td>{cell(v)}</td></tr>" for k, v in rows if v)

    file_rows = "".join(
        f'<tr><td><code>{esc(f.name)}</code></td><td class="num">{num(f.size)}</td><td><code>{esc(f.sha256[:12])}…</code></td></tr>'
        for f in sorted(b.files, key=lambda f: f.name)
    )
    file_table = (
        '<div class="table-scroll" style="margin-top:14px"><table class="data"><thead><tr><th>File</th>'
        '<th class="num">Bytes</th><th>SHA-256</th></tr></thead><tbody>' + file_rows + "</tbody></table></div>"
    )

    commands = _copyable_code(C.code_block(provenance.reproduction_commands(view)), "repro-cmd")
    slug = view.slug
    downloads = (
        '<div class="dl-row" style="margin-top:16px">'
        f'<a class="dl-btn" href="{slug}/{esc(view.bundle_filename)}">{esc(view.bundle_filename)} <span class="ext">.n4a</span></a>'
        f'<a class="dl-btn" href="{slug}/pipeline.json">pipeline.json</a>'
        f'<a class="dl-btn" href="{slug}/CITATION.cff">CITATION.cff</a>'
        f'<a class="dl-btn" href="{slug}/references.bib">references.bib</a>'
        f'<a class="dl-btn" href="{slug}/ro-crate-metadata.json">ro-crate-metadata.json</a>'
        "</div>"
    )
    return (
        '<section class="panel wide"><h2>Provenance &amp; reproduction<span class="h2-tag">fingerprinted</span></h2>'
        f'<div class="panel-body"><table class="kv"><tbody>{kv}</tbody></table>{file_table}'
        f'<div style="margin-top:18px">{commands}</div>{downloads}</div></section>'
    )


def _copyable_code(codeblock_html: str, pre_id: str) -> str:
    """Wrap a `.codeblock` so it has a copy button bound to an id'd `<pre>`."""
    html = codeblock_html.replace("<pre>", f'<pre id="{esc(pre_id)}">', 1)
    return f'<div class="copy-wrap">{C.copy_button(pre_id)}{html}</div>'


def _license_panel(view: PaperView) -> str:
    """Make the three license layers explicit: manuscript, reproduction code/content, dataset."""
    ds = view.dataset
    cells = [
        ("Manuscript", view.manuscript_license or "publisher's terms"),
        ("Reproduction bundle", "CeCILL-2.1 OR AGPL-3.0-or-later"),
        ("Dataset", (ds.get("license") or ("synthetic — no constraints" if (view.replay or {}).get("synthetic") else "see dataset DOI / origin"))),
    ]
    grid = "".join(
        f'<div class="license-cell"><div class="l-k">{esc(k)}</div><div class="l-v">{esc(v)}</div></div>'
        for k, v in cells
    )
    note = (
        '<p class="dl-note" style="margin-top:12px">Deposited manuscripts keep their publisher\'s copyright; '
        "datasets keep their own license / DOI terms. The reproduction code and page are dual-licensed open-source.</p>"
    )
    return f'<section class="panel wide"><h2>Licensing</h2><div class="panel-body"><div class="license-grid">{grid}</div>{note}</div></section>'


def _citation_panel(view: PaperView) -> str:
    bib = esc(provenance.paper_bibtex(view))
    cff = esc(provenance.citation_cff(view))
    bib_block = _copyable_code(f'<div class="codeblock"><div class="topbar"><i></i><i></i><i></i></div><pre>{bib}</pre></div>', "cite-bibtex")
    cff_block = _copyable_code(f'<div class="codeblock" style="margin-top:10px"><pre>{cff}</pre></div>', "cite-cff")
    guidance = (
        '<p class="dl-note" style="margin-bottom:14px">Cite the <strong>paper</strong> (below) for the science; '
        'cite this reproduction page / the deposited <code>.n4a</code> by its bundle fingerprint when referencing the exact pipeline.</p>'
    )
    return (
        '<section class="panel wide"><h2>Cite this</h2><div class="panel-body">'
        f"{guidance}{bib_block}"
        '<details style="margin-top:14px"><summary style="cursor:pointer;font-family:var(--display);font-weight:600">CITATION.cff</summary>'
        f"{cff_block}</details>"
        "</div></section>"
    )


def _scholarly_head(view: PaperView) -> str:
    """Google-Scholar / Zotero `citation_*` meta tags + a schema.org JSON-LD ScholarlyArticle."""
    tags: list[str] = []

    def m(name: str, content: object) -> None:
        if content:
            tags.append(f'<meta name="{name}" content="{esc(str(content))}">')

    m("citation_title", view.title)
    for a in view.authors:
        m("citation_author", a.name)
    if view.year:
        m("citation_publication_date", view.year)
    m("citation_journal_title", view.venue)
    m("citation_doi", view.doi)
    m("citation_abstract_html_url", f"{SITE_URL}/paper/{view.slug}.html")

    ld: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": view.title,
        "name": view.title,
        "url": f"{SITE_URL}/paper/{view.slug}.html",
    }
    if view.abstract:
        ld["abstract"] = view.abstract
    if view.authors:
        ld["author"] = [{"@type": "Person", "name": a.name} for a in view.authors]
    if view.year:
        ld["datePublished"] = str(view.year)
    if view.doi:
        ld["identifier"] = f"https://doi.org/{view.doi}"
    if view.venue:
        ld["publication"] = view.venue
    if view.keywords:
        ld["keywords"] = ", ".join(view.keywords)
    script = f'<script type="application/ld+json">{inline_json(ld)}</script>'
    return "\n".join(tags) + "\n" + script


def render_paper(view: PaperView) -> str:
    rel = "../"
    keywords = "".join(f'<span class="kw">{esc(k)}</span>' for k in view.keywords)
    kw_html = f'<div class="paper-kw">{keywords}</div>' if keywords else ""
    abstract = f'<p class="paper-abstract">{esc(view.abstract)}</p>' if view.abstract else ""
    links = ""
    if view.links:
        rendered = []
        for link in view.links:
            href = safe_url(link.get("url"))
            label = esc(link.get("label") or link.get("url"))
            rendered.append(f'<a href="{href}" target="_blank" rel="noopener">{label}</a>' if href else label)
        link_html = " · ".join(r for r in rendered if r)
        links = f'<div style="margin-top:14px;font-size:.88rem">{link_html}</div>' if link_html else ""

    def _inject(pid: str, html: str) -> str:
        return html.replace('class="panel', f'id="{pid}" class="panel-anchor ', 1) if html.strip() else html

    pipeline_panel = _inject(
        "pipeline",
        f'<section class="panel wide"><h2>Pipeline<span class="h2-tag">{view.n_steps} steps</span></h2>'
        f'<div class="panel-body">{C.pipeline_steps(view, rel)}</div></section>',
    )
    bib_panel = _inject(
        "bibliography",
        f'<section class="panel wide"><h2>Bibliography<span class="h2-tag">{len(view.references)} references</span></h2>'
        f'<div class="panel-body">{C.reference_list(view.references)}</div></section>',
    )
    results_grid = (
        f'<div id="results" class="panel-grid panel-anchor">{_protocol_panel(view)}{_results_panel(view)}{_dataset_panel(view)}</div>'
    )

    entries = [
        ("pipeline", "Pipeline", pipeline_panel),
        ("results", "Protocol &amp; results", results_grid),
        ("replay", "Live replay", _inject("replay", assets.replay_panel(view, rel))),
        ("methods", "Methods", _inject("methods", _methods_narrative(view))),
        ("bibliography", "Bibliography", bib_panel),
        ("license", "Licensing", _inject("license", _license_panel(view))),
        ("provenance", "Provenance", _inject("provenance", _provenance_panel(view, rel))),
        ("cite", "Cite this", _inject("cite", _citation_panel(view))),
    ]
    entries = [(pid, title, html) for pid, title, html in entries if html.strip()]
    toc_links = "".join(f'<a href="#{pid}">{title}</a>' for pid, title, _ in entries)
    toc = f'<aside class="toc"><h4>On this page</h4><nav>{toc_links}</nav></aside>'
    main = f'<div style="display:flex;flex-direction:column;gap:20px;min-width:0">{"".join(h for _, _, h in entries)}</div>'

    build = f'<div class="build-stamp">Generated by n4a-papers {__version__} · {esc(BUILD_STAMP)}</div>'

    body = f"""
{C.nav(rel, "catalog")}
<section class="paper-hero section-paper">
  <div class="container">
    <a class="back" href="{rel}catalog.html">&larr; Back to the archive</a>
    <div class="paper-badges">{_paper_badges(view)}</div>
    <h1 class="paper-title">{esc(view.title)}</h1>
    {_authors_html(view)}
    {f'<div class="paper-venue">{esc(view.venue)}</div>' if view.venue else ""}
    {abstract}
    {kw_html}
    {links}
  </div>
</section>
<section class="section" style="padding-top:36px">
  <div class="container">
    {C.kpi_strip(view.headline_metrics())}
    <div style="margin-top:26px" class="paper-layout">{toc}{main}</div>
    {build}
  </div>
</section>
{C.footer(rel)}
"""
    return page(
        title=f"{view.title} — nirs4all-papers",
        rel=rel,
        body=body,
        description=view.abstract[:180] if view.abstract else "",
        canonical=f"paper/{view.slug}.html",
        head_extra=_scholarly_head(view),
    )
