from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page


@dataclass(frozen=True, slots=True)
class RenderedViolation:
    rule: str
    selector: str
    measured: str
    expected: str

    def render(self) -> str:
        return f"{self.rule}: {self.selector} measured {self.measured}; expected {self.expected}"


class RenderedAssertionError(AssertionError):
    def __init__(self, violations: tuple[RenderedViolation, ...]) -> None:
        self.violations = violations
        super().__init__("\n".join(violation.render() for violation in violations))


_ACCESSIBILITY_MEASUREMENTS = r"""
({targetSize}) => {
  const violations = [];
  const add = (rule, element, measured, expected) => {
    violations.push({rule, selector: selectorFor(element), measured: String(measured), expected});
  };
  const selectorFor = (element) => {
    if (element.id) return `#${CSS.escape(element.id)}`;
    const parts = [];
    let current = element;
    while (current && current !== document.body) {
      const siblings = Array.from(current.parentElement?.children || [])
        .filter((candidate) => candidate.tagName === current.tagName);
      const suffix = siblings.length > 1 ? `:nth-of-type(${siblings.indexOf(current) + 1})` : "";
      parts.unshift(`${current.tagName.toLowerCase()}${suffix}`);
      current = current.parentElement;
    }
    return `body > ${parts.join(" > ")}`;
  };
  const visible = (element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return style.display !== "none"
      && style.visibility !== "hidden"
      && rect.width > 0
      && rect.height > 0;
  };
  const interactiveSelector = [
    "button", "a[href]", "input:not([type=hidden])", "select", "textarea",
    "[role=button]", "[role=link]", "[tabindex]"
  ].join(",");
  const interactive = Array.from(document.querySelectorAll(interactiveSelector)).filter(visible);
  const accessibleName = (element) => {
    const labelledBy = element.getAttribute("aria-labelledby");
    if (labelledBy) {
      const value = labelledBy
        .split(/\s+/)
        .map((id) => document.getElementById(id)?.textContent || "")
        .join(" ")
        .trim();
      if (value) return value;
    }
    const ariaLabel = element.getAttribute("aria-label")?.trim();
    if (ariaLabel) return ariaLabel;
    if ("labels" in element && element.labels?.length) {
      const value = Array.from(element.labels)
        .map((label) => label.textContent || "")
        .join(" ")
        .trim();
      if (value) return value;
    }
    const alt = element.getAttribute("alt")?.trim();
    if (alt) return alt;
    const text = element.textContent?.trim();
    if (text) return text;
    const title = element.getAttribute("title")?.trim();
    return title || "";
  };

  for (const element of interactive) {
    if (!accessibleName(element)) {
      add("accessible-name", element, "empty", "non-empty accessible name");
    }
    const rect = element.getBoundingClientRect();
    if (rect.width < targetSize || rect.height < targetSize) {
      add(
        "target-size",
        element,
        `${rect.width.toFixed(1)}x${rect.height.toFixed(1)}px`,
        `>= ${targetSize}x${targetSize}px`,
      );
    }
  }

  const labelableInput = [
    "input:not([type=hidden])",
    ":not([type=button])",
    ":not([type=submit])",
    ":not([type=reset])",
  ].join("");
  const labelableSelector = `${labelableInput},select,textarea`;
  const labelable = Array.from(document.querySelectorAll(labelableSelector)).filter(visible);
  for (const element of labelable) {
    const hasNativeLabel = "labels" in element && element.labels?.length > 0;
    const hasAriaLabel = Boolean(element.getAttribute("aria-label")?.trim());
    const labelledBy = element.getAttribute("aria-labelledby")?.trim();
    const hasLabelledBy = Boolean(
      labelledBy
      && labelledBy.split(/\s+/).every((id) => document.getElementById(id)),
    );
    if (!hasNativeLabel && !hasAriaLabel && !hasLabelledBy) {
      add("label", element, "unassociated", "native label or resolvable aria label");
    }
  }

  const tabbable = interactive.filter(
    (element) => !element.hasAttribute("disabled") && element.tabIndex >= 0,
  );
  for (const element of tabbable) {
    if (element.tabIndex > 0) {
      add("focus-order", element, `tabindex=${element.tabIndex}`, "DOM order (tabindex=0)");
    }
  }
  const primaryIndex = tabbable.findIndex(
    (element) => element.dataset.aiddFocusRole === "primary",
  );
  const maintenanceIndex = tabbable.findIndex(
    (element) => element.dataset.aiddFocusRole === "maintenance",
  );
  if (primaryIndex >= 0 && maintenanceIndex >= 0 && primaryIndex > maintenanceIndex) {
    add(
      "focus-order",
      tabbable[primaryIndex],
      `position=${primaryIndex + 1} after maintenance=${maintenanceIndex + 1}`,
      "primary before maintenance",
    );
  }

  const parseRgb = (value) => {
    const match = value.match(/rgba?\(([^)]+)\)/);
    if (!match) return null;
    const values = match[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return {r: values[0], g: values[1], b: values[2], a: values.length > 3 ? values[3] : 1};
  };
  const backgroundFor = (element) => {
    let current = element;
    while (current) {
      const color = parseRgb(getComputedStyle(current).backgroundColor);
      if (color && color.a > 0.01) return color;
      current = current.parentElement;
    }
    return {r: 255, g: 255, b: 255, a: 1};
  };
  const luminance = ({r, g, b}) => {
    const channel = (value) => {
      const normalized = value / 255;
      return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
    };
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
  };
  const textElements = Array.from(document.querySelectorAll("body *")).filter((element) => {
    if (!visible(element)) return false;
    return Array.from(element.childNodes).some(
      (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim(),
    );
  });
  for (const element of textElements) {
    const foreground = parseRgb(getComputedStyle(element).color);
    if (!foreground) continue;
    const background = backgroundFor(element);
    const lighter = Math.max(luminance(foreground), luminance(background));
    const darker = Math.min(luminance(foreground), luminance(background));
    const ratio = (lighter + 0.05) / (darker + 0.05);
    const style = getComputedStyle(element);
    const large = Number.parseFloat(style.fontSize) >= 24 || (
      Number.parseFloat(style.fontSize) >= 18.66
      && Number.parseInt(style.fontWeight, 10) >= 700
    );
    const minimum = large ? 3 : 4.5;
    if (ratio + 0.001 < minimum) {
      add("contrast", element, `${ratio.toFixed(2)}:1`, `>= ${minimum.toFixed(1)}:1`);
    }
  }

  return violations;
}
"""


_REDUCED_MOTION_MEASUREMENTS = r"""
() => {
  const selectorFor = (element) => (
    element.id ? `#${CSS.escape(element.id)}` : element.tagName.toLowerCase()
  );
  const seconds = (value) => value.split(",").map((part) => {
    const trimmed = part.trim();
    return trimmed.endsWith("ms") ? Number.parseFloat(trimmed) / 1000 : Number.parseFloat(trimmed);
  });
  const violations = [];
  for (const element of document.querySelectorAll("body *")) {
    const style = getComputedStyle(element);
    const duration = Math.max(
      ...seconds(style.animationDuration),
      ...seconds(style.transitionDuration),
    );
    if (duration > 0.01) {
      violations.push({
        rule: "reduced-motion",
        selector: selectorFor(element),
        measured: `${duration.toFixed(2)}s`,
        expected: "<= 0.01s when prefers-reduced-motion=reduce",
      });
    }
  }
  return violations;
}
"""


def collect_accessibility_violations(
    page: Page,
    *,
    target_size: float = 44.0,
) -> tuple[RenderedViolation, ...]:
    raw = page.evaluate(_ACCESSIBILITY_MEASUREMENTS, {"targetSize": target_size})
    page.emulate_media(reduced_motion="reduce")
    try:
        raw.extend(page.evaluate(_REDUCED_MOTION_MEASUREMENTS))
    finally:
        page.emulate_media(reduced_motion="no-preference")
    return tuple(RenderedViolation(**item) for item in raw)


def assert_accessible_render(page: Page, *, target_size: float = 44.0) -> None:
    violations = collect_accessibility_violations(page, target_size=target_size)
    if violations:
        raise RenderedAssertionError(violations)
