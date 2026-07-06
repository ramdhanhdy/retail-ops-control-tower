"""Build verification analytics from intervention outcomes."""
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from retail_ops_control_tower.verification.analytics import generate_verification_report

def main():
    outcomes = pd.read_csv(ROOT / "data" / "sample" / "intervention_outcomes.csv")
    report = generate_verification_report(outcomes, injected_effect=0.30)
    output_path = ROOT / "data" / "processed" / "verification_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Written to {output_path}")
    print(f"Intervention: {report['resolution_rates']['intervention_rate']:.1%}")
    print(f"Control: {report['resolution_rates']['control_rate']:.1%}")
    print(f"Recovery: {report['recovery']['estimated_effect']:.1%} (injected: 30%)")

if __name__ == "__main__":
    main()
