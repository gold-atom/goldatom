#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "${script_dir}/../../../.." && pwd)
results_dir="${script_dir}/results"
shard_dir=$(mktemp -d)
trap 'rm -rf -- "${shard_dir}"' EXIT

cd "${repo_root}"
common=(
  --historical-summary "${results_dir}/historical-summary.json"
  --historical-targets "${results_dir}/historical-targets.json"
)
scenario_pairs=(
  "A-constant B-historical-ratios-then-plateau"
  "C-post-tip-plateau D-growth-0.95"
  "D-growth-0.75 D-growth-0.25"
  "E-decline-1.05 E-decline-1.25"
  "E-decline-4.0 F-eight-epoch-growth-burst"
  "G-alternating-clamps H-adaptive-lambda-half"
)

for index in "${!scenario_pairs[@]}"; do
  read -r first second <<<"${scenario_pairs[index]}"
  python3 "${script_dir}/policy_sim.py" "${common[@]}" \
    --scenario "${first}" --scenario "${second}" \
    --output-json "${shard_dir}/part-${index}.json" \
    --output-csv "${shard_dir}/part-${index}.csv"
done

python3 "${script_dir}/merge_policy_results.py" \
  "${shard_dir}/part-0.json" "${shard_dir}/part-1.json" \
  "${shard_dir}/part-2.json" "${shard_dir}/part-3.json" \
  "${shard_dir}/part-4.json" "${shard_dir}/part-5.json" \
  --output-json "${results_dir}/policy-simulation.json" \
  --output-csv "${results_dir}/policy-simulation.csv"
