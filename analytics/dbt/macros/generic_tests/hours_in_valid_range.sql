{#
  Generic test: fails for rows whose value is outside [min_value, max_value] (both inclusive).
  Usage in schema.yml:
    data_tests:
      - hours_in_valid_range:
          arguments: { min_value: 0, max_value: 24 }
  NULLs are left to not_null so each failure has exactly one cause.
#}
{% test hours_in_valid_range(model, column_name, min_value=0, max_value=24) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }}
{% endtest %}
