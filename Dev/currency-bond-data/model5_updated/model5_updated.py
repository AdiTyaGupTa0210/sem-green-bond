#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def locate_input() -> Path:
    candidates = [
        ROOT / "all_currencies_combined.csv",
        ROOT.parent / "all_currencies_combined.csv",
        ROOT.parent.parent / "all_currencies_combined.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "all_currencies_combined.csv not found. Put it in Dev/currency-bond-data/."
    )


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("--", np.nan), errors="coerce")


def parse_tenor(value: object) -> float:
    if pd.isna(value):
        return np.nan
    m = re.search(r"(-?\d+(?:\.\d+)?)", str(value).replace(",", ""))
    return float(m.group(1)) if m else np.nan


def map_credit_rating(value: object) -> float:
    # Retain the repository's existing ordinal mapping so Model 5 remains
    # directly aligned with the corrected Model 6 matching logic.
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
    out["ESG_num"] = to_num(out["7. ESG"])
    out["Currency"] = out["5. Currency"].astype("string")
    out["Issuer_clean"] = out["Issuer"].astype("string")
    out["Seniority"] = out["14. Seniority"].astype("string")
    out["Instrument"] = out["Source Instrument Type"].astype("string")
    out["YTM_valid"] = out["YTM"].between(-100, 100)
    return out


def build_matched_greenium(d: pd.DataFrame) -> pd.DataFrame:
    """Corrected Model 5: direct matched greenium estimation."""
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

    mean_model = smf.ols("Greenium_bps ~ 1", data=trimmed).fit()
    used = mean_model.model.data.row_labels
    robust = mean_model.get_robustcov_results(
        cov_type="cluster", groups=trimmed.loc[used, "Issuer"]
    )
    mean_est = float(robust.params[0])
    mean_se = float(robust.bse[0])

    return pd.DataFrame([
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
    ])


def save_distribution(matches: pd.DataFrame) -> None:
    if matches.empty:
        return
    s = matches["Greenium_bps"].dropna()
    lo, hi = s.quantile([0.01, 0.99])
    clipped = s.clip(lo, hi)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(clipped, bins=60)
    ax.axvline(float(s.median()), linewidth=1.5)
    ax.axvline(0, linewidth=1)
    ax.set_xlabel("Matched greenium (bps): YTM_green - YTM_control")
    ax.set_ylabel("Matched green bonds")
    ax.set_title("Updated Model 5: matched greenium distribution")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model5_matched_greenium_distribution.png", dpi=180)
    plt.close(fig)


def write_report(summary: pd.DataFrame) -> None:
    sm = dict(zip(summary["metric"], summary["value"]))
    report = f"""# Updated Model 5 — Matched Greenium Model

The original Model 5 represented Greenium as a single-indicator ESG latent variable and used the contaminated Spread field. The corrected Model 5 replaces that construction with a direct matched yield differential.

## Definition

`Greenium = YTM_green - YTM_matched_conventional`

A negative value means the green bond has a lower yield than its matched conventional bond.

## Matching design

Each green bond is matched to a conventional bond from the same issuer, currency, seniority and instrument type, within ±1 issue year and ±2 years of tenor. The nearest candidate is selected using issue year, tenor, issue size and coupon, with same credit rating preferred where available.

## Results

- Matched pairs: {int(sm['matched_pairs']):,}
- Unique issuers: {int(sm['unique_issuers']):,}
- Median greenium: {sm['median_greenium_bps']:.3f} bps
- 1%-trimmed mean greenium: {sm['trimmed_1pct_mean_greenium_bps']:.3f} bps
- 95% issuer-clustered CI: [{sm['trimmed_1pct_ci95_low_bps']:.3f}, {sm['trimmed_1pct_ci95_high_bps']:.3f}] bps
- Share of matched green bonds with lower YTM: {sm['share_green_yield_lower']:.2%}

## Interpretation

The central matched greenium is close to zero. The trimmed mean is slightly negative, but its 95% confidence interval spans zero. Therefore, this matched-pair Model 5 does not support a large universal greenium; it is best interpreted as a robustness model that directly estimates the pricing differential using comparable bonds.
"""
    (OUTPUT_DIR / "model5_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    input_path = locate_input()
    raw = pd.read_csv(input_path, low_memory=False)
    data = prepare_data(raw)
    matches = build_matched_greenium(data)
    summary = summarize_greenium(matches)

    matches.to_csv(OUTPUT_DIR / "model5_matched_greenium.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "model5_results.csv", index=False)
    save_distribution(matches)
    write_report(summary)

    print("Updated Model 5 complete.")
    print(summary.to_string(index=False))
    print(f"Outputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
