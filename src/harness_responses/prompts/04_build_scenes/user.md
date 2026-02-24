## Task

Generate the Manim scene body for:
-   **Title**: {{ scene_title }}
-   **Description**: {{ scene_description }}
-   **Narration duration**: {{ narration_duration }}s
-   **Visual ideas**: {{ visual_ideas }}

## Available Tools

1.  **Search template library**: Find proven patterns.
    -   *Query example*: "animated line graph with voiceover tracking"

2.  **Search previous scenes**: Review validated code.
    -   *Query example*: "safe_layout with multiple equations"

3.  **Execute validation code**: Test timing/layout.
    ```python
    # Check if animations fit duration budget
    total_runtime = sum([anim1.run_time, anim2.run_time])
    assert total_runtime <= {{ narration_duration }} * 1.1
    ```

## Process

1.  Search Collections for 2-3 relevant examples.
2.  Draft the scene body using proven patterns from the template library.
3.  Validate the timing of your animations with the `code_execution` tool.
4.  Output the final scene body as a JSON object matching the `SceneBuild` schema.
