"""Load and enrich touchpoint data and export it to Parquet."""

import pandas as pd

from touchpoints_dash.constants import prod_bigquery_client, prod_project_id
from touchpoints_dash.funcs import bigquery_to_dataframe

df = pd.read_excel(
    "/Users/gustavo.camargo/dev/gdg-analytics/src/gdg_analytics/analytics/collaborators/IversonJordan/year_2026/touchpoint_eda/input/notes_raw_july1_oct22.xlsx",
    parse_dates=["occurred_on", "created_time", "updated_time"],
    dtype={"user_id": "string"},
)

df["occurred_on"] = pd.to_datetime(df["occurred_on"], errors="coerce", format="mixed")


query_or_table = (
    "bcs-grower-analytics-wh-prod.fx_strategy.rag_risk_grower_accounts_2026-10-27"
)
rag_risk_grower_accounts = bigquery_to_dataframe(
    query_or_table=query_or_table,
    project_id=prod_project_id,
    bigquery_client=prod_bigquery_client,
)

rag_risk_grower_accounts["covered"] = rag_risk_grower_accounts["covered"].map(
    {True: "Covered", False: "Not Covered"}
)

df = df[df["account_id"].notna()].copy()

df = df.rename(columns={"account_id": "sf_account_id", "user_id": "cwid"})

c_plus_data = pd.read_parquet(
    "/Users/gustavo.camargo/dev/gdg-analytics/data/sfgi_acct.parquet"
)[["sap_id_c", "acct_id", "sfgi_smpl_id_val"]]
c_plus_data = c_plus_data.rename(columns={"acct_id": "sf_account_id"})


# Make a lookup from sfgi_smpl_id_val to sf_account_id (keep one row per id)
lookup = (
    c_plus_data.dropna(subset=["sfgi_smpl_id_val", "sf_account_id"])
    .drop_duplicates(subset=["sfgi_smpl_id_val"])
    .set_index("sfgi_smpl_id_val")["sf_account_id"]
)

rag_risk_grower_accounts["sf_account_id"] = rag_risk_grower_accounts[
    "sf_account_id"
].fillna(rag_risk_grower_accounts["ird_id"].map(lookup))


df = pd.merge(left=df, right=rag_risk_grower_accounts, how="left", on=["sf_account_id"])

employee_keys_query = """SELECT
    sales_organization_level_1_name AS employee,
    sales_organization_level_1_person_network_id AS cwid,
    sales_organization_level_3_code AS Unit,
    sales_organization_level_2_code AS Squad,
    sales_organization_level_1_code AS Territory,
    sales_organization_level_3_name AS `Business Unit Lead`,
    rgnl_brnd_fmly_desc AS Brand,
    sales_organization_level_1_role_description AS Role,
    sales_organization_level_3_description AS business_unit_name,
    sales_organization_level_4_code AS USS,
    sales_organization_level_5_description AS area
FROM
    `bcs-csw-na-pmds-bir-dm.bi_warehouse.bi_sales_org_dim`
WHERE
    version_number = 2027
    """
employee_keys = bigquery_to_dataframe(
    query_or_table=employee_keys_query,
    project_id=prod_project_id,
    bigquery_client=prod_bigquery_client,
    use_bqstorage_api=True,
    dtypes={"Territory": "string", "cwid": "string"},
)
employee_keys = employee_keys.drop_duplicates(subset="cwid")

df = pd.merge(left=df, right=employee_keys, on=["cwid"], how="left")
df["rag_segment"] = df["rag_segment"].fillna("RTM Partner")
df["covered"] = df["covered"].fillna("N/A")
df = df[df["Business Unit Lead"].notna()]

df.to_parquet(
    "/Users/gustavo.camargo/dev/touchpoints-dash/src/touchpoints_dash/data/touchpoint_data.parquet"
)
df = pd.read_parquet(
    "/Users/gustavo.camargo/dev/touchpoints-dash/src/touchpoints_dash/data/touchpoint_data.parquet"
)
