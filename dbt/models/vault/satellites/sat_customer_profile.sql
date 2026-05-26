{{
  config(
    materialized='incremental',
    unique_key=['hub_customer_key', 'load_datetime'],
    tags=['satellite', 'customer']
  )
}}

{%- set source_model = ref('stg_customer') -%}

WITH source_data AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS hub_customer_key,
        customer_name,
        email,
        phone,
        date_of_birth,
        record_source,
        load_datetime
    FROM {{ source_model }}
    {% if is_incremental() %}
        WHERE load_datetime > (SELECT MAX(load_datetime) FROM {{ this }})
    {% endif %}
),

-- Hash the payload to detect changes
hashed_payload AS (
    SELECT
        hub_customer_key,
        {{ dbt_utils.generate_surrogate_key([
            'customer_name',
            'email', 
            'phone',
            'date_of_birth'
        ]) }} AS hash_diff,
        customer_name,
        email,
        phone,
        date_of_birth,
        record_source,
        load_datetime
    FROM source_data
),

-- Only insert if hash_diff has changed
filtered AS (
    SELECT * FROM hashed_payload
    {% if is_incremental() %}
        WHERE NOT EXISTS (
            SELECT 1 FROM {{ this }} existing
            WHERE existing.hub_customer_key = hashed_payload.hub_customer_key
            AND existing.hash_diff = hashed_payload.hash_diff
        )
    {% endif %}
)

SELECT * FROM filtered
