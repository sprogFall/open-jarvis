from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "build-android-apk.yml"


def test_build_workflow_retries_checkout_for_each_flutter_job():
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    expected_snippets = [
        (
            "analyze job checkout retry",
            """- name: Checkout repository (attempt 1)
        id: analyze_checkout_primary
        continue-on-error: true
        uses: actions/checkout@v6

      - name: Checkout repository (attempt 2)
        if: steps.analyze_checkout_primary.outcome == 'failure'
        uses: actions/checkout@v6""",
        ),
        (
            "test job checkout retry",
            """- name: Checkout repository (attempt 1)
        id: test_checkout_primary
        continue-on-error: true
        uses: actions/checkout@v6

      - name: Checkout repository (attempt 2)
        if: steps.test_checkout_primary.outcome == 'failure'
        uses: actions/checkout@v6""",
        ),
        (
            "build job checkout retry",
            """- name: Checkout repository (attempt 1)
        id: build_checkout_primary
        continue-on-error: true
        uses: actions/checkout@v6

      - name: Checkout repository (attempt 2)
        if: steps.build_checkout_primary.outcome == 'failure'
        uses: actions/checkout@v6""",
        ),
    ]

    for label, snippet in expected_snippets:
        assert snippet in workflow, f"Missing {label} fallback in workflow."
