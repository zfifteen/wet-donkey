## Task

Write the narration script for a video with the following plan.

Video Title: {{ plan.title }}
Video Description: {{ plan.description }}

{% for scene in plan.scenes %}
### Scene: {{ scene.title }}
Description: {{ scene.description }}
{% endfor %}

Generate a JSON object that follows the `Narration` schema, providing the `narration_text` for each scene.
