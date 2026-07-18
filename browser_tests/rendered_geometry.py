from __future__ import annotations

from playwright.sync_api import Page

from browser_tests.rendered_assertions import (
    RenderedAssertionError,
    RenderedViolation,
)

_GEOMETRY_MEASUREMENTS = r"""
({maxHeaderHeight}) => {
  const violations = [];
  const selectorFor = (element) => {
    if (element === document.documentElement) return "html";
    if (element.id) return `#${CSS.escape(element.id)}`;
    const parts = [];
    let current = element;
    while (current && current !== document.body) {
      const siblings = Array.from(current.parentElement?.children || [])
        .filter((candidate) => candidate.tagName === current.tagName);
      const suffix = siblings.length > 1
        ? `:nth-of-type(${siblings.indexOf(current) + 1})`
        : "";
      parts.unshift(`${current.tagName.toLowerCase()}${suffix}`);
      current = current.parentElement;
    }
    return `body > ${parts.join(" > ")}`;
  };
  const add = (rule, element, measured, expected) => {
    violations.push({
      rule,
      selector: selectorFor(element),
      measured: String(measured),
      expected,
    });
  };
  const visible = (element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== "none"
      && style.visibility !== "hidden"
      && rect.width > 0
      && rect.height > 0;
  };

  for (const header of document.querySelectorAll("[data-aidd-sticky-header]")) {
    if (!visible(header)) continue;
    const rect = header.getBoundingClientRect();
    if (rect.height > maxHeaderHeight) {
      add(
        "sticky-header",
        header,
        `${rect.height.toFixed(1)}px`,
        `<= ${maxHeaderHeight}px`,
      );
    }
  }

  for (const action of document.querySelectorAll("[data-aidd-primary-action]")) {
    if (!visible(action)) continue;
    const rect = action.getBoundingClientRect();
    if (rect.top < 0 || rect.bottom > window.innerHeight) {
      add(
        "primary-action",
        action,
        `top=${rect.top.toFixed(1)}px bottom=${rect.bottom.toFixed(1)}px`,
        `inside first viewport 0..${window.innerHeight}px`,
      );
    }
  }

  for (const element of document.querySelectorAll("[data-aidd-clipping-check]")) {
    if (!visible(element)) continue;
    if (element.scrollWidth > element.clientWidth || element.scrollHeight > element.clientHeight) {
      add(
        "clipping",
        element,
        `${element.scrollWidth}x${element.scrollHeight}px in `
          + `${element.clientWidth}x${element.clientHeight}px`,
        "content fits its rendered bounds",
      );
    }
  }

  const overlapElements = Array.from(
    document.querySelectorAll("[data-aidd-overlap-check]"),
  ).filter(visible);
  for (let leftIndex = 0; leftIndex < overlapElements.length; leftIndex += 1) {
    const left = overlapElements[leftIndex];
    const leftRect = left.getBoundingClientRect();
    for (let rightIndex = leftIndex + 1; rightIndex < overlapElements.length; rightIndex += 1) {
      const right = overlapElements[rightIndex];
      if (left.contains(right) || right.contains(left)) continue;
      const rightRect = right.getBoundingClientRect();
      const width = Math.min(leftRect.right, rightRect.right)
        - Math.max(leftRect.left, rightRect.left);
      const height = Math.min(leftRect.bottom, rightRect.bottom)
        - Math.max(leftRect.top, rightRect.top);
      if (width > 0.5 && height > 0.5) {
        add(
          "overlap",
          right,
          `${width.toFixed(1)}x${height.toFixed(1)}px with ${selectorFor(left)}`,
          "no overlap between declared surfaces",
        );
      }
    }
  }

  const scrollable = Array.from(document.querySelectorAll("body *")).filter((element) => {
    if (!visible(element)) return false;
    const style = getComputedStyle(element);
    return ["auto", "scroll"].includes(style.overflowY)
      && element.scrollHeight > element.clientHeight + 1;
  });
  const scrollableSet = new Set(scrollable);
  for (const element of scrollable) {
    let ancestor = element.parentElement;
    while (ancestor && ancestor !== document.body) {
      if (scrollableSet.has(ancestor)) {
        add(
          "nested-scroll",
          element,
          `scrollHeight=${element.scrollHeight}px inside ${selectorFor(ancestor)}`,
          "one primary vertical scroll owner",
        );
        break;
      }
      ancestor = ancestor.parentElement;
    }
  }

  const documentWidth = Math.max(
    document.documentElement.scrollWidth,
    document.body?.scrollWidth || 0,
  );
  if (documentWidth > window.innerWidth + 1) {
    const culprit = Array.from(document.querySelectorAll("body *"))
      .filter(visible)
      .sort(
        (left, right) => right.getBoundingClientRect().right
          - left.getBoundingClientRect().right,
      )
      .find((element) => {
        const rect = element.getBoundingClientRect();
        return rect.left < -1 || rect.right > window.innerWidth + 1;
      });
    add(
      "horizontal-overflow",
      culprit || document.documentElement,
      `scrollWidth=${documentWidth}px viewport=${window.innerWidth}px`,
      "document width <= viewport width",
    );
  }

  return violations;
}
"""


def collect_geometry_violations(
    page: Page,
    *,
    max_header_height: float = 80.0,
) -> tuple[RenderedViolation, ...]:
    raw = page.evaluate(
        _GEOMETRY_MEASUREMENTS,
        {"maxHeaderHeight": max_header_height},
    )
    return tuple(RenderedViolation(**item) for item in raw)


def assert_rendered_geometry(page: Page, *, max_header_height: float = 80.0) -> None:
    violations = collect_geometry_violations(
        page,
        max_header_height=max_header_height,
    )
    if violations:
        raise RenderedAssertionError(violations)
