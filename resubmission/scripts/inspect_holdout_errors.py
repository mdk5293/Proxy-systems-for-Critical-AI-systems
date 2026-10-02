import json

path = r"resubmission/results/holdout/repository_disjoint_holdout_v1_1_pairwise_scored.json"

with open(path, encoding="utf-8") as fh:
    payload = json.load(fh)

methods = [
    "metadata",
    "code_centric",
    "dynamic",
    "cross_language",
]

for method in methods:
    key = method + "_score"

    print()
    print("=" * 72)
    print(method.upper())
    print("=" * 72)

    for row in payload["pairs"]:
        label = row["label"]
        score = float(row[key])

        strict_expected = None

        if label == "known_match":
            strict_expected = True
        elif label == "known_non_match":
            strict_expected = False

        lenient_expected = label in {
            "known_match",
            "known_related",
        }

        predicted = score >= 50.0

        strict_error = (
            strict_expected is not None
            and predicted != strict_expected
        )

        lenient_error = (
            predicted != lenient_expected
        )

        if strict_error or lenient_error:
            flags = []

            if strict_error:
                flags.append("STRICT")

            if lenient_error:
                flags.append("LENIENT")

            print(
                f"{row['pair_id']:22} "
                f"{label:17} "
                f"score={score:6.2f} "
                f"error={','.join(flags)}"
            )
