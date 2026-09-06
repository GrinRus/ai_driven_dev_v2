from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import collect_accessibility_violations


def test_status_and_surface_palettes_resolve_through_semantic_roles(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main>
              <span id="success" class="small-badge good">Succeeded</span>
              <span id="warning" class="small-badge warn">Blocked</span>
              <span id="danger" class="small-badge bad">Failed</span>
              <span id="info" class="small-badge running">Running</span>
              <section id="neutralSurface" class="state-surface">No pending action</section>
              <section id="warnSurface" class="state-surface" data-state="unavailable">
                Runtime unavailable
              </section>
              <section id="badSurface" class="state-surface" data-state="error">
                Runtime failed
              </section>
            </main>
            """,
            wait_until="networkidle",
        )

        styles = page.evaluate(
            """
            () => {
              const value = (selector, property) => getComputedStyle(
                document.querySelector(selector)
              )[property];
              const tokenColor = (name) => {
                const probe = document.createElement("span");
                probe.style.color = `var(${name})`;
                document.body.appendChild(probe);
                const result = getComputedStyle(probe).color;
                probe.remove();
                return result;
              };
              return {
                success: value("#success", "backgroundColor"),
                warning: value("#warning", "backgroundColor"),
                danger: value("#danger", "backgroundColor"),
                info: value("#info", "backgroundColor"),
                neutralSurface: value("#neutralSurface", "backgroundColor"),
                warnSurface: value("#warnSurface", "backgroundColor"),
                badSurface: value("#badSurface", "backgroundColor"),
                successToken: tokenColor("--color-state-success-bg"),
                warningToken: tokenColor("--color-state-warning-bg-soft"),
                dangerToken: tokenColor("--color-state-danger-bg-strong"),
                infoToken: tokenColor("--color-state-info-bg"),
              };
            }
            """
        )
        assert styles["success"] == styles["successToken"]
        assert styles["warning"] == styles["warningToken"]
        assert styles["danger"] == styles["dangerToken"]
        assert styles["info"] == styles["infoToken"]
        assert len(
            {
                styles["neutralSurface"],
                styles["warnSurface"],
                styles["badSurface"],
            }
        ) == 3
        contrast_failures = [
            violation
            for violation in collect_accessibility_violations(page)
            if violation.rule == "contrast"
        ]
        assert contrast_failures == []
        browser_page.diagnostics.assert_clean()
