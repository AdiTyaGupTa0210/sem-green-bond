# Model 6 — Delta Measurement Scale for Credit Rating and ESG

## Change implemented

The absolute-level variables `CreditRating_ord` and `ESG_num` are no longer used as the Model 6 extensions in this version.

They are replaced by:

- `Delta_CreditRating = current issuer-year rating level − previous observed issuer-year rating level`
- `Delta_ESG = current issuer-year ESG level − previous observed issuer-year ESG level`

To avoid arbitrary ordering when an issuer has several bonds in the same year, the level is first collapsed to the **issuer-year median**, then the change from the issuer's previous observed year is calculated and merged back to the individual bond rows.

The repository's existing credit-rating ordinal mapping is preserved so the only substantive change is **level → delta**.

## Model specifications

- **M6-Hygiene**: Green + Certified + IssueSize_log + Tenor_years + Coupon + Currency×IssueYear FE + Seniority FE + Instrument FE
- **M6 + ΔCredit Rating**: Hygiene + Delta_CreditRating
- **M6 + ΔESG**: Hygiene + Delta_ESG
- **M6-Full Δ**: Hygiene + Delta_CreditRating + Delta_ESG

Issuer-clustered standard errors are retained.

## Maximum-sample results

| model               |     n |   green_n |   unique_issuers |   r_squared |   adj_r_squared |   green_coef_bps |   green_se_bps |   green_p_value |   delta_credit_rating_coef_bps_per_unit |   delta_credit_rating_p_value |   delta_esg_coef_bps_per_point |   delta_esg_p_value |
|:--------------------|------:|----------:|-----------------:|------------:|----------------:|-----------------:|---------------:|----------------:|----------------------------------------:|------------------------------:|-------------------------------:|--------------------:|
| M6-Hygiene          | 74476 |      3078 |             9220 |    0.326789 |        0.324239 |        18.7972   |        6.79523 |      0.00568199 |                               nan       |                   nan         |                      nan       |          nan        |
| M6 + ΔCredit Rating | 21228 |       901 |              644 |    0.273671 |        0.265715 |        -2.06939  |        6.54253 |      0.751879   |                                 2.7437  |                     0.506683  |                      nan       |          nan        |
| M6 + ΔESG           | 16027 |       939 |             1344 |    0.404251 |        0.395653 |         0.852125 |        4.74321 |      0.857453   |                               nan       |                   nan         |                        9.05307 |            0.250027 |
| M6-Full Δ           |  6613 |       385 |              335 |    0.323883 |        0.301814 |        -7.49124  |       11.7418  |      0.523913   |                                 8.22548 |                     0.0922218 |                        4.00553 |            0.484616 |

## Common-sample results

| model               |    n |   green_n |   unique_issuers |   r_squared |   adj_r_squared |   green_coef_bps |   green_se_bps |   green_p_value |   delta_credit_rating_coef_bps_per_unit |   delta_credit_rating_p_value |   delta_esg_coef_bps_per_point |   delta_esg_p_value |
|:--------------------|-----:|----------:|-----------------:|------------:|----------------:|-----------------:|---------------:|----------------:|----------------------------------------:|------------------------------:|-------------------------------:|--------------------:|
| M6-Hygiene          | 6613 |       385 |              335 |    0.323784 |        0.301929 |         -8.00251 |        11.7965 |        0.497999 |                               nan       |                   nan         |                      nan       |          nan        |
| M6 + ΔCredit Rating | 6613 |       385 |              335 |    0.323878 |        0.301918 |         -7.47469 |        11.7417 |        0.524824 |                                 8.33211 |                     0.0874887 |                      nan       |          nan        |
| M6 + ΔESG           | 6613 |       385 |              335 |    0.323792 |        0.301829 |         -8.01451 |        11.7976 |        0.497398 |                               nan       |                   nan         |                        4.90899 |            0.33458  |
| M6-Full Δ           | 6613 |       385 |              335 |    0.323883 |        0.301814 |         -7.49124 |        11.7418 |        0.523913 |                                 8.22548 |                     0.0922218 |                        4.00553 |            0.484616 |

## Measurement diagnostics

| metric                                          |   value |
|:------------------------------------------------|--------:|
| Total bond rows                                 |  169320 |
| Issuer-year rows                                |   43471 |
| Issuer-years with ESG level                     |    8502 |
| Issuer-years with ΔESG                          |    5427 |
| Issuer-years with non-zero ΔESG                 |     151 |
| Issuer-years with credit-rating level           |    4193 |
| Issuer-years with ΔCreditRating                 |    3041 |
| Issuer-years with non-zero ΔCreditRating        |     242 |
| Bond rows usable for both delta variables       |   34907 |
| Green bond rows usable for both delta variables |     417 |

## Important interpretation

This delta specification is mechanically implemented, but the source workbook does not provide a separate historical observation date for ESG or credit rating. The delta construction therefore assumes that the score/rating attached to a bond can be associated with that bond's issue year.

The diagnostics also show limited within-issuer change: most observed delta values are zero. This means delta-based coefficients should be treated as a robustness / measurement-scale specification unless historical issuer-year ESG and rating snapshots are independently verified.

The optional annualized variables `Delta_ESG_per_year` and `Delta_CreditRating_per_year` are also generated in `issuer_year_delta_scores.csv` for a later robustness check when gaps between observed issuer years exceed one year.
