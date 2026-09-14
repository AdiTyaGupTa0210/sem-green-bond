#!/usr/bin/env python3
from __future__ import annotations

import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent
INPUT_CANDIDATES = [
    ROOT / "all_currencies_combined.csv",
    ROOT.parent / "all_currencies_combined.csv",
]
OUTPUT_DIR = ROOT / "corrected_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def locate_input() -> Path:
    for p in INPUT_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "all_currencies_combined.csv not found. Put it beside this script or one folder above it."
    )


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("--", np.nan), errors="coerce")


def parse_tenor(value: object) -> float:
    if pd.isna(value):
        return np.nan
    m = re.search(r"(-?\d+(?:\.\d+)?)", str(value).replace(",", ""))
    return float(m.group(1)) if m else np.nan


def map_credit_rating(value: object) -> float:
    # Keep the repository's existing ordinal logic so this change is not confounded
    # with a new rating methodology.
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    if not text or text == "--":
        return np.nan
    if "investment grade" in text:
        return 5.0
    if "baa" in text:
        return 2.0
    if "aa" in text:
        return 4.0
    if ("a1" in text or "a2" in text or "a3" in text) and "aa" not in text:
        return 3.0
    return 1.0


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["YTM"] = to_num(out["Source Yield to Maturity"])
    out["Spread_raw"] = to_num(out["6. Spread"])
    out["ESG_num"] = to_num(out["7. ESG"])
    out["IssueSize"] = to_num(out["1. Issue Size"])
    out["IssueSize_log"] = np.log1p(out["IssueSize"].clip(lower=0))
    out["Coupon"] = to_num(out["Source Coupon"])
    out["Tenor_years"] = out["3. Tenor"].map(parse_tenor)
    out["IssueYear_num"] = pd.to_numeric(out["Issue Year"], errors="coerce")
    out["CreditRating_ord"] = out["4. Credit Rating"].map(map_credit_rating)
    out["Green"] = (
        out["Source Green Bond"].astype(str).str.strip().str.lower().eq("yes")
    ).astype(int)
    out["Certified"] = (
        out["8. Certification Status"].astype(str).str.strip().str.lower().eq("yes")
    ).astype(int)

    out["Currency"] = out["5. Currency"].astype("string")
    out["Issuer_clean"] = out["Issuer"].astype("string")
    out["Seniority"] = out["14. Seniority"].astype("string")
    out["Instrument"] = out["Source Instrument Type"].astype("string")
    out["CurrencyYear"] = (
        out["Currency"].astype(str)
        + " × "
        + out["IssueYear_num"].round().astype("Int64").astype(str)
    )

    # CORRECTION 1: Spread validation.
    # In the supplied workbook, most populated spread cells are exact copies of YTM.
    # These cannot be interpreted as independent credit spreads and are invalidated.
    copied = np.isclose(
        out["Spread_raw"], out["YTM"], rtol=0.0, atol=1e-8, equal_nan=False
    )
    implausible = out["Spread_raw"].abs() > 5000  # remove obvious unit/data errors
    out["Spread_is_YTM_copy"] = copied
    out["Spread_clean_bps"] = out["Spread_raw"].mask(copied | implausible)

    # Minimal outcome sanity check: discard only obviously corrupted numeric yields.
    out["YTM_valid"] = out["YTM"].between(-100, 100)
    return out


def fit_clustered(data: pd.DataFrame, formula: str):
    base = smf.ols(formula, data=data).fit()
    used_idx = base.model.data.row_labels
    groups = data.loc[used_idx, "Issuer_clean"]
    robust = base.get_robustcov_results(cov_type="cluster", groups=groups)
    names = base.model.exog_names
    params = pd.Series(robust.params, index=names)
    ses = pd.Series(robust.bse, index=names)
    pvals = pd.Series(robust.pvalues, index=names)
    return base, params, ses, pvals


def run_pricing_models(d: pd.DataFrame) -> pd.DataFrame:
    base_formula = (
        "YTM ~ Green + Certified + IssueSize_log + Tenor_years + Coupon "
        "+ C(CurrencyYear) + C(Seniority) + C(Instrument)"
    )
    specs = {
        "M6-Core": ("", []),
        "M6+Rating": (" + CreditRating_ord", ["CreditRating_ord"]),
        "M6+ESG": (" + ESG_num", ["ESG_num"]),
        "M6-Full": (" + CreditRating_ord + ESG_num", ["CreditRating_ord", "ESG_num"]),
    }

    base_required = [
        "YTM", "Green", "Certified", "IssueSize_log", "Tenor_years", "Coupon",
        "CurrencyYear", "Seniority", "Instrument", "Issuer_clean",
    ]
    rows = []
    for name, (extra_formula, extra_required) in specs.items():
        req = base_required + extra_required
        sample = d.loc[d["YTM_valid"] & d[req].notna().all(axis=1)].copy()
        model, par, se, pv = fit_clustered(sample, base_formula + extra_formula)
        green_coef = float(par["Green"])
        green_se = float(se["Green"])
        rows.append({
            "model": name,
            "n": int(model.nobs),
            "green_n": int(sample.loc[model.model.data.row_labels, "Green"].sum()),
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "green_coef_pct_points": green_coef,
            "green_coef_bps": green_coef * 100.0,
            "green_se_bps": green_se * 100.0,
            "green_ci95_low_bps": (green_coef - 1.96 * green_se) * 100.0,
            "green_ci95_high_bps": (green_coef + 1.96 * green_se) * 100.0,
            "green_p_value": float(pv["Green"]),
            "certified_coef_bps": float(par["Certified"]) * 100.0,
            "certified_p_value": float(pv["Certified"]),
        })
    return pd.DataFrame(rows)


def build_spread_report(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    both = d["Spread_raw"].notna() & d["YTM"].notna()
    overall = pd.DataFrame([
        {
            "metric": "Total rows",
            "value": len(d),
        },
        {"metric": "Rows with numeric spread", "value": int(d["Spread_raw"].notna().sum())},
        {"metric": "Rows with numeric YTM and spread", "value": int(both.sum())},
        {"metric": "Spread exactly equals YTM", "value": int(d["Spread_is_YTM_copy"].sum())},
        {
            "metric": "Share of populated spread that equals YTM",
            "value": float(d["Spread_is_YTM_copy"].sum() / max(1, both.sum())),
        },
        {"metric": "Usable cleaned spread rows", "value": int(d["Spread_clean_bps"].notna().sum())},
        {
            "metric": "Usable cleaned spread rows that are green",
            "value": int(d.loc[d["Spread_clean_bps"].notna(), "Green"].sum()),
        },
    ])

    by_sheet = (
        d.groupby("Source Sheet", dropna=False)
        .agg(
            rows=("Source Sheet", "size"),
            numeric_spread=("Spread_raw", lambda s: int(s.notna().sum())),
            ytm_copy=("Spread_is_YTM_copy", "sum"),
            clean_spread=("Spread_clean_bps", lambda s: int(s.notna().sum())),
        )
        .reset_index()
    )
    by_sheet["copy_share_of_numeric_spread"] = (
        by_sheet["ytm_copy"] / by_sheet["numeric_spread"].replace(0, np.nan)
    )
    return overall, by_sheet


def build_matched_greenium(d: pd.DataFrame) -> pd.DataFrame:
    # CORRECTION 2: Greenium is a matched yield differential, not a latent ESG factor.
    required = [
        "YTM", "Issuer_clean", "Currency", "IssueYear_num", "Tenor_years",
        "IssueSize_log", "Coupon", "Seniority", "Instrument",
    ]
    clean = d.loc[d["YTM_valid"] & d[required].notna().all(axis=1)].copy()
    green = clean[clean["Green"] == 1].copy()
    conventional = clean[clean["Green"] == 0].copy()

    size_sd = float(clean["IssueSize_log"].std()) or 1.0
    coupon_sd = float(clean["Coupon"].std()) or 1.0

    groups = {
        key: g
        for key, g in conventional.groupby(
            ["Issuer_clean", "Currency", "Seniority", "Instrument"], sort=False
        )
    }

    matches: list[dict[str, object]] = []
    for idx, row in green.iterrows():
        cand = groups.get(
            (row["Issuer_clean"], row["Currency"], row["Seniority"], row["Instrument"])
        )
        if cand is None or cand.empty:
            continue
        cand = cand[(cand["IssueYear_num"] - row["IssueYear_num"]).abs() <= 1]
        cand = cand[(cand["Tenor_years"] - row["Tenor_years"]).abs() <= 2]
        if cand.empty:
            continue

        # Prefer the same ordinal rating if a comparable rated control exists.
        if pd.notna(row["CreditRating_ord"]):
            same_rating = cand[cand["CreditRating_ord"] == row["CreditRating_ord"]]
            if not same_rating.empty:
                cand = same_rating

        distance = (
            (cand["IssueYear_num"] - row["IssueYear_num"]).abs()
            + (cand["Tenor_years"] - row["Tenor_years"]).abs() / 2.0
            + (cand["IssueSize_log"] - row["IssueSize_log"]).abs() / size_sd
            + (cand["Coupon"] - row["Coupon"]).abs() / coupon_sd
        )
        control_idx = distance.idxmin()
        ctrl = cand.loc[control_idx]
        diff_pctpt = float(row["YTM"] - ctrl["YTM"])
        matches.append({
            "green_row": int(idx),
            "control_row": int(control_idx),
            "Issuer": row["Issuer_clean"],
            "Currency": row["Currency"],
            "Seniority": row["Seniority"],
            "Instrument": row["Instrument"],
            "IssueYear_green": row["IssueYear_num"],
            "IssueYear_control": ctrl["IssueYear_num"],
            "Tenor_green": row["Tenor_years"],
            "Tenor_control": ctrl["Tenor_years"],
            "IssueSize_log_green": row["IssueSize_log"],
            "IssueSize_log_control": ctrl["IssueSize_log"],
            "Coupon_green": row["Coupon"],
            "Coupon_control": ctrl["Coupon"],
            "YTM_green": row["YTM"],
            "YTM_control": ctrl["YTM"],
            "Greenium_pct_points": diff_pctpt,
            "Greenium_bps": diff_pctpt * 100.0,
            "match_distance": float(distance.loc[control_idx]),
            "Certified": int(row["Certified"]),
            "ESG_num": row["ESG_num"],
        })
    return pd.DataFrame(matches)


def summarize_greenium(matches: pd.DataFrame) -> pd.DataFrame:
    if matches.empty:
        return pd.DataFrame([{"metric": "matched_pairs", "value": 0}])
    s = matches["Greenium_bps"].dropna()
    lo, hi = s.quantile([0.01, 0.99])
    trimmed = matches[matches["Greenium_bps"].between(lo, hi)].copy()

    # Cluster-robust CI for the 1%-trimmed mean, clustering by issuer.
    mean_model = smf.ols("Greenium_bps ~ 1", data=trimmed).fit()
    used = mean_model.model.data.row_labels
    robust = mean_model.get_robustcov_results(
        cov_type="cluster", groups=trimmed.loc[used, "Issuer"]
    )
    mean_est = float(robust.params[0])
    mean_se = float(robust.bse[0])

    rows = [
        {"metric": "matched_pairs", "value": int(len(matches))},
        {"metric": "unique_issuers", "value": int(matches["Issuer"].nunique())},
        {"metric": "raw_mean_greenium_bps", "value": float(s.mean())},
        {"metric": "median_greenium_bps", "value": float(s.median())},
        {"metric": "share_green_yield_lower", "value": float((s < 0).mean())},
        {"metric": "p01_greenium_bps", "value": float(lo)},
        {"metric": "p99_greenium_bps", "value": float(hi)},
        {"metric": "trimmed_1pct_mean_greenium_bps", "value": mean_est},
        {"metric": "trimmed_1pct_cluster_se_bps", "value": mean_se},
        {"metric": "trimmed_1pct_ci95_low_bps", "value": mean_est - 1.96 * mean_se},
        {"metric": "trimmed_1pct_ci95_high_bps", "value": mean_est + 1.96 * mean_se},
    ]
    return pd.DataFrame(rows)


def save_figures(model_results: pd.DataFrame, matches: pd.DataFrame) -> None:
    # Green coefficient comparison
    x = np.arange(len(model_results))
    y = model_results["green_coef_bps"].to_numpy()
    low = model_results["green_ci95_low_bps"].to_numpy()
    high = model_results["green_ci95_high_bps"].to_numpy()
    yerr = np.vstack([y - low, high - y])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(x, y, yerr=yerr, fmt="o", capsize=4)
    ax.axhline(0, linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(model_results["model"], rotation=20, ha="right")
    ax.set_ylabel("Green coefficient (basis points of YTM)")
    ax.set_title("Corrected multi-currency pricing models: Green coefficient")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model6_green_coefficients.png", dpi=180)
    plt.close(fig)

    if not matches.empty:
        s = matches["Greenium_bps"].dropna()
        lo, hi = s.quantile([0.01, 0.99])
        clipped = s.clip(lo, hi)
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.hist(clipped, bins=60)
        ax.axvline(float(s.median()), linewidth=1.5)
        ax.axvline(0, linewidth=1)
        ax.set_xlabel("Matched greenium (bps): YTM_green - YTM_control")
        ax.set_ylabel("Matched green bonds")
        ax.set_title("Matched greenium distribution (display clipped at 1st/99th percentiles)")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "matched_greenium_distribution.png", dpi=180)
        plt.close(fig)


def write_report(
    input_path: Path,
    d: pd.DataFrame,
    spread_overall: pd.DataFrame,
    models: pd.DataFrame,
    greenium: pd.DataFrame,
) -> None:
    sm = dict(zip(spread_overall["metric"], spread_overall["value"]))
    gm = dict(zip(greenium["metric"], greenium["value"]))

    lines = [
        "# Corrected Green-Bond Pricing Analysis",
        "",
        "This run implements only the three agreed methodological corrections while keeping the original data concepts intact.",
        "",
        "## Correction 1 — Spread validation",
        "",
        "**Before:** `6. Spread` was used directly as a pricing predictor. In the supplied data, however, most populated spread values are exact copies of `Source Yield to Maturity`, so the variable is not an independent spread measure in those rows.",
        "",
        "**After:** values equal to YTM are invalidated; obvious >5,000 bps unit/data errors are also excluded. Because cleaned spread coverage is extremely small, spread is not forced into the primary pricing model. It is retained as a diagnostic/robustness variable only.",
        "",
        f"- Numeric spread rows: {int(sm['Rows with numeric spread']):,}",
        f"- Spread=YTM rows: {int(sm['Spread exactly equals YTM']):,}",
        f"- Share of populated spread copied from YTM: {float(sm['Share of populated spread that equals YTM']):.2%}",
        f"- Usable cleaned spread rows: {int(sm['Usable cleaned spread rows']):,}",
        f"- Green bonds with usable cleaned spread: {int(sm['Usable cleaned spread rows that are green']):,}",
        "",
        "## Correction 2 — Greenium definition",
        "",
        "**Before:** Greenium was represented as a single-indicator latent construct based on ESG.",
        "",
        "**After:** Greenium is measured directly as `YTM_green − YTM_matched_conventional` in basis points. Each green bond is matched to a conventional bond from the same issuer, currency, seniority and instrument type, within ±1 issue year and ±2 years of tenor; the nearest candidate is selected on issue year, tenor, issue size and coupon, with same rating preferred where available.",
        "",
        f"- Matched green/conventional pairs: {int(gm.get('matched_pairs', 0)):,}",
        f"- Unique issuers represented: {int(gm.get('unique_issuers', 0)):,}",
        f"- Median matched greenium: {float(gm.get('median_greenium_bps', float('nan'))):.3f} bps",
        f"- 1%-trimmed mean matched greenium: {float(gm.get('trimmed_1pct_mean_greenium_bps', float('nan'))):.3f} bps",
        f"- 95% cluster-robust CI for trimmed mean: [{float(gm.get('trimmed_1pct_ci95_low_bps', float('nan'))):.3f}, {float(gm.get('trimmed_1pct_ci95_high_bps', float('nan'))):.3f}] bps",
        "",
        "A negative value denotes a conventional greenium (green bond yields less than its matched conventional bond).",
        "",
        "## Correction 3 — Multi-currency model with Currency × Year fixed effects",
        "",
        "**Before:** the main SEM restricted the sample to INR, leaving 565 complete cases for the original six-variable SEM.",
        "",
        "**After:** the corrected pricing models use all currencies while absorbing currency-specific interest-rate regimes through `Currency × IssueYear` fixed effects. Standard errors are clustered by issuer. Seniority and instrument type are also included as categorical controls; the repo's existing rating mapping is retained where rating is added.",
        "",
        "### Regenerated Model 6 results",
        "",
        "| Model | N | Green N | R² | Green effect (bps) | 95% CI (bps) | p-value |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in models.iterrows():
        lines.append(
            f"| {r['model']} | {int(r['n']):,} | {int(r['green_n']):,} | {r['r_squared']:.3f} | "
            f"{r['green_coef_bps']:.2f} | [{r['green_ci95_low_bps']:.2f}, {r['green_ci95_high_bps']:.2f}] | {r['green_p_value']:.4g} |"
        )

    lines += [
        "",
        "### Interpretation",
        "",
        "The corrected framework is methodologically stronger because it no longer treats a copied YTM field as an independent spread, it measures greenium as an actual yield differential, and it uses substantially more green-bond observations without mixing monetary regimes naively. The different nested Model 6 specifications should be read as robustness checks rather than as attempts to select the numerically most favorable coefficient.",
        "",
        "The matched analysis is especially important: it directly compares green bonds with economically similar conventional bonds from the same issuer. In this dataset the central matched greenium is close to zero, while raw means are sensitive to a small number of extreme yield differences; therefore median/trimmed estimates are more informative than the untrimmed mean.",
        "",
        "## Files generated",
        "",
        "- `model6_results.csv` — multi-currency fixed-effect pricing models",
        "- `matched_greenium.csv` — row-level matched green/conventional pairs",
        "- `matched_greenium_summary.csv` — greenium summary and robust interval",
        "- `spread_quality_report.csv` — overall spread validation",
        "- `spread_quality_by_source_sheet.csv` — spread problem by source sheet",
        "- `model6_green_coefficients.png` — green coefficient comparison",
        "- `matched_greenium_distribution.png` — matched greenium distribution",
        "",
        f"Input used: `{input_path.name}` ({len(d):,} rows).",
    ]
    (OUTPUT_DIR / "corrected_analysis_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    input_path = locate_input()
    print(f"Loading: {input_path}")
    raw = pd.read_csv(input_path, low_memory=False)
    d = prepare_data(raw)

    spread_overall, spread_by_sheet = build_spread_report(d)
    spread_overall.to_csv(OUTPUT_DIR / "spread_quality_report.csv", index=False)
    spread_by_sheet.to_csv(OUTPUT_DIR / "spread_quality_by_source_sheet.csv", index=False)

    models = run_pricing_models(d)
    models.to_csv(OUTPUT_DIR / "model6_results.csv", index=False)

    matches = build_matched_greenium(d)
    matches.to_csv(OUTPUT_DIR / "matched_greenium.csv", index=False)
    greenium_summary = summarize_greenium(matches)
    greenium_summary.to_csv(OUTPUT_DIR / "matched_greenium_summary.csv", index=False)

    save_figures(models, matches)
    write_report(input_path, d, spread_overall, models, greenium_summary)

    print("\nModel 6 results:")
    print(models.to_string(index=False))
    print("\nMatched greenium summary:")
    print(greenium_summary.to_string(index=False))
    print(f"\nOutputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
