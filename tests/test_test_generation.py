from breakbot.config import BreakBotConfig
from breakbot.models import Finding, SourceBundle
from breakbot.test_generation import AdversarialTestGenerator


def test_generator_targets_python_module_path():
    finding = Finding(
        title="Bad parser",
        severity="medium",
        file_path="package/parser.py",
        line_hint=3,
        description="desc",
        attack_idea="attack",
        suggested_fix="fix",
    )

    tests = AdversarialTestGenerator(BreakBotConfig()).generate(
        SourceBundle(source_name="demo", files=[]),
        [finding],
    )

    assert "importlib.import_module(\"package.parser\")" in tests[0].content
