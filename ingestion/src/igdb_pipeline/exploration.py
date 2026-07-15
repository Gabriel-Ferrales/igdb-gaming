"""Reusable helpers for exploratory analysis of IGDB responses."""

from typing import Any

import pandas as pd

from igdb_pipeline.client import query_igdb


def query_endpoint(
    endpoint: str,
    fields: list[str],
    client_id: str,
    access_token: str,
    limit: int = 100,
    where: str | None = None,
    sort: str = "id asc",
) -> list[dict[str, Any]]:
    """Query an IGDB endpoint with a reusable field/filter interface.

    Args:
        endpoint: IGDB API endpoint name, such as ``"games"`` or ``"genres"``.
        fields: Field names to request from IGDB, such as ``["id", "name"]``.
        client_id: Twitch application client ID used to authenticate with IGDB.
        access_token: OAuth access token used to authenticate with IGDB.
        limit: Maximum number of records to request. Defaults to 100.
        where: Optional IGDB filter expression, without the ``where`` keyword or
            trailing semicolon. For example, ``"rating >= 80"``.
        sort: IGDB sort expression, without the ``sort`` keyword or trailing
            semicolon. Defaults to sorting by ID in ascending order.

    Returns:
        A list of dictionaries, where each dictionary represents one record
        returned by the requested IGDB endpoint.
    """

    query_parts = [
        f"fields {', '.join(fields)};",
        f"limit {limit};",
        f"sort {sort};",
    ]

    if where:
        query_parts.append(f"where {where};")

    query = "\n".join(query_parts)

    return query_igdb(
        endpoint=endpoint,
        query=query,
        client_id=client_id,
        access_token=access_token,
    )


def normalize_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert IGDB records into a normalized pandas DataFrame.

    Args:
        records: IGDB records, with one dictionary per record. Dictionaries may
            contain nested objects.

    Returns:
        A DataFrame containing one row per record. Nested dictionary keys are
        flattened into dot-separated column names by ``pandas.json_normalize``.
    """
    return pd.json_normalize(records)


def null_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the percentage of missing values in each DataFrame column.

    Args:
        df: DataFrame whose columns should be checked for missing values.

    Returns:
        A DataFrame indexed by the original column names, with one
        ``null_percentage`` column. Results are rounded to two decimal places
        and sorted from the highest missing-value percentage to the lowest.
    """
    return (
        df.isna()
        .mean()
        .mul(100)
        .round(2)
        .rename("null_percentage")
        .sort_values(ascending=False)
        .to_frame()
    )


def nested_column_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Describe the observed Python value types in each DataFrame column.

    Args:
        df: DataFrame whose columns should be inspected.

    Returns:
        A DataFrame with one row per input column. It includes pandas dtype,
        all observed Python value types, flags for list- and dictionary-valued
        columns, and the first non-null example. Empty columns use ``"empty"``
        as their observed type and ``None`` as the example.
    """
    rows: list[dict[str, Any]] = []

    for column in df.columns:
        non_null = df[column].dropna()

        rows.append(
            {
                "column": column,
                "pandas_dtype": str(df[column].dtype),
                "observed_types": ", ".join(
                    sorted({type(value).__name__ for value in non_null})
                )
                or "empty",
                "contains_list": any(
                    isinstance(value, (list, tuple)) for value in non_null
                ),
                "contains_dict": any(isinstance(value, dict) for value in non_null),
                "example": (non_null.iloc[0] if not non_null.empty else None),
            }
        )

    return pd.DataFrame(rows)


def convert_unix_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Add UTC datetime versions of selected Unix timestamp columns.

    Args:
        df: Source DataFrame containing Unix timestamps measured in seconds.
        columns: Names of columns to convert. Names that are not present in the
            DataFrame are ignored.

    Returns:
        A copy of ``df`` with a new ``<column>_utc`` column for every requested
        column that exists. Invalid timestamp values become ``NaT``. The input
        DataFrame is not modified.
    """
    result = df.copy()

    for column in columns:
        if column in result.columns:
            result[f"{column}_utc"] = pd.to_datetime(
                result[column],
                unit="s",
                utc=True,
                errors="coerce",
            )

    return result


def primary_key_summary(
    df: pd.DataFrame,
    key: str = "id",
) -> pd.DataFrame:
    """Summarize null and duplicate values for a candidate primary key.

    Args:
        df: DataFrame containing the candidate key.
        key: Name of the candidate primary-key column. Defaults to ``"id"``.

    Returns:
        A one-row DataFrame containing row count, null key count, duplicate key
        count, distinct non-null key count, and a Boolean ``is_valid`` result.

    Raises:
        KeyError: If ``key`` is not present in ``df``.
    """
    if key not in df.columns:
        raise KeyError(f"Column {key!r} is not present in the DataFrame")

    null_count = int(df[key].isna().sum())
    duplicate_count = int(df[key].dropna().duplicated().sum())

    return pd.DataFrame(
        [
            {
                "key": key,
                "row_count": len(df),
                "null_count": null_count,
                "duplicate_count": duplicate_count,
                "distinct_count": int(df[key].nunique(dropna=True)),
                "is_valid": null_count == 0 and duplicate_count == 0,
            }
        ]
    )


def field_availability_summary(
    df: pd.DataFrame,
    requested_fields: list[str],
) -> pd.DataFrame:
    """Report whether requested API fields appeared in normalized records.

    APIs such as IGDB may omit a property instead of returning it as null. A
    field can therefore be valid but absent from every record in a small sample.

    Args:
        df: Normalized response DataFrame.
        requested_fields: API field names that were requested.

    Returns:
        A DataFrame with one row per requested field and an ``is_returned`` flag
        indicating whether the field exists as a DataFrame column.
    """
    return pd.DataFrame(
        {
            "requested_field": requested_fields,
            "is_returned": [field in df.columns for field in requested_fields],
        }
    )


def relationship_coverage(
    source_df: pd.DataFrame,
    source_column: str,
    target_df: pd.DataFrame,
    target_column: str = "id",
) -> pd.DataFrame:
    """Measure how many sampled foreign-key values exist in a target sample.

    List-valued source cells are flattened before comparison; scalar values are
    compared directly. Null values are ignored.

    Args:
        source_df: DataFrame containing foreign-key references.
        source_column: Name of the scalar- or list-valued foreign-key column.
        target_df: DataFrame containing the referenced keys.
        target_column: Referenced key column. Defaults to ``"id"``.

    Returns:
        A one-row DataFrame with total and unique reference counts, matched and
        unmatched unique counts, and sampled coverage percentage. Coverage may
        be below 100% when independently limited endpoint samples are compared.

    Raises:
        KeyError: If a requested source or target column does not exist.
    """
    if source_column not in source_df.columns:
        raise KeyError(
            f"Column {source_column!r} is not present in the source DataFrame"
        )
    if target_column not in target_df.columns:
        raise KeyError(
            f"Column {target_column!r} is not present in the target DataFrame"
        )

    references: list[Any] = []
    for value in source_df[source_column].dropna():
        if isinstance(value, (list, tuple, set)):
            references.extend(value)
        else:
            references.append(value)

    unique_references = set(references)
    target_keys = set(target_df[target_column].dropna())
    matched = unique_references & target_keys
    unmatched = unique_references - target_keys
    coverage = (
        round(len(matched) / len(unique_references) * 100, 2)
        if unique_references
        else 100.0
    )

    return pd.DataFrame(
        [
            {
                "relationship": (f"{source_column} -> {target_column}"),
                "reference_count": len(references),
                "unique_reference_count": len(unique_references),
                "matched_unique_count": len(matched),
                "unmatched_unique_count": len(unmatched),
                "sample_coverage_percentage": coverage,
            }
        ]
    )
