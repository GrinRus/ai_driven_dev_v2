const PRESENTATION_SELECTORS = new Set(["studio", "legacy"]);

function presentationSelectorFromSearch(search = window.location.search) {
  const requested = new URLSearchParams(search).get("ui") || "";
  return PRESENTATION_SELECTORS.has(requested) ? requested : "legacy";
}

function initializePresentationSelector() {
  const requested = presentationSelectorFromSearch();
  const selection = Object.freeze({
    requested,
    effective: "legacy",
    fallback: requested === "studio"
  });
  window.aiddPresentation = selection;
  document.documentElement.dataset.presentationRequested = selection.requested;
  document.documentElement.dataset.presentationEffective = selection.effective;
  return selection;
}

initializePresentationSelector();
