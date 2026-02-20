#!/usr/bin/env python3
"""
Local PDF-to-recommendations analyzer for proxy system testing.

Reads reference PDFs + proxytool.ipynb, derives concept coverage, and emits:
  - analysis/recommendations.md
  - analysis/recommendations.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as stats
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class DocumentText:
    path: Path
    title: str
    pages: List[str]


@dataclass
class CodeSignal:
    kind: str
    label: str
    cell_idx: int
    snippet: str


TAXONOMY: Dict[str, Dict[str, object]] = {
    "physical_environment": {
        "description": "Similarity of operational environment (land/air/sea/space/cyber/medical).",
        "keywords": {
            "land": 2.0, "air": 2.0, "sea": 2.0, "space": 2.0, "cyber": 2.0, "medical": 2.0,
            "physical environment": 3.0, "operational environment": 3.0
        },
        "expected_code_signals": ["EnvironmentMetric", "env_"],
    },
    "application_purpose": {
        "description": "Similarity of mission/application purpose.",
        "keywords": {
            "application purpose": 3.0, "mission": 1.5, "purpose": 2.5, "domain": 1.0,
            "reasoning": 2.0, "planning": 2.0, "perception": 2.0, "nlp": 2.0, "robotics": 2.0
        },
        "expected_code_signals": ["PurposeMetric", "purpose_"],
    },
    "operational_characteristics": {
        "description": "Runtime characteristics, constraints, failure modes, and system behavior.",
        "keywords": {
            "operational characteristics": 3.0, "runtime": 1.5, "latency": 1.0,
            "reliability": 1.5, "safety": 2.0, "failure mode": 2.5,
            "misuse": 2.5, "edge case": 2.0
        },
        "expected_code_signals": ["risk", "criticality", "misuse", "operational_"],
    },
    "ai_ml_algorithms": {
        "description": "Algorithmic comparability of systems.",
        "keywords": {
            "algorithm": 2.5, "ai/ml": 2.0, "machine learning": 2.0,
            "deep learning": 2.0, "reinforcement": 2.0, "classifier": 1.0,
            "model": 1.5
        },
        "expected_code_signals": ["AlgorithmMetric", "algo_"],
    },
    "development_techniques": {
        "description": "Engineering process, collaboration, and development practices.",
        "keywords": {
            "development techniques": 3.0, "commit": 1.5, "collaboration": 1.0,
            "issue": 1.0, "cadence": 1.5, "churn": 1.5, "testing artifacts": 2.0
        },
        "expected_code_signals": ["CadenceMetric", "ChurnMetric", "AttachRateMetric", "GitLoggerMetrics"],
    },
    "proxy_vnv_process": {
        "description": "NIST proxy validation and verification process phases.",
        "keywords": {
            "five-phase process": 3.0, "validation and verification": 3.0,
            "proxy design process": 2.5, "use case": 1.5, "misuse case": 2.5,
            "criticality level": 2.0, "taxonomy template": 2.0
        },
        "expected_code_signals": ["vnv", "phase", "proxy_validation", "misuse_case"],
    },
}


def _clean_text(text: str) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _extract_pdf_with_pypdf(pdf_path: Path) -> Optional[List[str]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return None
    try:
        reader = PdfReader(str(pdf_path))
        pages: List[str] = []
        for page in reader.pages:
            pages.append(_clean_text(page.extract_text() or ""))
        return pages
    except Exception:
        return None


def _extract_pdf_with_pdftotext(pdf_path: Path) -> Optional[List[str]]:
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw = proc.stdout or ""
        if not raw.strip():
            return None
        pages = [_clean_text(p) for p in raw.split("\f")]
        return [p for p in pages if p]
    except Exception:
        return None


def _extract_pdf_fallback(pdf_path: Path) -> List[str]:
    # Last resort: decode bytes and keep readable chunks.
    try:
        data = pdf_path.read_bytes().decode("latin-1", errors="ignore")
    except Exception:
        return [""]
    chunks = re.findall(r"[A-Za-z][A-Za-z0-9 ,.;:()#\-/]{30,}", data)
    return [_clean_text("\n".join(chunks[:800]))]


def load_pdf_document(pdf_path: Path) -> DocumentText:
    pages = _extract_pdf_with_pypdf(pdf_path)
    if not pages or stats.fmean([len(p) for p in pages]) < 80:
        pages = _extract_pdf_with_pdftotext(pdf_path)
    if not pages:
        pages = _extract_pdf_fallback(pdf_path)
    title = pdf_path.name
    if pages:
        first = pages[0][:500]
        m = re.search(r"(?im)^\s*([A-Z][A-Za-z0-9 ,:\-]{12,120})\s*$", first)
        if m:
            title = m.group(1).strip()
    return DocumentText(path=pdf_path, title=title, pages=pages)


def _best_evidence_for_term(doc: DocumentText, term: str) -> Optional[Dict[str, object]]:
    t = term.lower()
    best: Optional[Tuple[int, int, str]] = None
    for i, page in enumerate(doc.pages, start=1):
        low = page.lower()
        c = low.count(t)
        if c <= 0:
            continue
        snippet = re.sub(r"\s+", " ", page[:260]).strip()
        if best is None or c > best[0]:
            best = (c, i, snippet)
    if not best:
        return None
    return {"doc": doc.path.name, "page": best[1], "term": term, "snippet": best[2]}


def compute_document_dimension_scores(documents: List[DocumentText]) -> Dict[str, Dict[str, object]]:
    all_text = "\n\n".join("\n".join(d.pages) for d in documents).lower()
    out: Dict[str, Dict[str, object]] = {}
    for dim, spec in TAXONOMY.items():
        keywords: Dict[str, float] = spec["keywords"]  # type: ignore
        weighted_hits = 0.0
        max_possible = sum(keywords.values())
        evidences: List[Dict[str, object]] = []
        for k, w in keywords.items():
            if k in all_text:
                weighted_hits += w
                for doc in documents:
                    ev = _best_evidence_for_term(doc, k)
                    if ev:
                        evidences.append(ev)
                        break
        score = weighted_hits / max(max_possible, 1.0)
        out[dim] = {
            "score": round(score, 4),
            "description": spec["description"],
            "evidence": evidences[:4],
        }
    return out


def load_notebook_code_cells(notebook_path: Path) -> List[str]:
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells: List[str] = []
    for c in nb.get("cells", []):
        if c.get("cell_type") != "code":
            continue
        src = c.get("source", [])
        if isinstance(src, list):
            code_cells.append("".join(src))
        else:
            code_cells.append(str(src))
    return code_cells


def extract_code_signals(code_cells: List[str]) -> List[CodeSignal]:
    signals: List[CodeSignal] = []
    for i, text in enumerate(code_cells):
        for cls in re.findall(r"class\s+([A-Za-z0-9_]+)\s*\(", text):
            if "Metric" in cls:
                line = next((ln.strip() for ln in text.splitlines() if f"class {cls}" in ln), f"class {cls}")
                signals.append(CodeSignal("class", cls, i, line[:200]))
        if "ALL_METRICS" in text:
            snippet = "\n".join(text.splitlines()[:25])
            signals.append(CodeSignal("registry", "ALL_METRICS", i, snippet[:400]))
        for feat in re.findall(r"\"([a-zA-Z_]+(?:_[a-zA-Z_]+)*)\"\s*:", text):
            if feat.startswith(("env_", "purpose_", "algo_", "sent_", "churn_", "commit_", "attach_")):
                signals.append(CodeSignal("feature", feat, i, feat))
    return signals


def compute_code_dimension_scores(signals: List[CodeSignal], code_cells: List[str]) -> Dict[str, Dict[str, object]]:
    corpus = "\n\n".join(code_cells).lower()
    signal_labels = [s.label for s in signals]
    out: Dict[str, Dict[str, object]] = {}
    for dim, spec in TAXONOMY.items():
        expected: List[str] = spec["expected_code_signals"]  # type: ignore
        hits = []
        for e in expected:
            found = e in signal_labels or e.lower() in corpus
            hits.append(1.0 if found else 0.0)
        score = (sum(hits) / max(len(expected), 1)) if expected else 0.0
        evidence = []
        for s in signals:
            if any(ex.lower() in (s.label.lower() + " " + s.snippet.lower()) for ex in expected):
                evidence.append(
                    {"cell_idx": s.cell_idx, "kind": s.kind, "label": s.label, "snippet": s.snippet[:220]}
                )
        out[dim] = {
            "score": round(score, 4),
            "description": spec["description"],
            "evidence": evidence[:4],
        }
    return out


def _priority_for_gap(gap: float) -> str:
    if gap >= 0.7:
        return "P1"
    if gap >= 0.45:
        return "P2"
    return "P3"


def build_recommendations(
    doc_scores: Dict[str, Dict[str, object]],
    code_scores: Dict[str, Dict[str, object]],
) -> List[Dict[str, object]]:
    recs: List[Dict[str, object]] = []
    for dim in TAXONOMY.keys():
        d = float(doc_scores[dim]["score"])
        c = float(code_scores[dim]["score"])
        gap = max(d - c, 0.0)
        if gap < 0.15:
            continue
        priority = _priority_for_gap(gap)
        if dim == "operational_characteristics":
            action = (
                "Add an operational-characteristics metric family (risk markers, safety/criticality,"
                " failure-mode mentions, and runtime constraints), then include it in ALL_METRICS."
            )
        elif dim == "proxy_vnv_process":
            action = (
                "Add explicit proxy V&V process outputs (phase coverage, use/misuse-case traceability,"
                " and criticality indicators) to align with NIST CSWP-31."
            )
        elif dim == "development_techniques":
            action = (
                "Expand development-technique coverage with workflow/process attributes beyond cadence/churn,"
                " such as test-artifact and validation-signal proxies from metadata."
            )
        else:
            action = f"Increase coverage depth for `{dim}` signals and normalize feature naming across metrics."
        recs.append(
            {
                "dimension": dim,
                "priority": priority,
                "gap": round(gap, 4),
                "impact": round(gap * 5, 2),
                "effort": "medium" if priority == "P1" else "low",
                "recommendation": action,
                "document_evidence": doc_scores[dim]["evidence"][:2],
                "code_evidence": code_scores[dim]["evidence"][:2],
            }
        )
    recs.sort(key=lambda r: r["gap"], reverse=True)
    return recs


def render_markdown_report(
    pdf_paths: List[Path],
    notebook_path: Path,
    doc_scores: Dict[str, Dict[str, object]],
    code_scores: Dict[str, Dict[str, object]],
    recommendations: List[Dict[str, object]],
) -> str:
    lines: List[str] = []
    lines.append("# PDF-to-Recommendations Analysis")
    lines.append("")
    lines.append("## Context and sources analyzed")
    for p in pdf_paths:
        lines.append(f"- `{p}`")
    lines.append(f"- Implementation analyzed: `{notebook_path}`")
    lines.append("")

    lines.append("## Coverage matrix by taxonomy dimension")
    lines.append("")
    lines.append("| Dimension | Doc signal score | Code coverage score | Gap |")
    lines.append("|---|---:|---:|---:|")
    for dim in TAXONOMY.keys():
        ds = float(doc_scores[dim]["score"])
        cs = float(code_scores[dim]["score"])
        gap = max(ds - cs, 0.0)
        lines.append(f"| `{dim}` | {ds:.2f} | {cs:.2f} | {gap:.2f} |")
    lines.append("")

    lines.append("## Prioritized improvizations")
    if not recommendations:
        lines.append("- No significant gaps detected by the configured thresholds.")
    for rec in recommendations:
        lines.append(
            f"- **{rec['priority']}** `{rec['dimension']}` (gap={rec['gap']:.2f}): {rec['recommendation']}"
        )
        doc_evs = rec.get("document_evidence", [])
        code_evs = rec.get("code_evidence", [])
        if doc_evs:
            ev = doc_evs[0]
            lines.append(
                f"  - Doc evidence: `{ev.get('doc')}` page {ev.get('page')} matched `{ev.get('term')}`"
            )
        if code_evs:
            cev = code_evs[0]
            lines.append(
                f"  - Code evidence: `proxytool.ipynb` code-cell {cev.get('cell_idx')} signal `{cev.get('label')}`"
            )
        else:
            lines.append("  - Code evidence: no direct signal found in current implementation.")
    lines.append("")

    lines.append("## Next implementation steps (manual)")
    lines.append("- Implement P1 items first, then rerun this analyzer to quantify gap reduction.")
    lines.append("- Keep metric names consistent to improve registry discoverability and report explainability.")
    lines.append("- Add tests/notebook checks that verify new metric keys appear in `ALL_METRICS` outputs.")
    lines.append("")
    return "\n".join(lines)


def validate_traceability(recommendations: List[Dict[str, object]]) -> List[str]:
    issues: List[str] = []
    for rec in recommendations:
        if not rec.get("document_evidence"):
            issues.append(f"{rec['dimension']}: missing document evidence")
        if "code_evidence" not in rec:
            issues.append(f"{rec['dimension']}: missing code evidence field")
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze reference PDFs and suggest proxytool improvements.")
    parser.add_argument(
        "--pdf",
        action="append",
        dest="pdfs",
        default=[],
        help="Path to a reference PDF (repeat --pdf for multiple files).",
    )
    parser.add_argument(
        "--notebook",
        default="proxytool.ipynb",
        help="Path to notebook implementation file.",
    )
    parser.add_argument(
        "--out-md",
        default="analysis/recommendations.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--out-json",
        default="analysis/recommendations.json",
        help="JSON evidence output path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.pdfs:
        raise SystemExit("Provide at least one --pdf path.")

    pdf_paths = [Path(p).expanduser() for p in args.pdfs]
    missing = [str(p) for p in pdf_paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing PDF files: {missing}")

    notebook_path = Path(args.notebook).expanduser()
    if not notebook_path.exists():
        raise SystemExit(f"Notebook not found: {notebook_path}")

    documents = [load_pdf_document(p) for p in pdf_paths]
    doc_scores = compute_document_dimension_scores(documents)

    code_cells = load_notebook_code_cells(notebook_path)
    signals = extract_code_signals(code_cells)
    code_scores = compute_code_dimension_scores(signals, code_cells)

    recommendations = build_recommendations(doc_scores, code_scores)
    traceability_issues = validate_traceability(recommendations)

    out_md = Path(args.out_md)
    out_json = Path(args.out_json)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    report_md = render_markdown_report(
        pdf_paths=pdf_paths,
        notebook_path=notebook_path,
        doc_scores=doc_scores,
        code_scores=code_scores,
        recommendations=recommendations,
    )
    out_md.write_text(report_md, encoding="utf-8")

    payload = {
        "sources": [str(p) for p in pdf_paths],
        "notebook": str(notebook_path),
        "doc_scores": doc_scores,
        "code_scores": code_scores,
        "recommendations": recommendations,
        "traceability_issues": traceability_issues,
    }
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote: {out_md}")
    print(f"Wrote: {out_json}")
    if traceability_issues:
        print("Traceability issues:")
        for issue in traceability_issues:
            print(f" - {issue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
