# Reliability and Validity Assessment — Delta ESG and Delta Credit Rating

## Scope
This assessment is for the revised Model 6 measurement specification in which the absolute ESG and credit-rating levels are replaced by issuer-year change measures:

- Delta_ESG = current issuer-year ESG − previous observed issuer-year ESG
- Delta_CreditRating = current issuer-year rating score − previous observed issuer-year rating score

## 1. Internal-consistency reliability: not applicable
Cronbach's alpha, McDonald's omega, Composite Reliability (CR), and AVE were **not calculated**, because Delta_ESG and Delta_CreditRating are each single observed measures. Computing alpha/omega/CR from unrelated bond controls would be methodologically invalid.

## 2. Temporal reliability / stability

### ESG
- Consecutive issuer-year pairs: **5,427**
- Pearson lag correlation: **0.9995**
- Spearman lag correlation: **0.9997**
- ICC: **0.9996**
- Exact repeat rate: **97.22%**
- Mean absolute year-to-year change: **0.0205**

Interpretation: ESG is extremely stable across consecutive observed issuer-years. However, the exact-repeat rate is so high that this should not automatically be presented as strong measurement reliability; it may also indicate stale/repeated source values and explains why the delta measure has little variation.

### Credit rating
- Consecutive issuer-year pairs: **3,041**
- Spearman lag correlation: **0.8574**
- Quadratic weighted Cohen's kappa: **0.8762**
- ICC: **0.8459**
- Exact repeat rate: **92.04%**
- Mean absolute change: **0.1330**

Interpretation: the ordinal credit-rating measure shows strong temporal agreement.

## 3. Responsiveness of the delta scales

### Delta ESG
- Observed delta values: **5,427**
- Non-zero changes: **151**
- Non-zero share: **2.78%**

### Delta Credit Rating
- Observed delta values: **3,041**
- Non-zero changes: **242**
- Non-zero share: **7.96%**

Interpretation: both delta measures are highly zero-inflated, especially Delta_ESG. This substantially limits their ability to identify dynamic effects.

## 4. Discriminant validity / empirical distinctness
On issuer-years where both deltas are observed (N = **1,572**):
- Pearson correlation: **0.2117**, p = **2.189e-17**
- Spearman correlation: **0.0417**, p = **0.09835**
- VIF for Delta_ESG: **1.003**
- VIF for Delta_CreditRating: **1.009**

Interpretation: the two delta variables are not collinear and behave as empirically distinct controls. Formal HTMT/Fornell-Larcker validity is not applicable because these are not multi-item latent constructs.

## 5. Criterion / predictive validity against YTM
All comparisons use the same common sample (N = **6,613**).

- Hygiene R²: **0.323784**
- + Delta Credit Rating R²: **0.323878**; incremental R² = **0.000094**
- + Delta ESG R²: **0.323792**; incremental R² = **0.000008**
- Full Delta R²: **0.323883**; incremental R² = **0.000099**
- Joint clustered Wald test for Delta Rating and Delta ESG: **F = 1.6938, p = 0.1854**

Interpretation: the delta variables add very little incremental explanatory power for YTM in the current common sample. Therefore criterion/predictive validity for the delta specification is presently weak.

## 6. Overall assessment
- **Credit-rating reliability:** strong temporal agreement.
- **ESG temporal stability:** extremely high, but the near-constant values raise a data-responsiveness concern.
- **Discriminant distinctness:** acceptable; Delta_ESG and Delta_CreditRating are not redundant.
- **Predictive/criterion validity for YTM:** weak in the current delta specification.
- **Convergent validity / CR / AVE / alpha / omega:** cannot be validly tested with the current single-indicator measures.
- **Main limitation:** the workbook does not contain independently timestamped historical ESG/rating snapshots; delta values are aligned to bond IssueYear. This temporal assumption should be stated explicitly.

## Recommendation
Keep the delta specification as a robustness/dynamic-change model, but do not claim full scale reliability/construct validity yet. Formal measurement-model validation becomes appropriate only if multiple defensible indicators are collected (for example separate E, S and G components, and a richer credit-quality measurement block).
