import csv as csv_module
import numpy as np
import pandas as pd
from io import StringIO


def _to_native(obj):
    """Recursively convert numpy types to plain Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (obj != obj):  # NaN
        return None
    return obj


def analyze_sales(csv_data: str, question: str = "") -> dict:
    """Analyze any CSV data and return rich insights."""
    # Strip UTF-8 BOM
    csv_data = csv_data.lstrip('﻿').lstrip('ï»¿')
    try:
        sample = csv_data[:4000]
        try:
            dialect = csv_module.Sniffer().sniff(sample, delimiters=',;\t|')
            sep = dialect.delimiter
        except Exception:
            sep = ','
        df = pd.read_csv(StringIO(csv_data), sep=sep)
    except Exception as e:
        return {"error": f"Failed to parse CSV: {e}"}

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]

    summary = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": df.columns.tolist(),
        "missing_values": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
        "numeric_summary": {},
        "categorical_summary": {},
        "sample_rows": df.head(5).to_dict(orient="records"),
    }

    for col in numeric_cols:
        s = df[col].dropna()
        summary["numeric_summary"][col] = {
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "std": round(float(s.std()), 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "sum": round(float(s.sum()), 2),
            "missing": int(df[col].isnull().sum()),
        }

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().round(2)
        pairs = []
        cols = corr.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if not (val != val):  # skip NaN correlations
                    pairs.append({
                        "col_a": cols[i],
                        "col_b": cols[j],
                        "correlation": round(float(val), 2),
                    })
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        summary["top_correlations"] = pairs[:10]

    for col in categorical_cols:
        counts = {str(k): int(v) for k, v in df[col].value_counts().head(10).items()}
        summary["categorical_summary"][col] = {
            "unique_values": int(df[col].nunique()),
            "top_values": counts,
        }

    for date_col in date_cols:
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            summary["date_range"] = {
                "column": date_col,
                "start": str(df[date_col].min().date()),
                "end": str(df[date_col].max().date()),
            }
            break
        except Exception:
            pass

    if categorical_cols and numeric_cols:
        grp_col = categorical_cols[0]
        num_col = numeric_cols[0]
        grouped = {
            str(k): round(float(v), 2)
            for k, v in df.groupby(grp_col)[num_col].mean().items()
        }
        summary["group_insight"] = {
            "grouped_by": grp_col,
            "metric": f"mean_{num_col}",
            "values": grouped,
        }

    return _to_native(summary)


TOOL_DEFINITION = {
    "name": "analyze_sales",
    "description": (
        "Analyze any CSV data — sales, products, cars, surveys, etc. "
        "Returns numeric stats (mean, median, std, min, max), categorical value counts, "
        "top correlations, group-by insights, and sample rows. "
        "Use this whenever the user uploads a CSV file or asks for data analysis."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_data": {
                "type": "string",
                "description": "Raw CSV content as a string.",
            },
            "question": {
                "type": "string",
                "description": "Optional specific question about the data.",
            },
        },
        "required": ["csv_data"],
    },
}
