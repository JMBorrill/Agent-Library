import json
import shutil

import pytest

from agentlib.cli import main
from agentlib.frameworks import evidence, router


@pytest.fixture
def lib(tmp_path, root):
    (tmp_path / "sources").mkdir()
    shutil.copy(root / "sources" / "pdf-manifest.json", tmp_path / "sources")
    (tmp_path / "catalog").mkdir()
    cat = {
        "catalog_id": "nist-ssdf", "source_id": "nist-ssdf", "title": "t", "edition": "1.1",
        "extraction": {"method": "test", "date": "2026-10-13", "fidelity": "structural"},
        "items": [{"id": "PW.7.1", "text": "Review code", "citation": {"pdf_page": 24}},
                  {"id": "PO.1.1", "text": "Define reqs", "citation": {"pdf_page": 12}}],
    }
    (tmp_path / "catalog" / "nist-ssdf.json").write_text(json.dumps(cat))
    return tmp_path


def levels(findings):
    return [(f.level, f.message) for f in findings]


def test_valid_citation(lib):
    assert evidence.check_document("Code review is required [nist-ssdf PW.7.1, p. 24].", lib) == []


def test_unknown_source_and_page_range(lib):
    msgs = levels(evidence.check_document("[made-up 1.2, p. 3] and [nist-ssdf, p. 999]", lib))
    assert any("unknown source" in m for _, m in msgs)
    assert any("out of range" in m for _, m in msgs)


def test_page_disagrees_with_catalog(lib):
    msgs = levels(evidence.check_document("[nist-ssdf PW.7.1, p. 5]", lib))
    assert msgs and msgs[0][0] == "warning" and "p. 24" in msgs[0][1]


def test_hallucinated_identifier(lib):
    msgs = levels(evidence.check_document("We implement PW.9.9 and PO.1.1.", lib))
    assert any("PW.9.9" in m for _, m in msgs)
    assert not any("PO.1.1" in m for _, m in msgs)


def test_overclaim_and_code_blocks_ignored(lib):
    assert any("over-claim" in m for _, m in levels(evidence.check_document("The system is fully compliant.", lib)))
    assert evidence.check_document("```\nfully compliant PW.9.9\n```", lib) == []


def test_require_citations(lib):
    assert any("no source citations" in f.message for f in evidence.check_document("plain text", lib, require_citations=True))


def test_page_ranges_and_aliases(lib):
    assert evidence.check_document("[nasa-se-design 4.1, pp. 40-41]", lib) == []
    assert evidence.check_document("[nasa-se, pp. 40-999]", lib)


def test_link_only_source_accepted(lib):
    assert evidence.check_document("[nasa-software SWEHB 7.18, p. 1]", lib) == []


def test_grader_functions(root):
    ok, _ = evidence.grade_no_overclaim("We find evidence indicates conformance.", {})
    assert ok
    ok, _ = evidence.grade_no_overclaim("This is certified and guaranteed.", {})
    assert not ok


def test_cli_evidence_check(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text("Cited [nist-ssdf, p. 1].\n")
    assert main(["evidence", "check", str(doc)]) == 0
    doc.write_text("Cited [nist-ssdf, p. 999].\n")
    assert main(["evidence", "check", str(doc), "--format", "json"]) == 1
    assert '"citations": 1' in capsys.readouterr().out


def test_router_ranks_relevant_skill(root):
    skills = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    res = router.route("we need citations and an evidence audit trail for the assessment report")
    if "evidence-and-citation" in skills:
        assert res[0]["skill"] == "evidence-and-citation"
    for name, expected in [("green-book-appraisal", "business case NPV and optimism bias for public spending"),
                           ("owasp-asvs", "ASVS penetration test of a web application with OAuth"),
                           ("nist-ssdf", "SBOM and software supply chain attestation for our CI/CD pipeline"),
                           ("nist-ai-rmf", "AI risk assessment of an LLM chatbot for bias"),
                           ("nasa-systems-engineering", "prepare for PDR with a SEMP and trade study")]:
        if name in skills:
            assert router.route(expected)[0]["skill"] == name, expected


def test_router_phrase_boundaries():
    assert not router._phrase_hit("sca", " escalate ")
    assert router._phrase_hit("sca", " run sca daily ")


def test_asvs_identifier_forms(root):
    if not (root / "catalog" / "owasp-asvs-5.json").is_file():
        pytest.skip("ASVS catalog not present")
    assert evidence.check_document("Covers V6.2.1 and v5.0.0-6.2.1.", root) == []
    msgs = [f.message for f in evidence.check_document("Covers V6.99.1 and v5.0.0-6.99.2.", root)]
    assert any("V6.99.1" in m for m in msgs) and any("6.99.2" in m for m in msgs)
