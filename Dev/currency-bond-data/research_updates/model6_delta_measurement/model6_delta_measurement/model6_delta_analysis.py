#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent
INPUT_CANDIDATES = [
    ROOT / "all_currencies_combined.csv",
    ROOT.parent / "all_currencies_combined.csv",
]
OUTPUT_DIR = ROOT / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def locate_input() -> Path:
    for p in INPUT_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("all_currencies_combined.csv not found.")


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("--", np.nan), errors="coerce")


def parse_tenor(value: object) -> float:
    if pd.isna(value):
        return np.nan
    m = re.search(r"(-?\d+(?:\.\d+)?)", str(value).replace(",", ""))
    return float(m.group(1)) if m else np.nan


def map_credit_rating(value: object) -> float:
    # Preserve the repository's existing ordinal mapping so that the only
    # substantive measurement change here is level -> delta.
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
    out["YTM_valid"] = out["YTM"].between(-100, 100)
    return out


def build_delta_measures(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Measurement-scale change:
      Delta_ESG_it    = ESG_i,t - ESG_i,t-
      Delta_Rating_it = Rating_i,t - Rating_i,t-

    t- is the issuer's previous observed issue year with a non-missing value.

    To avoid arbitrary ordering when an issuer has multiple bonds in one year,
    ESG and rating are first collapsed to issuer-year medians. The issuer-year
    delta is then merged back to every bond belonging to that issuer-year.
    """
    issuer_year = (
        d.dropna(subset=["Issuer_clean", "IssueYear_num"])
        .groupby(["Issuer_clean", "IssueYear_num"], as_index=False)
        .agg(
            ESG_level=("ESG_num", "median"),
            Rating_level=("CreditRating_ord", "median"),
            issuer_year_bonds=("Issuer_clean", "size"),
        )
        .sort_values(["Issuer_clean", "IssueYear_num"])
    )

    def previous_observed(group: pd.DataFrame, col: str) -> pd.DataFrame:
        prev_value = np.nan
        prev_year = np.nan
        values, years = [], []
        for value, year in zip(group[col], group["IssueYear_num"]):
            values.append(prev_value)
            years.append(prev_year)
            if pd.notna(value):
                prev_value = value
                prev_year = year
        return pd.DataFrame(
            {
                f"Prev_{col}": values,
                f"PrevYear_{col}": years,
            },
            index=group.index,
        )

    pieces = []
    for _, g in issuer_year.groupby("Issuer_clean", sort=False):
        x = g.copy()
        for col in ["ESG_level", "Rating_level"]:
            x = x.join(previous_observed(g, col))
        pieces.append(x)

    issuer_year = pd.concat(pieces).sort_index()

    issuer_year["Delta_ESG"] = (
        issuer_year["ESG_level"] - issuer_year["Prev_ESG_level"]
    )
    issuer_year["Delta_ESG_year_gap"] = (
        issuer_year["IssueYear_num"] - issuer_year["PrevYear_ESG_level"]
    )

    issuer_year["Delta_CreditRating"] = (
        issuer_year["Rating_level"] - issuer_year["Prev_Rating_level"]
    )
    issuer_year["Delta_CreditRating_year_gap"] = (
        issuer_year["IssueYear_num"] - issuer_year["PrevYear_Rating_level"]
    )

    # Optional annualized versions retained for robustness/future use.
    issuer_year["Delta_ESG_per_year"] = (
        issuer_year["Delta_ESG"] / issuer_year["Delta_ESG_year_gap"]
    )
    issuer_year["Delta_CreditRating_per_year"] = (
        issuer_year["Delta_CreditRating"]
        / issuer_year["Delta_CreditRating_year_gap"]
    )

    merge_cols = [
        "Issuer_clean",
        "IssueYear_num",
        "ESG_level",
        "Rating_level",
        "Delta_ESG",
        "Delta_CreditRating",
        "Delta_ESG_year_gap",
        "Delta_CreditRating_year_gap",
        "Delta_ESG_per_year",
        "Delta_CreditRating_per_year",
    ]
    out = d.merge(
        issuer_year[merge_cols],
        on=["Issuer_clean", "IssueYear_num"],
        how="left",
    )
    return out, issuer_year


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


BASE_FORMULA = (
    "YTM ~ Green + Certified + IssueSize_log + Tenor_years + Coupon "
    "+ C(CurrencyYear) + C(Seniority) + C(Instrument)"
)

BASE_REQUIRED = [
    "YTM",
    "Green",
    "Certified",
    "IssueSize_log",
    "Tenor_years",
    "Coupon",
    "CurrencyYear",
    "Seniority",
    "Instrument",
    "Issuer_clean",
]

SPECS = {
    "M6-Hygiene": ("", []),
    "M6 + ΔCredit Rating": (
        " + Delta_CreditRating",
        ["Delta_CreditRating"],
    ),
    "M6 + ΔESG": (" + Delta_ESG", ["Delta_ESG"]),
    "M6-Full Δ": (
        " + Delta_CreditRating + Delta_ESG",
        ["Delta_CreditRating", "Delta_ESG"],
    ),
}


def collect_result(name, model, sample, par, se, pv):
    row = {
        "model": name,
        "n": int(model.nobs),
        "green_n": int(sample.loc[model.model.data.row_labels, "Green"].sum()),
        "unique_issuers": int(
            sample.loc[model.model.data.row_labels, "Issuer_clean"].nunique()
        ),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "green_coef_bps": float(par["Green"] * 100.0),
        "green_se_bps": float(se["Green"] * 100.0),
        "green_p_value": float(pv["Green"]),
    }
    if "Delta_CreditRating" in par:
        row["delta_credit_rating_coef_bps_per_unit"] = float(
            par["Delta_CreditRating"] * 100.0
        )
        row["delta_credit_rating_p_value"] = float(pv["Delta_CreditRating"])
    if "Delta_ESG" in par:
        row["delta_esg_coef_bps_per_point"] = float(par["Delta_ESG"] * 100.0)
        row["delta_esg_p_value"] = float(pv["Delta_ESG"])
    return row


def run_maximum_sample_models(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, (extra_formula, extra_required) in SPECS.items():
        req = BASE_REQUIRED + extra_required
        sample = d.loc[
            d["YTM_valid"] & d[req].notna().all(axis=1)
        ].copy()
        model, par, se, pv = fit_clustered(sample, BASE_FORMULA + extra_formula)
        rows.append(collect_result(name, model, sample, par, se, pv))
    return pd.DataFrame(rows)


def run_common_sample_models(d: pd.DataFrame) -> pd.DataFrame:
    common_required = BASE_REQUIRED + [
        "Delta_CreditRating",
        "Delta_ESG",
    ]
    common = d.loc[
        d["YTM_valid"] & d[common_required].notna().all(axis=1)
    ].copy()

    rows = []
    for name, (extra_formula, _) in SPECS.items():
        model, par, se, pv = fit_clustered(common, BASE_FORMULA + extra_formula)
        rows.append(collect_result(name, model, common, par, se, pv))
    return pd.DataFrame(rows)


def build_diagnostics(d: pd.DataFrame, issuer_year: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("Total bond rows", len(d)),
        ("Issuer-year rows", len(issuer_year)),
        ("Issuer-years with ESG level", int(issuer_year["ESG_level"].notna().sum())),
        (
            "Issuer-years with ΔESG",
            int(issuer_year["Delta_ESG"].notna().sum()),
        ),
        (
            "Issuer-years with non-zero ΔESG",
            int((issuer_year["Delta_ESG"].dropna() != 0).sum()),
        ),
        (
            "Issuer-years with credit-rating level",
            int(issuer_year["Rating_level"].notna().sum()),
        ),
        (
            "Issuer-years with ΔCreditRating",
            int(issuer_year["Delta_CreditRating"].notna().sum()),
        ),
        (
            "Issuer-years with non-zero ΔCreditRating",
            int((issuer_year["Delta_CreditRating"].dropna() != 0).sum()),
        ),
        (
            "Bond rows usable for both delta variables",
            int(
                (
                    d["Delta_ESG"].notna()
                    & d["Delta_CreditRating"].notna()
                ).sum()
            ),
        ),
        (
            "Green bond rows usable for both delta variables",
            int(
                d.loc[
                    d["Delta_ESG"].notna()
                    & d["Delta_CreditRating"].notna(),
                    "Green",
                ].sum()
            ),
        ),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def main():
    input_path = locate_input()
    raw = pd.read_csv(input_path, low_memory=False)
    d = prepare_data(raw)
    d, issuer_year = build_delta_measures(d)

    max_results = run_maximum_sample_models(d)
    common_results = run_common_sample_models(d)
    diagnostics = build_diagnostics(d, issuer_year)

    max_results.to_csv(
        OUTPUT_DIR / "model6_delta_maximum_sample_results.csv", index=False
    )
    common_results.to_csv(
        OUTPUT_DIR / "model6_delta_common_sample_results.csv", index=False
    )
    diagnostics.to_csv(
        OUTPUT_DIR / "delta_measurement_diagnostics.csv", index=False
    )
    issuer_year.to_csv(
        OUTPUT_DIR / "issuer_year_delta_scores.csv", index=False
    )

    print("Maximum-sample models")
    print(max_results.to_string(index=False))
    print("\nCommon-sample models")
    print(common_results.to_string(index=False))
    print("\nDiagnostics")
    print(diagnostics.to_string(index=False))


if __name__ == "__main__":
    main()
