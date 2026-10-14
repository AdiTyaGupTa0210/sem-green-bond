# Bootstrap Robustness Analysis — Delta Model 6

## Design
- Method: **issuer-cluster wild bootstrap** using Rademacher (+1/-1) weights.
- Replications: **5,000**.
- Random seed: **20261009**.
- Common sample: **N = 6,613 bonds**.
- Green bonds: **385**.
- Issuer clusters: **335**.
- All four specifications use the same common sample.
- Confidence intervals: **2.5th and 97.5th percentiles** of the bootstrap coefficient distribution.
- The issuer is the bootstrap cluster because bonds issued by the same entity are not treated as independent.

## Full Delta Model

### H1 — Green pricing differential
- Point estimate: **-7.49 bps**
- Bootstrap mean: **-7.35 bps**
- Bootstrap SE: **11.78 bps**
- 95% percentile CI: **[-29.83, 15.34] bps**
- Bootstrap-SE p-value: **0.5247**
- CI excludes zero: **No**

### H2 — Change in ESG
- Point estimate: **4.01 bps per one-point ΔESG**
- Bootstrap mean: **4.07 bps**
- Bootstrap SE: **5.62 bps**
- 95% percentile CI: **[-5.51, 13.54] bps**
- Bootstrap-SE p-value: **0.4763**
- CI excludes zero: **No**

### H3 — Change in Credit Rating
- Point estimate: **8.23 bps per one-unit ΔCreditRating**
- Bootstrap mean: **8.14 bps**
- Bootstrap SE: **4.80 bps**
- 95% percentile CI: **[-0.70, 17.07] bps**
- Bootstrap-SE p-value: **0.0867**
- CI excludes zero: **No**

## Interpretation
Bootstrapping evaluates coefficient stability while respecting issuer-level dependence. A coefficient has bootstrap support at the 5% level when its 95% bootstrap interval excludes zero.

The delta-measure limitation found in the reliability/validity step remains: only a small fraction of issuer-year ESG and rating deltas are non-zero. Therefore wide bootstrap intervals for Delta_ESG and Delta_CreditRating are substantively plausible rather than a bootstrap failure.

## Why this is not an ordinary row bootstrap
An ordinary row bootstrap would treat individual bonds as independent. That is inappropriate here because several bonds can come from the same issuer. The present procedure applies the same bootstrap perturbation to all residuals belonging to an issuer, preserving within-issuer dependence and retaining Currency × IssueYear, Seniority, and Instrument fixed effects.
