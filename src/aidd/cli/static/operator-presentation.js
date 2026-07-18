function presentationSelectorFromSearch(_search = window.location.search) {
  return "studio";
}

function resolveSurfaceRendererFor(entry, _selector) {
  return Object.freeze({
    surface: entry.id,
    presentation: "studio",
    renderer: `studio:${entry.id}`,
    rollout: entry.rollout,
    fallback: false
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
