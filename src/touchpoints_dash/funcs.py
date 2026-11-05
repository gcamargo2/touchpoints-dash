"""Provide helpers for loading BigQuery results into pandas DataFrames."""

from typing import Any

import numpy as np
import pandas as pd
import pandas_gbq
from google.cloud import bigquery
from pydantic import ConfigDict, validate_call


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def bigquery_to_dataframe(
    query_or_table: str,
    project_id: str,
    bigquery_client: bigquery.Client,
    *,
    qaqc: bool = True,
    use_bqstorage_api: bool = True,
    dtypes: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Bigquery to dataframe.

    Args:
        query_or_table: The BigQuery table ID or a SQL query to execute.
        project_id: The Google Cloud project ID.
        bigquery_client: An authenticated BigQuery client instance.
        qaqc: If True, remove duplicate rows and check for unique indexes.
        use_bqstorage_api: If True, use BigQuery Storage API.
        dtypes: data types.

    Returns:
        A pandas DataFrame with the query results or table data.
    """
    df = pandas_gbq.read_gbq(
        query_or_table=query_or_table,
        project_id=project_id,
        bigquery_client=bigquery_client,
        use_bqstorage_api=use_bqstorage_api,
        dtypes=dtypes,
    )

    # QAQC
    if qaqc:
        df_qaqc = df.drop_duplicates(
            subset=[
                c
                for c in df.columns
                if not df[c].map(lambda v: isinstance(v, np.ndarray)).any()
            ]
        )
        if df.shape[0] - df_qaqc.shape[0] > 0:
            print(
                f"Found {df.shape[0] - df_qaqc.shape[0]} duplicated rows when bigquery_to_dataframe functino ran on query: {query_or_table}."
            )
        assert df.shape[0] > 0, f"Empty dataframe from: {query_or_table}."
    return df
