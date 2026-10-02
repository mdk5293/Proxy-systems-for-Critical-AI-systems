from pathlib import Path
import re


path = Path("tools/score_labeled_benchmark_redux.py")

text = path.read_text(encoding="utf-8")

replacement = r'''def _github_side(pair: Dict[str, object]) -> Tuple[str, str]:
    """Return (query_url, target_url) for REDUX pair scoring.

    Distinct GitHub-to-GitHub known-match pairs are scored directly.
    Historical mirror pairs with a non-GitHub upstream retain GitHub
    self-comparison behavior for backward compatibility.
    """
    a = str(pair.get("repo_a_url", "")).strip()
    b = str(pair.get("repo_b_url", "")).strip()

    a_g = _norm_github(a)
    b_g = _norm_github(b)

    a_is_github = bool(
        re.match(r"https?://github\.com/[^/]+/[^/]+", a, re.I)
    )
    b_is_github = bool(
        re.match(r"https?://github\.com/[^/]+/[^/]+", b, re.I)
    )

    label = str(pair.get("label", ""))

    if label == "known_match" and a_is_github and b_is_github:
        return a_g, b_g

    if label == "known_match" and b_is_github:
        return b_g, b_g

    if a_is_github and b_is_github:
        return a_g, b_g

    if b_is_github:
        return b_g, b_g

    if a_is_github:
        return a_g, a_g

    raise ValueError(
        f"No GitHub URL for pair {pair.get('pair_id')}"
    )


'''

pattern = re.compile(
    r"def _github_side\(.*?\n(?=def _load_three_test)",
    re.DOTALL,
)

new_text, count = pattern.subn(replacement, text)

if count != 1:
    raise RuntimeError(
        f"Expected to replace exactly one _github_side function; replaced {count}"
    )

path.write_text(new_text, encoding="utf-8")

print("Patched:", path)
