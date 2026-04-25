import pandas as pd
from io import StringIO


def analyze_campaign(csv_data: str, metric: str = "all") -> dict:
    """Analyze marketing campaign performance data from CSV."""
    try:
        df = pd.read_csv(StringIO(csv_data))
    except Exception as e:
        return {"error": f"Failed to parse CSV: {e}"}

    result = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": df.columns.tolist(),
        "metrics": {},
    }

    col_lower = {c.lower(): c for c in df.columns}

    def get_col(*names):
        for n in names:
            if n in col_lower:
                return col_lower[n]
        return None

    impressions_col = get_col("impressions", "views", "reach")
    clicks_col = get_col("clicks", "click")
    spend_col = get_col("spend", "cost", "budget", "amount")
    conversions_col = get_col("conversions", "conversion", "leads", "sales")
    revenue_col = get_col("revenue", "income", "value")

    if impressions_col:
        result["metrics"]["total_impressions"] = int(df[impressions_col].sum())

    if clicks_col:
        result["metrics"]["total_clicks"] = int(df[clicks_col].sum())

    if impressions_col and clicks_col:
        total_imp = df[impressions_col].sum()
        total_clicks = df[clicks_col].sum()
        result["metrics"]["ctr_percent"] = round(
            (total_clicks / total_imp * 100) if total_imp else 0, 2
        )

    if spend_col:
        result["metrics"]["total_spend"] = round(float(df[spend_col].sum()), 2)

    if spend_col and clicks_col:
        total_spend = df[spend_col].sum()
        total_clicks = df[clicks_col].sum()
        result["metrics"]["cpc"] = round(
            (total_spend / total_clicks) if total_clicks else 0, 2
        )

    if conversions_col:
        result["metrics"]["total_conversions"] = int(df[conversions_col].sum())

    if spend_col and conversions_col:
        total_spend = df[spend_col].sum()
        total_conv = df[conversions_col].sum()
        result["metrics"]["cpa"] = round(
            (total_spend / total_conv) if total_conv else 0, 2
        )

    if revenue_col and spend_col:
        total_rev = df[revenue_col].sum()
        total_spend = df[spend_col].sum()
        result["metrics"]["roas"] = round(
            (total_rev / total_spend) if total_spend else 0, 2
        )

    result["sample_rows"] = df.head(5).to_dict(orient="records")
    return result


TOOL_DEFINITION = {
    "name": "analyze_campaign",
    "description": (
        "Analyze marketing campaign performance from CSV data. Computes KPIs "
        "like CTR, CPC, CPA, ROAS, impressions, clicks, and conversions. "
        "Use this when the user asks about campaign effectiveness or ad performance."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_data": {
                "type": "string",
                "description": "Raw CSV content as a string.",
            },
            "metric": {
                "type": "string",
                "description": "Specific metric to focus on, or 'all' for full analysis.",
                "default": "all",
            },
        },
        "required": ["csv_data"],
    },
}
