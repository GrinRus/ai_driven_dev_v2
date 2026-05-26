from __future__ import annotations

from html.parser import HTMLParser
from importlib.resources import files

from aidd.cli.ui_assets import _INDEX_HTML, _OPERATOR_CSS, _OPERATOR_JS


class _StartTagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def _html_tags() -> list[tuple[str, dict[str, str | None]]]:
    collector = _StartTagCollector()
    collector.feed(_INDEX_HTML)
    return collector.tags


def _attrs_for(tag: str, **required: str) -> dict[str, str | None]:
    for candidate_tag, attrs in _html_tags():
        if candidate_tag != tag:
            continue
        if all(attrs.get(key) == value for key, value in required.items()):
            return attrs
    raise AssertionError(f"missing <{tag}> with attrs {required}")


def test_operator_assets_are_loaded_from_packaged_static_resources() -> None:
    static_files = files("aidd.cli.static")

    assert static_files.joinpath("index.html").read_text(encoding="utf-8") == _INDEX_HTML
    assert static_files.joinpath("operator.css").read_text(encoding="utf-8") == _OPERATOR_CSS
    assert static_files.joinpath("operator.js").read_text(encoding="utf-8") == _OPERATOR_JS


def test_index_html_exposes_named_operator_landmarks() -> None:
    assert _attrs_for("header", **{"aria-label": "Operator controls"})
    assert _attrs_for("main", **{"aria-label": "Operator workspace"})
    assert _attrs_for("aside", **{"aria-label": "Workflow navigation"})
    assert _attrs_for("section", **{"aria-label": "Stage cockpit"})
    assert _attrs_for("aside", **{"aria-label": "Run details"})
    assert _attrs_for("section", **{"aria-label": "Activity and recent artifacts"})
    assert _attrs_for("nav", id="stageRail", **{"aria-label": "Workflow stages"})


def test_index_html_exposes_tab_and_panel_semantics() -> None:
    assert _attrs_for("div", role="tablist", **{"aria-label": "Stage cockpit views"})
    overview_tab = _attrs_for("button", id="tab-overview", role="tab")
    questions_tab = _attrs_for("button", id="tab-questions", role="tab")
    panel = _attrs_for("div", id="cockpitContent", role="tabpanel")

    assert overview_tab["aria-selected"] == "true"
    assert overview_tab["aria-controls"] == "cockpitContent"
    assert questions_tab["aria-selected"] == "false"
    assert questions_tab["aria-controls"] == "cockpitContent"
    assert panel["aria-labelledby"] == "tab-overview"
    assert panel["tabindex"] == "0"


def test_index_html_exposes_runtime_and_loading_contracts() -> None:
    runtime_label = _attrs_for("label", **{"class": "runtime-picker", "for": "runtimeSelect"})
    runtime_select = _attrs_for("select", id="runtimeSelect")
    loading_state = _attrs_for("div", **{"class": "empty-state loading-state"})

    assert runtime_label["for"] == runtime_select["id"]
    assert loading_state["class"] == "empty-state loading-state"


def test_operator_script_keeps_dynamic_accessibility_contracts() -> None:
    assert "function questionControlId(prefix, questionId, index)" in _OPERATOR_JS
    assert 'aria-describedby="${questionTextId}"' in _OPERATOR_JS
    assert 'aria-current="${isActive ? "step" : "false"}"' in _OPERATOR_JS
    assert 'button.setAttribute("aria-selected", isActive ? "true" : "false");' in _OPERATOR_JS
    assert "renderTruncationNotice(" in _OPERATOR_JS
    assert "function scrollActiveStageIntoView()" in _OPERATOR_JS


def test_operator_css_keeps_focus_and_screen_reader_contracts() -> None:
    assert ".sr-only" in _OPERATOR_CSS
    assert "button:focus-visible" in _OPERATOR_CSS
    assert "outline: 3px solid var(--focus-ring)" in _OPERATOR_CSS
    assert ".truncation-notice" in _OPERATOR_CSS
    assert ".saved-answer" in _OPERATOR_CSS
