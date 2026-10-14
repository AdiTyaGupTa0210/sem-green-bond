# Revised Greenium Analysis After Conceptual Corrections

## What was changed
1. All nested Green-coefficient models use the **same N=6,600 common sample** so coefficient movement is not caused by changing observations.
2. The decomposition adds controls sequentially to identify exactly where the raw Green effect disappears.
3. Certification is tested **with and without** because Green and Certified are strongly related and certification may absorb part of the Green-label effect.
4. Coupon is tested **with and without** because coupon is closely linked to bond pricing and can act as an aggressive pricing control.
5. A candidate H1 specification excluding Certification and Coupon is reported, while both variables remain in sensitivity models rather than being deleted opportunistically.
6. The matched-bond greenium analysis was rebuilt using **exact issuer, currency, seniority, instrument and Investment-Grade status**, plus issue-year and tenor calipers.
7. A true sovereign/swap benchmark-adjusted yield was **not fabricated** because the workbook does not contain the required external benchmark curve.

## Raw YTM comparison on the common sample
Green mean YTM = 3.4180%
Non-green mean YTM = 3.6746%
Raw Green minus non-green difference = -25.65 bps.

## Green-coefficient decomposition
                          step  green_coef_bps  green_p  weighted_R2
                 D0 Green only      -40.271060 0.029405     0.002864
         D1 + Currency×Year FE        4.409684 0.520309     0.841508
D2 + Seniority + Instrument FE        1.618565 0.765376     0.863083
             D3 + Size + Tenor        1.228209 0.632073     0.902512
           D4 + Credit quality        0.469919 0.835095     0.904586
                      D5 + ESG        0.427624 0.849491     0.904794
                   D6 + Coupon        1.201814 0.681712     0.913770
            D7 + Certification        1.809775 0.655505     0.913770

The decomposition identifies which controls account for the raw difference. Because the sample and robust weights are held fixed, movements in the Green coefficient are attributable to the added model terms rather than changing sample composition.

## Certification sensitivity
            model  green_coef_bps  green_p  certified_coef_bps  certified_p  weighted_R2
Without Certified        1.201814 0.681712                 NaN          NaN      0.91377
   With Certified        1.809775 0.655505           -0.695093     0.854554      0.91377

## Coupon sensitivity
         model  green_coef_bps  green_p  coupon_coef_bps  coupon_p  weighted_R2
Without Coupon        1.155783 0.805263              NaN       NaN     0.904795
   With Coupon        1.809775 0.655505        27.463494  0.000006     0.913770

## Candidate primary H1 model
Controls: issue size, tenor, ESG, Investment Grade status, Currency×Year FE, Seniority FE, Instrument FE.
Certification and Coupon are excluded from this one specification and reported separately as sensitivity checks.

Green coefficient = 0.43 bps
Issuer-clustered p = 0.8495
ESG coefficient = -3.86 bps per SD, p = 0.0089
Investment Grade coefficient = -76.72 bps, p = 9.344e-09

## Improved matched greenium
                                           method  pairs  issuers  mean_greenium_bps  median_greenium_bps  share_negative  bootstrap_ci95_low_bps  bootstrap_ci95_high_bps  bootstrap_mean_p_approx
Exact-stratum nearest neighbour, with replacement    680      121         -34.910268             -0.13345        0.510294              -95.151594                 0.599710                   0.0796
       Greedy nearest neighbour, no control reuse    653      121         -14.122911             -0.20000        0.519142              -38.256970                 0.888539                   0.1120

Negative greenium means the matched Green bond has a lower YTM than its comparable conventional bond.

## Benchmark-adjusted yield
A true benchmark-adjusted yield requires an external sovereign or swap curve matched by currency, observation/issue date, and maturity. The current workbook does not contain that information, so no pseudo-benchmark was invented. The matched-conventional-bond analysis above is the defensible within-dataset alternative.
