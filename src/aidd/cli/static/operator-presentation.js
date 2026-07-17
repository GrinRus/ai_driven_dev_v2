const PRESENTATION_SELECTORS = new Set(["studio", "legacy"]);

function presentationSelectorFromSearch(search = window.location.search) {
  const requested = new URLSearchParams(search).get("ui") || "";
  return PRESENTATION_SELECTORS.has(requested) ? requested : "legacy";
}

function resolveSurfaceRendererFor(entry, selector) {
  const requested = PRESENTATION_SELECTORS.has(selector) ? selector : "legacy";
  const studioEligible = ["candidate", "parity_closed"].includes(entry.rollout);
  const presentation = requested === "studio" && studioEligible ? "studio" : "legacy";
  return Object.freeze({
    surface: entry.id,
    presentation,
    renderer: presentation === "studio" ? `studio:${entry.id}` : entry.rollbackRenderer,
    rollout: entry.rollout,
    fallback: requested === "studio" && presentation === "legacy"
  });
}

function resolveSurfaceRenderer(surfaceId, selector = window.aiddPresentation?.requested) {
  const entry = surfaceParityEntry(surfaceId);
  if (!entry) throw new Error(`Unknown presentation surface: ${surfaceId}`);
  return resolveSurfaceRendererFor(entry, selector);
}

function selectSurfaceRenderer(surfaceId, renderers) {
  const resolution = resolveSurfaceRenderer(surfaceId);
  const renderer = renderers?.[resolution.presentation];
  if (typeof renderer !== "function") {
    throw new Error(
      `Missing ${resolution.presentation} renderer for ${surfaceId} (${resolution.rollout})`
    );
  }
  return {resolution, renderer};
}

function initializePresentationSelector() {
  const requested = presentationSelectorFromSearch();
  const surfaces = Object.freeze(Object.fromEntries(
    SURFACE_PARITY_MANIFEST.map((entry) => [
      entry.id,
      resolveSurfaceRendererFor(entry, requested)
    ])
  ));
  const presentations = new Set(
    Object.values(surfaces).map((resolution) => resolution.presentation)
  );
  const effective = presentations.size === 1 ? [...presentations][0] : "mixed";
  const selection = Object.freeze({
    requested,
    effective,
    fallback: Object.values(surfaces).some((resolution) => resolution.fallback),
    surfaces
  });
  window.aiddPresentation = selection;
  document.documentElement.dataset.presentationRequested = selection.requested;
  document.documentElement.dataset.presentationEffective = selection.effective;
  return selection;
}

initializePresentationSelector();
