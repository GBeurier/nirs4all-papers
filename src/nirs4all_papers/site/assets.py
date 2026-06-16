# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
"""The live in-browser pipeline replay: a self-contained, pure-JS reference engine.

It re-runs the *published pipeline definition* (preprocessing + target transform + PLS model) on the
deposited dataset under leakage-safe k-fold cross-validation, recomputes the parity/residual plots
and RMSE/R²/RPD, and renders them as inline SVG — with **no build step and no network**, so it works
from ``file://`` and on GitHub Pages alike.

This is the alpha replay engine. The production target is the **libn4m WebAssembly** engine already
shipped in ``nirs4all-web`` (``runPortablePipeline``); the panel is structured to swap to it. The
numerics here (NIPALS PLS, SNV, Savitzky–Golay, standardisation, k-fold OOF) are genuine — not a
recording — but the page never claims to be WebAssembly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .escape import esc, inline_json

if TYPE_CHECKING:
    from ..model import PaperView

# Feature-space ops the JS engine implements (fit-on-train where stateful).
_SUPPORTED_FEATURE_OPS = {"minmax", "snv", "standard_scaler", "savgol", "msc", "detrend", "first_derivative", "second_derivative", "gaussian_filter"}
_PLS_FAMILY = {"pls", "simpls", "ikpls", "pcr"}


def replay_plan(view: PaperView) -> dict[str, Any]:
    """Translate the typed pipeline steps into an executable plan for the JS engine."""
    features: list[dict[str, Any]] = []
    y_transform: str | None = None
    model: dict[str, Any] | None = None
    unsupported: list[str] = []

    for sv in view.steps:
        kind = sv.info.kind
        mid = sv.method_id
        if kind == "split":
            continue
        if kind == "target":
            y_transform = "minmax" if mid == "minmax" else "standard_scaler"
            continue
        if kind == "model":
            n_comp = sv.info.params.get("n_components")
            is_pls = (mid in _PLS_FAMILY) or ("pls" in sv.info.short_name.lower())
            model = {
                "op": "pls",
                "n_components": int(n_comp) if isinstance(n_comp, (int, float)) else 10,
                "supported": is_pls,
                "name": sv.info.short_name,
            }
            continue
        op = mid if mid in _SUPPORTED_FEATURE_OPS else None
        if op is None:
            unsupported.append(sv.info.short_name)
            continue
        features.append({"op": op, "params": sv.info.params})

    return {"features": features, "yTransform": y_transform, "model": model, "cv": 5, "unsupported": unsupported}


def replay_panel(view: PaperView, rel: str) -> str:
    """The replay section: payload + controls + chart slots, or a graceful 'no dataset' note."""
    if not view.replay:
        return (
            '<section class="panel wide"><h2>Live replay<span class="h2-tag">in-browser</span></h2>'
            '<div class="panel-body"><p class="dl-note">No replay dataset was included with this paper '
            '(<code>replay.json</code>). The full pipeline is still reproducible from the deposited '
            '<code>.n4a</code> with the commands in the reproduction section below.</p></div></section>'
        )

    plan = replay_plan(view)
    ds = view.replay
    payload = {
        "plan": plan,
        "dataset": {
            "X": ds.get("X"),
            "y": ds.get("y"),
            "axis": ds.get("axis"),
            "target": ds.get("target") or "target",
            "name": ds.get("name") or "dataset",
        },
    }
    model = plan.get("model") or {}
    unsupported_note = ""
    if plan.get("unsupported"):
        ops = plan["unsupported"]
        verb = "is" if len(ops) == 1 else "are"
        pron = "it" if len(ops) == 1 else "them"
        unsupported_note = (
            f'<p class="replay-note">Note: {esc(", ".join(ops))} {verb} not in the in-browser reference '
            f"engine and {'was' if len(ops) == 1 else 'were'} skipped; the deposited bundle applies {pron} in full.</p>"
        )
    model_note = ""
    if model and not model.get("supported"):
        model_note = (
            f'<p class="replay-note">The model <code>{esc(model.get("name"))}</code> is not in the '
            "in-browser reference engine (PLS family only in this alpha); the parity below uses PLS as a stand-in.</p>"
        )
    syn = ds.get("synthetic")
    data_note = ds.get("note") or ("Synthetic demonstration dataset — no redistribution constraints." if syn else "")

    return f"""
<section class="panel wide replay-wrap">
  <h2>Live replay — re-run this pipeline<span class="h2-tag">in your browser</span></h2>
  <div class="panel-body">
    <div class="replay-controls">
      <button class="btn btn-primary" id="replay-run">&#9654; Run the pipeline</button>
      <span class="replay-status" id="replay-status">ready</span>
      <span class="replay-engine" style="margin-left:auto"><i></i> pure-JS reference engine · NIPALS PLS · {esc(str(plan.get("cv")))}-fold OOF</span>
    </div>
    <div class="replay-metrics" id="replay-metrics"></div>
    <div class="replay-grid">
      <div class="replay-chart chart" id="replay-parity" tabindex="0" role="button" aria-label="parity plot"></div>
      <div class="replay-chart chart" id="replay-resid" tabindex="0" role="button" aria-label="residual plot"></div>
    </div>
    <p class="replay-note">Re-runs the published preprocessing + model on the included dataset under
    leakage-safe {esc(str(plan.get("cv")))}-fold cross-validation, recomputing out-of-fold predictions and scores entirely in
    your browser. {esc(data_note)}</p>
    <p class="replay-note"><strong>Approximate.</strong> This is an independent pure-JS reference engine
    (NIPALS PLS) with a deterministic {esc(str(plan.get("cv")))}-fold split — it demonstrates the pipeline, but does not reproduce
    the deposited run's exact PLS implementation or fold strategy, so these scores are close to, not
    identical to, the published values above. The exact pipeline is reproducible from the
    <code>.n4a</code> with the commands below.</p>
    {unsupported_note}{model_note}
  </div>
</section>
<script>window.__N4A_REPLAY__ = {inline_json(payload)};</script>
<script>{REPLAY_JS}</script>
"""


# The engine. Plain string (no f-string) so JS braces are literal.
REPLAY_JS = r"""
(function () {
  "use strict";
  var DATA = window.__N4A_REPLAY__;
  if (!DATA) return;
  var TEAL = "#0f766e", TEALS = "#0d9488", MUTED = "#64748b", FAINT = "#94a3b8",
      GRID = "#dde4ec", GRIDS = "#eef2f7", INK = "#0f172a", AMBER = "#b7791f";

  // ── tiny matrix helpers (row-major arrays of arrays) ──────────────────
  function colMean(X) { var n = X.length, p = X[0].length, m = new Float64Array(p);
    for (var i = 0; i < n; i++) for (var j = 0; j < p; j++) m[j] += X[i][j];
    for (var j2 = 0; j2 < p; j2++) m[j2] /= n; return m; }
  function colStd(X, mean) { var n = X.length, p = X[0].length, s = new Float64Array(p);
    for (var i = 0; i < n; i++) for (var j = 0; j < p; j++) { var d = X[i][j] - mean[j]; s[j] += d * d; }
    for (var j2 = 0; j2 < p; j2++) s[j2] = Math.sqrt(s[j2] / Math.max(1, n)) || 1; return s; }
  function colMin(X) { var p = X[0].length, m = X[0].slice();
    for (var i = 1; i < X.length; i++) for (var j = 0; j < p; j++) if (X[i][j] < m[j]) m[j] = X[i][j]; return m; }
  function colMax(X) { var p = X[0].length, m = X[0].slice();
    for (var i = 1; i < X.length; i++) for (var j = 0; j < p; j++) if (X[i][j] > m[j]) m[j] = X[i][j]; return m; }
  function clone(X) { return X.map(function (r) { return r.slice(); }); }

  // ── preprocessing ops: {fit(Xtrain) -> state, apply(X, state)} ────────
  var OPS = {
    snv: { stateless: true, apply: function (X) {
      return X.map(function (r) { var m = 0, n = r.length; for (var i = 0; i < n; i++) m += r[i]; m /= n;
        var s = 0; for (var i2 = 0; i2 < n; i2++) { var d = r[i2] - m; s += d * d; } s = Math.sqrt(s / Math.max(1, n - 1)) || 1;
        return r.map(function (v) { return (v - m) / s; }); }); } },
    detrend: { stateless: true, apply: function (X) {
      var p = X[0].length, xs = []; for (var k = 0; k < p; k++) xs.push(k);
      var xm = (p - 1) / 2, sxx = 0; for (var k2 = 0; k2 < p; k2++) sxx += (k2 - xm) * (k2 - xm);
      return X.map(function (r) { var ym = 0; for (var i = 0; i < p; i++) ym += r[i]; ym /= p;
        var sxy = 0; for (var i2 = 0; i2 < p; i2++) sxy += (i2 - xm) * (r[i2] - ym); var b = sxy / (sxx || 1);
        return r.map(function (v, i3) { return v - (ym + b * (i3 - xm)); }); }); } },
    first_derivative: { stateless: true, apply: function (X) { return deriv(X, 1); } },
    second_derivative: { stateless: true, apply: function (X) { return deriv(X, 2); } },
    gaussian_filter: { stateless: true, apply: function (X, st, params) { return smooth(X, (params && params.sigma) || 2); } },
    savgol: { stateless: true, apply: function (X, st, params) {
      var win = (params && (params.window_length || params.window)) || 11;
      var poly = (params && (params.polyorder || params.order)) || 2;
      var der = (params && params.deriv) || 0; return savgol(X, win, poly, der); } },
    minmax: { fit: function (X) { return { mn: colMin(X), mx: colMax(X) }; },
      apply: function (X, st) { return X.map(function (r) { return r.map(function (v, j) {
        var d = st.mx[j] - st.mn[j]; return d > 1e-12 ? (v - st.mn[j]) / d : 0; }); }); } },
    standard_scaler: { fit: function (X) { var m = colMean(X); return { mean: m, std: colStd(X, m) }; },
      apply: function (X, st) { return X.map(function (r) { return r.map(function (v, j) { return (v - st.mean[j]) / st.std[j]; }); }); } },
    msc: { fit: function (X) { return { ref: colMean(X) }; },
      apply: function (X, st) { var ref = st.ref, p = ref.length, rm = 0; for (var k = 0; k < p; k++) rm += ref[k]; rm /= p;
        return X.map(function (r) { var xm = 0; for (var i = 0; i < p; i++) xm += r[i]; xm /= p;
          var sxy = 0, sxx = 0; for (var i2 = 0; i2 < p; i2++) { var dr = ref[i2] - rm, dx = r[i2] - xm; sxy += dr * dx; sxx += dr * dr; }
          var b = sxy / (sxx || 1) || 1; return r.map(function (v) { return (v - xm) / b + rm; }); }); } }
  };

  function deriv(X, order) { return X.map(function (r) { if (r.length < 3) return r.slice(); var out = r.slice();
    for (var o = 0; o < order; o++) { var nx = out.slice(); for (var i = 1; i < out.length - 1; i++) nx[i] = (out[i + 1] - out[i - 1]) / 2;
      nx[0] = out[1] - out[0]; nx[out.length - 1] = out[out.length - 1] - out[out.length - 2]; out = nx; } return out; }); }
  function smooth(X, sigma) { var rad = Math.max(1, Math.round(sigma * 2)), ker = [], s = 0;
    for (var k = -rad; k <= rad; k++) { var w = Math.exp(-(k * k) / (2 * sigma * sigma)); ker.push(w); s += w; }
    ker = ker.map(function (w) { return w / s; });
    return X.map(function (r) { return r.map(function (_v, i) { var acc = 0; for (var k2 = -rad; k2 <= rad; k2++) {
      var idx = Math.min(r.length - 1, Math.max(0, i + k2)); acc += r[idx] * ker[k2 + rad]; } return acc; }); }); }

  // Savitzky–Golay via least-squares convolution coefficients.
  function savgol(X, win, poly, der) {
    win = win % 2 === 0 ? win + 1 : win; var half = (win - 1) >> 1; poly = Math.min(poly, win - 1);
    var A = []; for (var i = -half; i <= half; i++) { var row = []; for (var j = 0; j <= poly; j++) row.push(Math.pow(i, j)); A.push(row); }
    // Solve (A^T A) c = A^T e_der for the central-row coefficients of the requested derivative.
    var ata = []; for (var a = 0; a <= poly; a++) { ata.push([]); for (var b = 0; b <= poly; b++) { var s = 0; for (var r = 0; r < win; r++) s += A[r][a] * A[r][b]; ata[a].push(s); } }
    var coeffs = [];
    for (var pt = 0; pt < win; pt++) {
      var rhs = []; for (var a2 = 0; a2 <= poly; a2++) rhs.push(A[pt][a2]);
      var sol = solveSym(ata.map(function (r) { return r.slice(); }), rhs.slice());
      // coefficient for derivative `der` = der! * sol[der]
      var fact = 1; for (var f = 2; f <= der; f++) fact *= f;
      coeffs.push(der < sol.length ? fact * sol[der] : 0);
    }
    return X.map(function (r) { return r.map(function (_v, i) { var acc = 0; for (var k = -half; k <= half; k++) {
      var idx = Math.min(r.length - 1, Math.max(0, i + k)); acc += r[idx] * coeffs[k + half]; } return acc; }); });
  }
  function solveSym(M, b) { var n = b.length;
    for (var c = 0; c < n; c++) { var piv = c; for (var r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
      var t = M[c]; M[c] = M[piv]; M[piv] = t; var tb = b[c]; b[c] = b[piv]; b[piv] = tb; var d = M[c][c] || 1e-12;
      for (var r2 = 0; r2 < n; r2++) { if (r2 === c) continue; var f = M[r2][c] / d; for (var k = c; k < n; k++) M[r2][k] -= f * M[c][k]; b[r2] -= f * b[c]; } }
    var x = []; for (var i = 0; i < n; i++) x.push(b[i] / (M[i][i] || 1e-12)); return x; }

  // ── NIPALS PLS (single target) ────────────────────────────────────────
  function plsFit(X, y, nComp) {
    var n = X.length, p = X[0].length; nComp = Math.max(1, Math.min(nComp, n - 1, p));
    var xmean = colMean(X), ymean = 0; for (var i = 0; i < n; i++) ymean += y[i]; ymean /= n;
    var Xr = X.map(function (r) { return r.map(function (v, j) { return v - xmean[j]; }); });
    var yr = y.map(function (v) { return v - ymean; });
    var W = [], P = [], Q = [];
    for (var a = 0; a < nComp; a++) {
      var w = new Float64Array(p); for (var j = 0; j < p; j++) { var s = 0; for (var ii = 0; ii < n; ii++) s += Xr[ii][j] * yr[ii]; w[j] = s; }
      var wn = 0; for (var j2 = 0; j2 < p; j2++) wn += w[j2] * w[j2]; wn = Math.sqrt(wn) || 1; for (var j3 = 0; j3 < p; j3++) w[j3] /= wn;
      var t = new Float64Array(n); for (var i2 = 0; i2 < n; i2++) { var st = 0; for (var j4 = 0; j4 < p; j4++) st += Xr[i2][j4] * w[j4]; t[i2] = st; }
      var tt = 0; for (var i3 = 0; i3 < n; i3++) tt += t[i3] * t[i3]; tt = tt || 1e-12;
      var pv = new Float64Array(p); for (var j5 = 0; j5 < p; j5++) { var sp = 0; for (var i4 = 0; i4 < n; i4++) sp += Xr[i4][j5] * t[i4]; pv[j5] = sp / tt; }
      var q = 0; for (var i5 = 0; i5 < n; i5++) q += yr[i5] * t[i5]; q /= tt;
      for (var i6 = 0; i6 < n; i6++) { for (var j6 = 0; j6 < p; j6++) Xr[i6][j6] -= t[i6] * pv[j6]; yr[i6] -= t[i6] * q; }
      W.push(w); P.push(pv); Q.push(q);
    }
    return { xmean: xmean, ymean: ymean, W: W, P: P, Q: Q };
  }
  function plsPredict(model, X) {
    var p = model.xmean.length;
    return X.map(function (row) { var xc = new Float64Array(p); for (var j = 0; j < p; j++) xc[j] = row[j] - model.xmean[j];
      var yh = model.ymean;
      for (var a = 0; a < model.W.length; a++) { var w = model.W[a], pv = model.P[a]; var t = 0; for (var j2 = 0; j2 < p; j2++) t += xc[j2] * w[j2];
        for (var j3 = 0; j3 < p; j3++) xc[j3] -= t * pv[j3]; yh += t * model.Q[a]; } return yh; });
  }

  // ── run the feature pipeline (fit-on-train, apply to both) ────────────
  function runFeatures(plan, Xtr, Xte) {
    var tr = clone(Xtr), te = clone(Xte);
    (plan.features || []).forEach(function (step) { var op = OPS[step.op]; if (!op) return;
      if (op.stateless) { tr = op.apply(tr, null, step.params); te = op.apply(te, null, step.params); }
      else { var st = op.fit(tr); tr = op.apply(tr, st); te = op.apply(te, st); } });
    return { tr: tr, te: te };
  }
  function fitYScaler(kind, y) { if (kind === "minmax") { var mn = Math.min.apply(null, y), mx = Math.max.apply(null, y);
      return { f: function (v) { return (v - mn) / ((mx - mn) || 1); }, inv: function (v) { return v * ((mx - mn) || 1) + mn; } }; }
    if (kind === "standard_scaler") { var m = 0; for (var i = 0; i < y.length; i++) m += y[i]; m /= y.length;
      var s = 0; for (var i2 = 0; i2 < y.length; i2++) s += (y[i2] - m) * (y[i2] - m); s = Math.sqrt(s / Math.max(1, y.length)) || 1;
      return { f: function (v) { return (v - m) / s; }, inv: function (v) { return v * s + m; } }; }
    return { f: function (v) { return v; }, inv: function (v) { return v; } }; }

  // ── k-fold OOF cross-validation ───────────────────────────────────────
  function crossValidate(plan, X, y) {
    var n = X.length, k = Math.max(2, Math.min(plan.cv || 5, n));
    var nComp = (plan.model && plan.model.n_components) || 10;
    var pred = new Array(n);
    for (var f = 0; f < k; f++) {
      var trX = [], trY = [], teIdx = [];
      for (var i = 0; i < n; i++) { if (i % k === f) teIdx.push(i); else { trX.push(X[i]); trY.push(y[i]); } }
      if (trX.length < 3 || teIdx.length === 0) continue;
      var teX = teIdx.map(function (i) { return X[i]; });
      var fp = runFeatures(plan, trX, teX);
      var ys = fitYScaler(plan.yTransform, trY);
      var trYs = trY.map(ys.f);
      var model = plsFit(fp.tr, trYs, nComp);
      var yhs = plsPredict(model, fp.te);
      teIdx.forEach(function (gi, li) { pred[gi] = ys.inv(yhs[li]); });
    }
    return pred;
  }

  function metrics(y, yhat) {
    var n = 0, sse = 0, ym = 0, cnt = 0;
    for (var i = 0; i < y.length; i++) if (yhat[i] != null) { ym += y[i]; cnt++; } ym /= Math.max(1, cnt);
    var sst = 0; for (var i2 = 0; i2 < y.length; i2++) if (yhat[i2] != null) { var e = y[i2] - yhat[i2]; sse += e * e; sst += (y[i2] - ym) * (y[i2] - ym); n++; }
    var rmse = Math.sqrt(sse / Math.max(1, n));
    var r2 = sst > 0 ? 1 - sse / sst : NaN;
    var sd = Math.sqrt(sst / Math.max(1, n));
    return { rmse: rmse, r2: r2, rpd: (rmse > 0 && sst > 0) ? sd / rmse : NaN, n: n };
  }

  // ── SVG rendering ─────────────────────────────────────────────────────
  function fmt(v) { if (!isFinite(v)) return "—"; var a = Math.abs(v); return a >= 100 || a === 0 ? v.toFixed(1) : a >= 1 ? v.toFixed(3) : v.toPrecision(3); }
  function niceScale(lo, hi) { if (hi <= lo) hi = lo + 1; var span = hi - lo, pad = span * 0.06; return [lo - pad, hi + pad]; }
  function scatterSVG(meas, pred, target) {
    var W = 460, H = 360, pl = 56, pr = 16, pt = 18, pb = 44, pw = W - pl - pr, ph = H - pt - pb;
    var pts = []; for (var i = 0; i < meas.length; i++) if (pred[i] != null) pts.push([meas[i], pred[i]]);
    if (!pts.length) return "";
    var all = []; pts.forEach(function (q) { all.push(q[0], q[1]); });
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all), sc = niceScale(lo, hi);
    function sx(v) { return pl + (v - sc[0]) / (sc[1] - sc[0]) * pw; }
    function sy(v) { return pt + (1 - (v - sc[0]) / (sc[1] - sc[0])) * ph; }
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet"><title>parity</title>';
    s += '<rect x="' + pl + '" y="' + pt + '" width="' + pw + '" height="' + ph + '" rx="3" fill="#fff" stroke="' + GRID + '"></rect>';
    for (var g = 0; g <= 4; g++) { var fr = g / 4, gx = pl + fr * pw, gy = pt + fr * ph, gv = sc[0] + (1 - fr) * (sc[1] - sc[0]);
      s += '<line x1="' + pl + '" y1="' + gy.toFixed(1) + '" x2="' + (pl + pw) + '" y2="' + gy.toFixed(1) + '" stroke="' + GRIDS + '"></line>';
      s += '<text x="' + (pl - 7) + '" y="' + (gy + 3).toFixed(1) + '" text-anchor="end" font-size="10.5" fill="' + MUTED + '" font-family="monospace">' + fmt(gv) + '</text>';
      s += '<text x="' + gx.toFixed(1) + '" y="' + (H - 26) + '" text-anchor="middle" font-size="10.5" fill="' + MUTED + '" font-family="monospace">' + fmt(sc[0] + fr * (sc[1] - sc[0])) + '</text>'; }
    s += '<line x1="' + sx(sc[0]) + '" y1="' + sy(sc[0]) + '" x2="' + sx(sc[1]) + '" y2="' + sy(sc[1]) + '" stroke="' + FAINT + '" stroke-dasharray="5 4" stroke-width="1.3"></line>';
    pts.forEach(function (q) { s += '<circle cx="' + sx(q[0]).toFixed(1) + '" cy="' + sy(q[1]).toFixed(1) + '" r="3.4" fill="' + TEALS + '" fill-opacity="0.62" stroke="#fff" stroke-width="0.8"></circle>'; });
    s += '<text x="' + (pl + pw / 2) + '" y="' + (H - 7) + '" text-anchor="middle" font-size="11.5" fill="' + FAINT + '">measured ' + esc(target) + '</text>';
    s += '<text transform="translate(15 ' + (pt + ph / 2) + ') rotate(-90)" text-anchor="middle" font-size="11.5" fill="' + FAINT + '">predicted (OOF)</text>';
    s += '</svg>'; return s;
  }
  function residSVG(meas, pred, target) {
    var W = 460, H = 360, pl = 56, pr = 16, pt = 18, pb = 44, pw = W - pl - pr, ph = H - pt - pb;
    var xs = [], rs = []; for (var i = 0; i < meas.length; i++) if (pred[i] != null) { xs.push(meas[i]); rs.push(meas[i] - pred[i]); }
    if (!xs.length) return "";
    var xlo = Math.min.apply(null, xs), xhi = Math.max.apply(null, xs), xs2 = niceScale(xlo, xhi);
    var rm = Math.max.apply(null, rs.map(Math.abs)) || 1, rsc = [-rm * 1.1, rm * 1.1];
    function sx(v) { return pl + (v - xs2[0]) / (xs2[1] - xs2[0]) * pw; }
    function sy(v) { return pt + (1 - (v - rsc[0]) / (rsc[1] - rsc[0])) * ph; }
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet"><title>residuals</title>';
    s += '<rect x="' + pl + '" y="' + pt + '" width="' + pw + '" height="' + ph + '" rx="3" fill="#fff" stroke="' + GRID + '"></rect>';
    for (var g = 0; g <= 4; g++) { var fr = g / 4, gy = pt + fr * ph, gv = rsc[1] - fr * (rsc[1] - rsc[0]);
      s += '<line x1="' + pl + '" y1="' + gy.toFixed(1) + '" x2="' + (pl + pw) + '" y2="' + gy.toFixed(1) + '" stroke="' + GRIDS + '"></line>';
      s += '<text x="' + (pl - 7) + '" y="' + (gy + 3).toFixed(1) + '" text-anchor="end" font-size="10.5" fill="' + MUTED + '" font-family="monospace">' + fmt(gv) + '</text>'; }
    s += '<line x1="' + pl + '" y1="' + sy(0).toFixed(1) + '" x2="' + (pl + pw) + '" y2="' + sy(0).toFixed(1) + '" stroke="' + AMBER + '" stroke-width="1.3"></line>';
    for (var i2 = 0; i2 < xs.length; i2++) s += '<circle cx="' + sx(xs[i2]).toFixed(1) + '" cy="' + sy(rs[i2]).toFixed(1) + '" r="3.2" fill="' + TEAL + '" fill-opacity="0.55" stroke="#fff" stroke-width="0.7"></circle>';
    s += '<text x="' + (pl + pw / 2) + '" y="' + (H - 7) + '" text-anchor="middle" font-size="11.5" fill="' + FAINT + '">measured ' + esc(target) + '</text>';
    s += '<text transform="translate(15 ' + (pt + ph / 2) + ') rotate(-90)" text-anchor="middle" font-size="11.5" fill="' + FAINT + '">residual</text>';
    s += '</svg>'; return s;
  }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function pill(value, label) { return '<div class="replay-pill"><b>' + value + '</b><span>' + label + '</span></div>'; }

  function setStatus(cls, text) { var el = document.getElementById("replay-status"); if (el) { el.className = "replay-status " + cls; el.textContent = text; } }

  function run() {
    var ds = DATA.dataset, plan = DATA.plan;
    if (!plan.model) { setStatus("err", "no model in pipeline"); return; }
    setStatus("busy", "running " + (plan.cv || 5) + "-fold cross-validation…");
    setTimeout(function () {
      try {
        var X = ds.X, y = ds.y;
        var pred = crossValidate(plan, X, y);
        var m = metrics(y, pred);
        if (!m.n) { setStatus("err", "dataset too small to cross-validate (need at least " + ((plan.cv || 5) + 2) + " samples)"); return; }
        var r2s = isFinite(m.r2) ? m.r2.toFixed(3) : "—";
        var rpds = isFinite(m.rpd) ? m.rpd.toFixed(2) : "—";
        document.getElementById("replay-metrics").innerHTML =
          pill(fmt(m.rmse), "RMSE (cv)") + pill(r2s, "R² (cv)") + pill(rpds, "RPD") +
          pill(m.n, "samples") + pill((plan.model.n_components), "components");
        document.getElementById("replay-parity").innerHTML = scatterSVG(y, pred, ds.target);
        document.getElementById("replay-resid").innerHTML = residSVG(y, pred, ds.target);
        setStatus("done", "done · recomputed in your browser");
      } catch (e) { setStatus("err", "replay error: " + e.message); }
    }, 30);
  }

  var btn = document.getElementById("replay-run");
  if (btn) btn.addEventListener("click", run);
  if (document.readyState === "complete" || document.readyState === "interactive") setTimeout(run, 120);
  else window.addEventListener("DOMContentLoaded", function () { setTimeout(run, 120); });
})();
"""
