{% macro duckdb__get_escape_characters() %}
    {%- do return(('"', '"')) -%}
{% endmacro %}

{% macro duckdb__cast_datetime(column_str, as_string=false, alias=none, date_type=none) %}
    {{ automate_dv.postgres__cast_datetime(column_str=column_str, as_string=as_string, alias=alias, date_type=date_type) }}
{% endmacro %}

{% macro duckdb__cast_date(column_str, as_string=false, alias=none) %}
    {{ automate_dv.postgres__cast_date(column_str=column_str, as_string=as_string, alias=alias) }}
{% endmacro %}
