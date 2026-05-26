{{
  config(
    materialized='incremental',
    unique_key='transaction_hk',
    tags=['link', 'transactions']
  )
}}

WITH source_data AS (
    SELECT
        transaction_hk,
        account_hk,
        transaction_id,
        transaction_datetime,
        amount,
        transaction_type,
        merchant,
        category,
        record_source,
        load_datetime
    FROM {{ ref('stg_transactions') }}
    {% if is_incremental() %}
        WHERE load_datetime > (SELECT COALESCE(MAX(load_datetime), '1900-01-01') FROM {{ this }})
    {% endif %}
)

SELECT * FROM source_data

-- Why use a T-Link for Banking?
-- Immutable Ledger: In banking, you never "update" a transaction. If a mistake is made, a second "reversal" transaction is created. The T-Link perfectly mirrors this real-world accounting practice.

-- Performance: By keeping the amount in the Link, you don't have to join a Satellite to see how much money moved. This makes balance aggregation (Sum of Amounts) extremely fast in Snowflake.

-- Auditability: Every row contains the RECORD_SOURCE. If there is a discrepancy in the ledger, you can trace the specific transaction back to the exact S3 file it arrived in.
