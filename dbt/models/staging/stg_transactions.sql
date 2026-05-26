{{
  config(
    materialized='view',
    tags=['staging', 'transactions']
  )
}}

WITH source_data AS (
    {% if target.name == 'local' %}
    SELECT * FROM read_csv_auto('s3://raw-bucket/transactions/transactions.csv', HEADER=TRUE)
    {% else %}
    SELECT * FROM {{ source('raw_banking', 'transactions') }}
    {% endif %}
),

renamed AS (
    SELECT
        transaction_id,
        account_id,
        transaction_type,
        amount,
        CAST(transaction_date AS TIMESTAMP) AS transaction_datetime,
        CAST(NULL AS VARCHAR) AS merchant,
        CAST(NULL AS VARCHAR) AS category,
        '{{ var("source_system") }}' AS record_source,
        CURRENT_TIMESTAMP AS load_datetime,
        {{ dbt_utils.generate_surrogate_key(['transaction_id']) }} AS transaction_hk,
        {{ dbt_utils.generate_surrogate_key(['account_id']) }} AS account_hk
    FROM source_data
    WHERE transaction_id IS NOT NULL
)

SELECT * FROM renamed
