{{
  config(
    materialized='incremental',
    unique_key='hub_customer_key',
    tags=['hub', 'customer']
  )
}}

{%- set source_model = ref('stg_customer') -%}

WITH source_data AS (
    SELECT DISTINCT
        customer_id,
        record_source,
        load_datetime
    FROM {{ source_model }}
    {% if is_incremental() %}
        WHERE load_datetime > (SELECT MAX(load_datetime) FROM {{ this }})
    {% endif %}
),

hashed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS hub_customer_key,
        customer_id,
        record_source,
        load_datetime
    FROM source_data
)

SELECT * FROM hashed
