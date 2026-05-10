# chrome_tools 0.1 browser-control plan

This zip contains a planning pack for continuing development on branch `0.1` of `davidnoz123/chrome_tools`.

The immediate goal is to grow the existing raw-CDP foundation into a narrow, safe, Claude-friendly browser tooling layer.

The intended direction is:

```text
existing chrome_tools.py
    Chrome launch/adoption
    CDP WebSocket client
    target/session attach
    Runtime.evaluate
    CDP event dispatch
        ↓
PageController
        ↓
DOM/accessibility-style snapshot
        ↓
element refs
        ↓
safe query/action tools for Claude
        ↓
DataAnnotation support workflows
```

The key design decision is:

> Claude should never drive raw CDP directly. Claude should query a structured snapshot, then act on refs through named, guarded operations.

Suggested reading order:

1. `01_current_branch_assessment.md`
2. `02_architecture.md`
3. `03_claude_tooling_layer.md`
4. `04_query_tools_spec.md`
5. `05_action_tools_spec.md`
6. `06_single_file_implementation_plan.md`
7. `07_dataannotation_direction.md`
8. `08_safety_and_agents_policy.md`
9. `09_sim_tests.md`
10. `10_ready_to_paste_claude_prompt.md`
