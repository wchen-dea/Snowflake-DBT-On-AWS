{{
  config(
    materialized='table',
    tags=['marts', 'customer_360']
  )
}}

WITH customer_profile_ranked AS (
    SELECT
        hub.hub_customer_key,
        hub.customer_id,
        sat.customer_name,
        sat.email,
        sat.phone,
        sat.date_of_birth,
        ROW_NUMBER() OVER (
            PARTITION BY hub.hub_customer_key
            ORDER BY sat.load_datetime DESC
        ) AS profile_rank
    FROM {{ ref('hub_customer') }} hub
    LEFT JOIN {{ ref('sat_customer_profile') }} sat
        ON hub.hub_customer_key = sat.hub_customer_key
),

customers AS (
    SELECT
        hub_customer_key,
        customer_id,
        customer_name,
        email,
        phone,
        date_of_birth,
        DATEDIFF('year', date_of_birth, CURRENT_DATE()) AS age
    FROM customer_profile_ranked
    WHERE profile_rank = 1
),

account_balance_ranked AS (
    SELECT
        link.hub_customer_key,
        link.hub_account_key,
        link.account_id,
        sat_acc.account_type,
        sat_acc.balance,
        ROW_NUMBER() OVER (
            PARTITION BY link.hub_account_key
            ORDER BY sat_acc.load_datetime DESC
        ) AS balance_rank
    FROM {{ ref('link_customer_account') }} link
    LEFT JOIN {{ ref('sat_account_balance') }} sat_acc
        ON link.hub_account_key = sat_acc.account_hk
),

latest_accounts AS (
    SELECT
        hub_customer_key,
        account_id,
        COALESCE(account_type, 'UNKNOWN') AS account_type,
        COALESCE(balance, 0) AS balance,
        CASE
            WHEN UPPER(COALESCE(account_type, '')) IN ('CLOSED', 'INACTIVE') THEN 0
            ELSE 1
        END AS is_active_account
    FROM account_balance_ranked
    WHERE balance_rank = 1
),

transactions AS (
    SELECT
        link.hub_customer_key,
        COUNT(DISTINCT txn.transaction_id) AS total_transactions,
        COALESCE(SUM(txn.amount), 0) AS total_transaction_amount,
        MAX(txn.transaction_datetime) AS last_transaction_date
    FROM {{ ref('link_customer_account') }} link
    LEFT JOIN {{ ref('t_link_transactions') }} txn
        ON link.hub_account_key = txn.account_hk
    GROUP BY link.hub_customer_key
)

SELECT
    c.hub_customer_key,
    c.customer_id,
    a.account_id,
    a.balance,
    c.customer_name,
    c.email,
    c.phone,
    c.age,
    COUNT(DISTINCT a.account_id) OVER (PARTITION BY c.hub_customer_key) AS total_accounts,
    SUM(a.is_active_account) OVER (PARTITION BY c.hub_customer_key) AS active_accounts,
    SUM(a.balance) OVER (PARTITION BY c.hub_customer_key) AS total_balance,
    COALESCE(t.total_transactions, 0) AS total_transactions,
    COALESCE(t.total_transaction_amount, 0) AS total_transaction_amount,
    t.last_transaction_date,
    CURRENT_TIMESTAMP AS generated_at
FROM customers c
INNER JOIN latest_accounts a ON c.hub_customer_key = a.hub_customer_key
LEFT JOIN transactions t ON c.hub_customer_key = t.hub_customer_key
