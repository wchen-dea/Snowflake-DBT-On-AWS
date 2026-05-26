{{
  config(
    materialized='view',
    tags=['staging', 'customers']
  )
}}

WITH source AS (
  {% if target.name == 'local' %}
  SELECT * FROM read_csv_auto('s3://raw-bucket/customers/customers.csv', HEADER=TRUE)
  {% else %}
  SELECT * FROM {{ source('raw_banking', 'customers') }}
  {% endif %}
),

renamed AS (
    SELECT
        -- Business Keys
        customer_id,
        
        -- Descriptive Attributes
    TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')) AS customer_name,
        LOWER(TRIM(email)) AS email,
    CAST(NULL AS VARCHAR) AS phone,
    CAST(NULL AS DATE) AS date_of_birth,
        
        -- Metadata
        created_at,
        updated_at,
        '{{ var("source_system") }}' AS record_source,
        CURRENT_TIMESTAMP AS load_datetime
        
    FROM source
    WHERE customer_id IS NOT NULL
)

SELECT * FROM renamed
