# Updated Model 5 — Matched Greenium Model

The original Model 5 represented Greenium as a single-indicator ESG latent variable and used the contaminated Spread field. The corrected Model 5 replaces that construction with a direct matched yield differential.

## Definition

`Greenium = YTM_green - YTM_matched_conventional`

A negative value means the green bond has a lower yield than its matched conventional bond.

## Matching design

Each green bond is matched to a conventional bond from the same issuer, currency, seniority and instrument type, within ±1 issue year and ±2 years of tenor. The nearest candidate is selected using issue year, tenor, issue size and coupon, with same credit rating preferred where available.

## Results

- Matched pairs: 1,660
- Unique issuers: 575
- Median greenium: -0.021 bps
- 1%-trimmed mean greenium: -0.303 bps
- 95% issuer-clustered CI: [-2.023, 1.417] bps
- Share of matched green bonds with lower YTM: 50.42%

## Interpretation

The central matched greenium is close to zero. The trimmed mean is slightly negative, but its 95% confidence interval spans zero. Therefore, this matched-pair Model 5 does not support a large universal greenium; it is best interpreted as a robustness model that directly estimates the pricing differential using comparable bonds.
