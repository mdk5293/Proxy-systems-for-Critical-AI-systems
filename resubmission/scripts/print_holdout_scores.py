import json

path = r"resubmission/results/holdout/repository_disjoint_holdout_v1_1_pairwise_scored.json"

with open(path, encoding="utf-8") as fh:
    payload = json.load(fh)

print(
    f"{'pair_id':22} "
    f"{'label':17} "
    f"{'meta':>7} "
    f"{'code':>7} "
    f"{'dyn':>7} "
    f"{'cross':>7}"
)

for row in payload["pairs"]:
    print(
        f"{row['pair_id']:22} "
        f"{row['label']:17} "
        f"{float(row['metadata_score']):7.2f} "
        f"{float(row['code_centric_score']):7.2f} "
        f"{float(row['dynamic_score']):7.2f} "
        f"{float(row['cross_language_score']):7.2f}"
    )
