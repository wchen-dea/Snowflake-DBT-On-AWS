{{
  config(
    materialized='view',
    tags=['staging', 'accounts']
  )
}}

WITH source_data AS (
    {% if target.name == 'local' %}
    SELECT * FROM read_csv_auto('s3://raw-bucket/accounts/accounts.csv', HEADER=TRUE)
    {% else %}
    SELECT * FROM {{ source('raw_banking', 'accounts') }}
    {% endif %}
),

renamed AS (
    SELECT
        account_id,
        customer_id,
        account_type,
        balance,
    CAST(NULL AS VARCHAR) AS currency,
    CAST('ACTIVE' AS VARCHAR) AS status,
    CAST(created_at AS DATE) AS opened_date,
        updated_at,
        '{{ var("source_system") }}' AS record_source,
        CURRENT_TIMESTAMP AS load_datetime,
        {{ dbt_utils.generate_surrogate_key(['account_id']) }} AS account_hk,
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_hk,
        {{ dbt_utils.generate_surrogate_key(['account_type', 'balance']) }} AS account_hashdiff
    FROM source_data
    WHERE account_id IS NOT NULL
)

SELECT * FROM renamed
