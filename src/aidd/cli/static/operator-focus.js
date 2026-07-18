let operatorFocusReturnTarget = null;
let operatorFocusEntryPending = false;

const OPERATOR_DETAIL_TRIGGER_SELECTOR = [
  "[data-tab-shortcut]",
  "[data-open-artifact]",
  "[data-artifact-key]",
  "[data-evidence-node]",
  "[data-next-flow-action]"
].join(",");

function currentDecisionTarget() {
  const selectors = [
    "#cockpitContent [data-primary-recovery-slot]",
    "#cockpitContent [data-primary-slot]",
    "#cockpitContent .setup-actions",
    "#globalNextActionStrip",
    "#nextActionPanel"
  ];
  for (const selector of selectors) {
    const candidate = document.querySelector(selector);
    if (candidate && !candidate.hidden && !candidate.closest("[hidden]")) return candidate;
  }
  return null;
}

function syncCurrentDecisionTarget() {
  document.querySelectorAll('[data-current-decision-target="true"]').forEach((node) => {
    node.removeAttribute("data-current-decision-target");
    if (node.id === "currentDecision") {
      const stableId = node.dataset.currentDecisionStableId || "";
      if (stableId) node.id = stableId;
      else node.removeAttribute("id");
    }
    delete node.dataset.currentDecisionStableId;
    if (node.getAttribute("tabindex") === "-1") node.removeAttribute("tabindex");
  });
  const target = currentDecisionTarget();
  if (target) {
    if (target.id && target.id !== "currentDecision") {
      target.dataset.currentDecisionStableId = target.id;
    }
    target.id = "currentDecision";
    target.setAttribute("data-current-decision-target", "true");
    target.setAttribute("tabindex", "-1");
  }
  if (operatorFocusEntryPending) {
    operatorFocusEntryPending = false;
    const content = document.getElementById("cockpitContent");
    if (content) content.focus({preventScroll: true});
  }
  return target;
}

function focusCurrentDecision() {
  const target = syncCurrentDecisionTarget();
  if (!target) return false;
  target.scrollIntoView({block: "start", inline: "nearest"});
  target.focus({preventScroll: true});
  return true;
}

function rememberOperatorFocusReturn(trigger) {
  if (!trigger) return;
  operatorFocusReturnTarget = trigger;
  operatorFocusEntryPending = true;
}

function returnOperatorFocus() {
  const fallback = document.querySelector('[data-tab][aria-selected="true"]');
  const target = operatorFocusReturnTarget?.isConnected ? operatorFocusReturnTarget : fallback;
  operatorFocusReturnTarget = null;
  operatorFocusEntryPending = false;
  if (!target) return false;
  target.focus();
  return true;
}

document.addEventListener("click", (event) => {
  const skip = event.target.closest?.("#skipToDecision");
  if (skip) {
    event.preventDefault();
    focusCurrentDecision();
    return;
  }
  const detailTrigger = event.target.closest?.(OPERATOR_DETAIL_TRIGGER_SELECTOR);
  if (detailTrigger) rememberOperatorFocusReturn(detailTrigger);
}, true);

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !operatorFocusReturnTarget) return;
  event.preventDefault();
  returnOperatorFocus();
});
