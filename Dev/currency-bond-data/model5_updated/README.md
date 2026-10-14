# Updated Model 5 — Matched Greenium Model

This is the corrected replacement for the original Model 5 mediation specification.

## Why it was updated

The original Model 5 used:

- `Spread_log` as a predictor even though the supplied spread field is largely duplicated from YTM; and
- `Greenium =~ 1*ESG_num`, which treats ESG as though it were the greenium itself.

The corrected Model 5 instead estimates greenium directly:

`Greenium = YTM_green - YTM_matched_conventional`

## Matching variables

- same issuer
- same currency
- same seniority
- same instrument type
- issue year within ±1 year
- tenor within ±2 years
- nearest issue size
- nearest coupon
- same rating preferred where available

## Run

From `Dev/currency-bond-data`:

```powershell
.\.venv\Scripts\Activate.ps1
python model5_updated\model5_updated.py
```

The local `all_currencies_combined.csv` must remain in `Dev/currency-bond-data`; do not commit it.

## Verified results

- 1,660 matched green/conventional pairs
- 575 unique issuers
- median greenium: -0.021 bps
- 1%-trimmed mean: -0.303 bps
- 95% issuer-clustered CI: [-2.023, 1.417] bps
