# Corrected Greenium Model Audit — Iterative Re-check

## Validation correction
During the iterative check I re-applied the YTM validity filter before estimation. The final results below use only YTM values between -100% and 100% before robust treatment, matching the existing project sanity rule. The earlier intermediate computation without this filter was discarded.

## 1. Delta measurement audit
The proposed temporal delta measurement does **not** have adequate source support as the primary specification.

- Multi-year ESG issuers checked: **1,706**
- Share with exactly one unique ESG score across issue years: **95.49%**
- Multi-year rating issuers checked: **707**
- Share with unchanged rating-set pattern: **82.32%**

The workbook has IssueYear, but it does not provide an independent historical observation date for the ESG score or rating. Therefore IssueYear should not be treated as the timestamp of those measures.

**Decision:** keep temporal delta models only as exploratory robustness; do not use them as the main model.

## 2. Credit-rating measurement correction
The old 1–5 mapping was removed because it imposed arbitrary distances. The primary credit-quality measure is now **Investment Grade status**:

- 1 = broad "Investment Grade" OR exact rating Baa3/BBB- or better
- 0 = broad "High Yield" OR exact rating below Baa3/BBB-
- missing/WD = excluded

A full notch mapping is reported only as sensitivity.

## 3. Why robust YTM estimation is needed
Main common sample:
- N = **6,600**
- Green bonds = **416**
- Issuers = **477**
- YTM min/max = **-100.00% / 80.49%**
- 0.5th / 99.5th percentile = **-14.84% / 9.12%**

Because the tails are extreme, the preferred estimator is Huber M-estimation, with issuer-clustered inference. Tukey, Hampel, trimming, winsorization, two-way clustering and wild bootstrap are used as checks.

## 4. Preferred robust results

### H1 — Green pricing differential
- coefficient = **1.81 bps**
- issuer-clustered p = **0.6555**
- two-way-clustered p = **0.6966**
- bootstrap 95% CI = **[-5.93, 9.68] bps**
- bootstrap p = **0.6501**

**Conclusion:** no robust evidence for H1 in this corrected model.

### H2 — ESG and YTM
ESG is standardized; the coefficient is per 1 SD increase.

- coefficient = **-3.06 bps per SD**
- issuer-clustered p = **0.0330**
- two-way-clustered p = **0.0480**
- bootstrap 95% CI = **[-5.81, -0.33] bps**
- bootstrap p = **0.0308**

**Conclusion:** H2 is supported in the preferred outlier-robust specification. Higher ESG is associated with lower YTM. This is associational, not causal.

### H3 — Credit quality and YTM
- Investment Grade coefficient = **-55.22 bps**
- issuer-clustered p = **0.00000042**
- two-way-clustered p = **0.00000047**
- bootstrap 95% CI = **[-75.57, -34.19] bps**
- bootstrap p = **0.00000027**

**Conclusion:** broad investment-grade status has strong support as a pricing control. However, the fine exact-notch sensitivity does not reproduce this effect, so do not describe this as a precise linear per-notch effect.

## 5. Moderation checks
Green × ESG is not statistically reliable. An issuer-fixed-effect Green × Investment Grade interaction can appear significant, but the main sample contains only **8 green high-yield observations** versus **408 green investment-grade observations**.

**Decision:** reject that apparent significance as sparse-cell instability. Do not claim moderation.

## 6. Final defensible position
1. H1: **not supported** in the corrected robust model.
2. H2: **supported as an ESG-level association with YTM** under Huber, two-way-clustered, and bootstrap checks.
3. H3: **supported for broad investment-grade status**, not for a precise notch slope.
4. Temporal delta ESG/rating should be moved to exploratory robustness, not the primary specification.
5. No model was retained simply because it produced p < .05; a tempting interaction result was explicitly rejected after checking cell support.
