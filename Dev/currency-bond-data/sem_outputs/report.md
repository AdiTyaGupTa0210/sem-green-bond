# Indian Bond SEM Study


## Data preprocessing summary

INR rows: 25095 of 169320

Shared complete-case sample: 565 rows

                 best_factor  loading  communality  retain_as_indicator                               decision
YTM_log                   F2    0.990        0.981                 True                    retain as indicator
SourceCoupon              F1    0.978        0.958                 True                    retain as indicator
Spread_log                F3    0.332        0.193                False  drop from latent / treat as predictor
ESG_num                   F1    0.482        0.249                False  drop from latent / treat as predictor
CreditRating_ord          F3    0.495        0.389                False  drop from latent / treat as predictor
IssueSize_log             F3    0.802        0.660                 True                    retain as indicator


## EFA findings

### 2 factors

                     F1     F2
YTM_log           0.424  0.137
SourceCoupon      0.999 -0.022
Spread_log       -0.003 -0.388
ESG_num           0.524  0.124
CreditRating_ord -0.259  0.602
IssueSize_log     0.239  0.625

YTM_log             0.198
SourceCoupon        0.998
Spread_log          0.150
ESG_num             0.290
CreditRating_ord    0.430
IssueSize_log       0.448

### 3 factors

                     F1     F2     F3
YTM_log           0.024  0.990 -0.014
SourceCoupon      0.978  0.037  0.027
Spread_log        0.148 -0.246 -0.332
ESG_num           0.482  0.061  0.115
CreditRating_ord -0.369  0.093  0.495
IssueSize_log     0.124 -0.042  0.802

YTM_log             0.981
SourceCoupon        0.958
Spread_log          0.193
ESG_num             0.249
CreditRating_ord    0.389
IssueSize_log       0.660


## Model comparison

                           model  sample_n    CFI  RMSEA     Chi2  DoF     AIC     BIC  R2_BondPricing
Model 1 - Baseline Pricing Model       565 0.9285 0.1172  34.9648  4.0 11.8762 37.8972          0.3423
       Model 5 - Mediation Model       565 0.7064 0.2058 174.2785  7.0 27.3831 88.0986          0.9026
         Model 2 - Quality Model       565 0.7022 0.1733 179.4039 10.0 21.3649 69.0700          0.3445
            Model 4 - Full Model       565 0.6807 0.2147 188.9087  7.0 27.3313 88.0469          0.0000
        Model 3 - Greenium Model       565 0.3454 0.6402 464.2955  2.0 14.3565 49.0511          0.0127


## Final interpretation

The data support a strong pricing block around yield and coupon, but not a fully clean latent structure. Issuer quality is only partly supported: issue size behaves like the dominant indicator, while rating is weak. ESG is the weakest element in the measurement system and works better as a proxy predictor than a robust latent. Among the competing SEMs, the quality model is the least implausible compromise, but all models show non-trivial misfit, so the conclusions should be treated as exploratory rather than confirmatory.


## Decision logging

## Model 1 - Baseline Pricing Model

Establish the base market-risk and ESG mechanism.

CFI: 0.928, RMSEA: 0.117, R2(BondPricing): 0.342

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log    -0.027  0.493039
            BondPricing             ESG_num     0.583       0.0
                YTM_log         BondPricing     0.476         -
           SourceCoupon         BondPricing     0.902       0.0

       lval       rval  Est. Std   p-value
BondPricing Spread_log    -0.027  0.493039
BondPricing    ESG_num     0.583       0.0

## Model 2 - Quality Model

Test whether issuer strength adds explanatory power.

CFI: 0.702, RMSEA: 0.173, R2(BondPricing): 0.344

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log    -0.043  0.228441
            BondPricing             ESG_num     0.535       0.0
            BondPricing             Quality    -0.233  0.039596
                YTM_log         BondPricing     0.437         -
           SourceCoupon         BondPricing     0.982       0.0
       CreditRating_ord             Quality     1.000         -
          IssueSize_log             Quality     0.324  0.027988

       lval       rval  Est. Std   p-value
BondPricing Spread_log    -0.043  0.228441
BondPricing    ESG_num     0.535       0.0
BondPricing    Quality    -0.233  0.039596

## Model 3 - Greenium Model

Test a proxy greenium channel.

CFI: 0.345, RMSEA: 0.640, R2(BondPricing): 0.013

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log    -0.112   0.00944
            BondPricing            Greenium     0.010  0.996949
                YTM_log         BondPricing     0.967         -
           SourceCoupon         BondPricing     0.542  0.089807
                ESG_num            Greenium     0.017         -

       lval       rval  Est. Std   p-value
BondPricing Spread_log    -0.112   0.00944
BondPricing   Greenium     0.010  0.996949

## Model 4 - Full Model

Jointly test market risk, quality, and ESG.

CFI: 0.681, RMSEA: 0.215, R2(BondPricing): 0.000

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log     0.052  0.172962
            BondPricing             Quality    29.362  0.999968
            BondPricing            Greenium   -27.899  0.999968
                YTM_log         BondPricing     0.331         -
           SourceCoupon         BondPricing     1.000  0.000028
       CreditRating_ord             Quality     0.355         -
          IssueSize_log             Quality     1.000  0.010561
                ESG_num            Greenium     0.169         -

       lval       rval  Est. Std   p-value
BondPricing Spread_log     0.052  0.172962
BondPricing    Quality    29.362  0.999968
BondPricing   Greenium   -27.899  0.999968

## Model 5 - Mediation Model

Test whether issuer quality feeds into pricing through ESG.

CFI: 0.706, RMSEA: 0.206, R2(BondPricing): 0.903

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
               Greenium             Quality     0.352   0.00002
            BondPricing          Spread_log     0.039  0.288463
            BondPricing            Greenium     0.965       0.0
            BondPricing             Quality    -0.048  0.466857
                YTM_log         BondPricing     0.450         -
           SourceCoupon         BondPricing     0.956       0.0
       CreditRating_ord             Quality     0.324         -
          IssueSize_log             Quality     1.000  0.019304
                ESG_num            Greenium     0.585         -

            lval        rval  Est. Std   p-value
        Greenium     Quality     0.352   0.00002
     BondPricing  Spread_log     0.039  0.288463
     BondPricing    Greenium     0.965       0.0
     BondPricing     Quality    -0.048  0.466857
         YTM_log BondPricing     0.450         -
    SourceCoupon BondPricing     0.956       0.0
CreditRating_ord     Quality     0.324         -
   IssueSize_log     Quality     1.000  0.019304
         ESG_num    Greenium     0.585         -