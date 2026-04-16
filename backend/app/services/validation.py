"""Dataset validation service — checks data quality and generates reports."""
import io
from typing import Any

import pandas as pd


def validate_dataset(data: bytes, format: str) -> dict[str, Any]:
    """Run quality checks on a dataset and return a validation report."""
    try:
        if format == "csv":
            df = pd.read_csv(io.BytesIO(data))
        elif format == "json":
            df = pd.read_json(io.BytesIO(data), lines=True)
        elif format == "parquet":
            df = pd.read_parquet(io.BytesIO(data))
        else:
            return {"valid": False, "errors": [f"Unsupported format: {format}"]}
    except Exception as e:
        return {"valid": False, "errors": [f"Failed to parse file: {str(e)}"]}

    issues = []
    warnings = []

    # Basic shape
    row_count = len(df)
    col_count = len(df.columns)

    if row_count == 0:
        issues.append("Dataset has no rows")
    if col_count == 0:
        issues.append("Dataset has no columns")

    # Check for duplicate columns
    dupes = df.columns[df.columns.duplicated()].tolist()
    if dupes:
        issues.append(f"Duplicate column names: {dupes}")

    # Check for entirely null columns
    null_cols = [col for col in df.columns if df[col].isnull().all()]
    if null_cols:
        warnings.append(f"Columns entirely null: {null_cols}")

    # Check for duplicate rows
    dupe_rows = df.duplicated().sum()
    if dupe_rows > 0:
        pct = (dupe_rows / row_count) * 100
        if pct > 50:
            issues.append(f"{dupe_rows} duplicate rows ({pct:.1f}% of data)")
        elif pct > 10:
            warnings.append(f"{dupe_rows} duplicate rows ({pct:.1f}% of data)")

    # Column-level quality
    column_reports = []
    for col in df.columns:
        col_report = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().mean() * 100, 1),
            "unique_count": int(df[col].nunique()),
            "unique_pct": round(df[col].nunique() / max(row_count, 1) * 100, 1),
        }

        # Check for high cardinality in string columns that might be IDs
        if df[col].dtype == "object" and col_report["unique_pct"] > 95:
            col_report["likely_id"] = True

        # Check for constant columns (only one value)
        if col_report["unique_count"] <= 1 and row_count > 1:
            warnings.append(f"Column '{col}' has only {col_report['unique_count']} unique value(s)")

        # Numeric stats
        if df[col].dtype in ("int64", "float64"):
            col_report["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
            col_report["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
            col_report["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
            col_report["median"] = float(df[col].median()) if not pd.isna(df[col].median()) else None
            col_report["std"] = float(df[col].std()) if not pd.isna(df[col].std()) else None

            # Check for potential outliers using IQR
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outlier_count = ((df[col] < q1 - 3 * iqr) | (df[col] > q3 + 3 * iqr)).sum()
                if outlier_count > 0:
                    col_report["outlier_count"] = int(outlier_count)
                    if outlier_count / row_count > 0.05:
                        warnings.append(f"Column '{col}' has {outlier_count} extreme outliers")

        column_reports.append(col_report)

    # Mixed type detection
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().head(100)
            numeric_count = sum(1 for v in sample if _is_numeric_string(str(v)))
            if 0 < numeric_count < len(sample) and numeric_count / len(sample) > 0.3:
                warnings.append(f"Column '{col}' has mixed types (some numeric, some text)")

    return {
        "valid": len(issues) == 0,
        "row_count": row_count,
        "column_count": col_count,
        "issues": issues,
        "warnings": warnings,
        "columns": column_reports,
        "quality_score": _compute_quality_score(issues, warnings, column_reports, row_count),
    }


def _is_numeric_string(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _compute_quality_score(
    issues: list, warnings: list, columns: list, row_count: int,
) -> int:
    """Compute a 0-100 quality score."""
    score = 100

    # Penalize issues heavily
    score -= len(issues) * 20

    # Penalize warnings moderately
    score -= len(warnings) * 5

    # Penalize high null rates
    for col in columns:
        if col["null_pct"] > 50:
            score -= 5
        elif col["null_pct"] > 20:
            score -= 2

    # Bonus for reasonable size
    if row_count >= 10:
        score = min(score + 5, 100)

    return max(0, min(100, score))
