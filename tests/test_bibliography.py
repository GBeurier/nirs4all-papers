# SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
from __future__ import annotations

from nirs4all_papers.bibliography import build_bibliography, latex_escape, reference_for, resolve_method


def test_resolve_method_synonyms():
    assert resolve_method("PLSRegression") == "pls"
    assert resolve_method("StandardNormalVariate") == "snv"
    assert resolve_method("MinMaxScaler") == "minmax"
    assert resolve_method("RandomForestRegressor") is None


def test_resolve_via_raw_fallback():
    assert resolve_method("Weird", "sklearn.cross_decomposition._pls.PLSRegression") == "pls"


def test_build_bibliography_dedupes_by_citation():
    # minmax and standard_scaler both cite Pedregosa (scikit-learn) -> one merged reference.
    refs, id_to_ref = build_bibliography(["minmax", "snv", "standard_scaler", "pls"])
    assert len(refs) == 3
    assert id_to_ref["minmax"] is id_to_ref["standard_scaler"]
    assert [r.number for r in refs] == [1, 2, 3]


def test_latex_escape_hash():
    out = latex_escape("10.1002/(SICI)1099-128X(199701)11:1<73::AID-CEM435>3.0.CO;2-#")
    assert r"\#" in out and out.count("#") == out.count(r"\#")


def test_to_bibtex_type_and_escaping():
    snv = reference_for("snv")
    bib = snv.to_bibtex()
    assert bib.startswith("@article{snv,")
    assert " and " in bib  # "; " author separator -> " and "
