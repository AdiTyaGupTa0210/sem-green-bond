# Model 6 — Corrected Green Bond Pricing Analysis

This folder contains the corrected Model 6 implementation and outputs.

## Main outcome
Dependent variable: **Yield to Maturity (YTM)**.

## Main corrections
1. The original `6. Spread` field is not used as a primary predictor because most populated values duplicate YTM.
2. Greenium is treated as an actual green-vs-conventional yield differential rather than a latent ESG proxy.
3. The analysis uses the multi-currency sample with Currency × Issue Year fixed effects and issuer-clustered standard errors.

## Model 6 variants
- M6-Core
- M6 + Rating
- M6 + ESG
- M6-Full

For direct comparison, use `results/model6_common_sample_results.csv`, where all four specifications use the same N = 6,675 observations.

## Files
- `model6_analysis.py` — corrected analysis script
- `results/model6_common_sample_results.csv` — preferred like-for-like comparison
- `results/model6_maximum_data_results.csv` — largest available sample per specification
- `results/matched_greenium_summary.csv` — matched-pair robustness summary
- `results/corrected_analysis_report.md` — corrected analysis report
- `results/Model6_Results_and_Diagram.docx` — final results/diagram document

The local input file `all_currencies_combined.csv` remains excluded from Git and should stay local.
