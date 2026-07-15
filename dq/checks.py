"""Lightweight, dependency-free data-quality engine (Great Expectations style).

Reads a declarative suite from ``dq/expectations.yaml`` and validates a DataFrame,
emitting a machine-readable report and a non-zero exit code on failure so an
orchestrator (Airflow) can *gate* the pipeline on data quality.

Run:  python -m dq.checks --csv data/samples/reviews.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import pandas as pd
import yaml


def _run_check(df: pd.DataFrame, chk: dict) -> dict:
    col = chk.get("column")
    kind = chk["type"]
    total = len(df)
    unexpected = 0

    if kind == "not_null":
        unexpected = int(df[col].isna().sum())
    elif kind == "unique":
        unexpected = int(df[col].duplicated().sum())
    elif kind == "between":
        s = pd.to_numeric(df[col], errors="coerce")
        unexpected = int(((s < chk["min"]) | (s > chk["max"]) | s.isna()).sum())
    elif kind == "min_str_length":
        s = df[col].astype(str).str.strip()
        unexpected = int((s.str.len() < chk["min"]).sum())
    elif kind == "not_future":
        s = pd.to_datetime(df[col], errors="coerce").dt.date
        today = date.today()
        unexpected = int((s.isna() | (s > today)).sum())
    elif kind == "in_set":
        unexpected = int((~df[col].isin(chk["values"])).sum())
    else:
        raise ValueError(f"unknown check type: {kind}")

    return {
        "name": chk["name"],
        "type": kind,
        "column": col,
        "unexpected": unexpected,
        "total": total,
        "success": unexpected == 0,
    }


def validate(df: pd.DataFrame, suite_path: str = "dq/expectations.yaml") -> dict:
    suite = yaml.safe_load(open(suite_path, encoding="utf-8"))
    results = [_run_check(df, c) for c in suite["checks"]]
    passed = sum(r["success"] for r in results)
    return {
        "suite": suite["suite"],
        "rows": len(df),
        "checks_total": len(results),
        "checks_passed": passed,
        "success": passed == len(results),
        "results": results,
    }


def main():
    ap = argparse.ArgumentParser(description="Run the data-quality suite")
    ap.add_argument("--csv", default="data/samples/reviews.csv")
    ap.add_argument("--suite", default="dq/expectations.yaml")
    ap.add_argument("--report", default="dq/last_report.json")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    report = validate(df, args.suite)
    json.dump(report, open(args.report, "w", encoding="utf-8"), indent=2, default=str)

    print(f"Suite '{report['suite']}': {report['checks_passed']}/{report['checks_total']} passed on {report['rows']} rows")
    for r in report["results"]:
        mark = "PASS" if r["success"] else "FAIL"
        print(f"  [{mark}] {r['name']}: {r['unexpected']} unexpected")
    print("RESULT:", "ALL CHECKS PASSED" if report["success"] else "DATA QUALITY FAILED")
    sys.exit(0 if report["success"] else 1)


if __name__ == "__main__":
    main()
