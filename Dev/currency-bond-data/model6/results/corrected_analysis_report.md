# Corrected Green-Bond Pricing Analysis

This run implements only the three agreed methodological corrections while keeping the original data concepts intact.

## Correction 1 — Spread validation

**Before:** `6. Spread` was used directly as a pricing predictor. In the supplied data, however, most populated spread values are exact copies of `Source Yield to Maturity`, so the variable is not an independent spread measure in those rows.

**After:** values equal to YTM are invalidated; obvious >5,000 bps unit/data errors are also excluded. Because cleaned spread coverage is extremely small, spread is not forced into the primary pricing model. It is retained as a diagnostic/robustness variable only.

- Numeric spread rows: 82,218
- Spread=YTM rows: 81,481
- Share of populated spread copied from YTM: 99.11%
- Usable cleaned spread rows: 733
- Green bonds with usable cleaned spread: 6

## Correction 2 — Greenium definition

**Before:** Greenium was represented as a single-indicator latent construct based on ESG.

**After:** Greenium is measured directly as `YTM_green − YTM_matched_conventional` in basis points. Each green bond is matched to a conventional bond from the same issuer, currency, seniority and instrument type, within ±1 issue year and ±2 years of tenor; the nearest candidate is selected on issue year, tenor, issue size and coupon, with same rating preferred where available.

- Matched green/conventional pairs: 1,660
- Unique issuers represented: 575
- Median matched greenium: -0.021 bps
- 1%-trimmed mean matched greenium: -0.303 bps
- 95% cluster-robust CI for trimmed mean: [-2.023, 1.417] bps

A negative value denotes a conventional greenium (green bond yields less than its matched conventional bond).

## Correction 3 — Multi-currency model with Currency × Year fixed effects

**Before:** the main SEM restricted the sample to INR, leaving 565 complete cases for the original six-variable SEM.

**After:** the corrected pricing models use all currencies while absorbing currency-specific interest-rate regimes through `Currency × IssueYear` fixed effects. Standard errors are clustered by issuer. Seniority and instrument type are also included as categorical controls; the repo's existing rating mapping is retained where rating is added.

### Regenerated Model 6 results

| Model | N | Green N | R² | Green effect (bps) | 95% CI (bps) | p-value |
|---|---:|---:|---:|---:|---:|---:|
| M6-Core | 74,476 | 3,078 | 0.327 | 18.80 | [5.48, 32.12] | 0.005682 |
| M6+Rating | 21,595 | 965 | 0.252 | -3.33 | [-15.64, 8.99] | 0.5966 |
| M6+ESG | 18,913 | 1,111 | 0.293 | -2.48 | [-16.65, 11.70] | 0.7323 |
| M6-Full | 6,675 | 416 | 0.308 | -11.66 | [-38.24, 14.92] | 0.3904 |

### Interpretation

The corrected framework is methodologically stronger because it no longer treats a copied YTM field as an independent spread, it measures greenium as an actual yield differential, and it uses substantially more green-bond observations without mixing monetary regimes naively. The different nested Model 6 specifications should be read as robustness checks rather than as attempts to select the numerically most favorable coefficient.

The matched analysis is especially important: it directly compares green bonds with economically similar conventional bonds from the same issuer. In this dataset the central matched greenium is close to zero, while raw means are sensitive to a small number of extreme yield differences; therefore median/trimmed estimates are more informative than the untrimmed mean.

## Files generated

- `model6_results.csv` — multi-currency fixed-effect pricing models
- `matched_greenium.csv` — row-level matched green/conventional pairs
- `matched_greenium_summary.csv` — greenium summary and robust interval
- `spread_quality_report.csv` — overall spread validation
- `spread_quality_by_source_sheet.csv` — spread problem by source sheet
- `model6_green_coefficients.png` — green coefficient comparison
- `matched_greenium_distribution.png` — matched greenium distribution

Input used: `all_currencies_combined.csv` (169,320 rows).