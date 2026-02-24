## Task

Create a complete video plan for the following topic:
**{{ topic }}**

{% if retry_context %}
## Retry Context

The previous attempt failed with the following error. Please analyze the error and adjust your plan accordingly.
Error: {{ retry_context }}
{% endif %}

Generate a JSON object matching the `Plan` schema.
