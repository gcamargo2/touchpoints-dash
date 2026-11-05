"""Configure production BigQuery credentials and the shared client."""

# Credentials
from bayer_api.bayer_auth import get_gat_prod_bq_credential
from bayer_api.bigquery import gen_bigquery_client

prod_project_id = "bcs-grower-analytics-wh-prod"
gat_prod_bq_credential = get_gat_prod_bq_credential()


prod_bigquery_client = gen_bigquery_client(
    project=prod_project_id, credentials=gat_prod_bq_credential
)
