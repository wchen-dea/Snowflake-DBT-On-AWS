{{
  config(
    materialized='incremental',
    unique_key=['account_hk', 'load_datetime'],
    tags=['satellite', 'account']
  )
}}

WITH source_data AS (
    SELECT
        account_hk,
        account_hashdiff,
        account_type,
        balance,
        record_source,
        load_datetime
    FROM {{ ref('stg_banking_accounts') }}
    {% if is_incremental() %}
        WHERE load_datetime > (SELECT COALESCE(MAX(load_datetime), '1900-01-01') FROM {{ this }})
    {% endif %}
),

filtered AS (
    SELECT *
    FROM source_data s
    {% if is_incremental() %}
    WHERE NOT EXISTS (
        SELECT 1
        FROM {{ this }} t
        WHERE t.account_hk = s.account_hk
          AND t.account_hashdiff = s.account_hashdiff
    )
    {% endif %}
)

SELECT * FROM filtered


-- Historical Accuracy: If a customer’s balance was $1,500.50 on January 15th and changed to $2,000.00 on February 1st, this table will hold both records. You can go back in time to see exactly what the balance was at any moment.

-- Storage Efficiency: If the balance doesn't change for six months, the src_hashdiff logic prevents dbt from inserting duplicate rows every day, keeping your Snowflake storage lean.

-- Regulatory Compliance: Banks are often required to show "Point-in-Time" states. This Satellite allows you to recreate the state of any account for any specific date for auditors.
