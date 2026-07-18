const STUDIO_INBOX_SECTION_ORDER = Object.freeze([
  "needs-decision",
  "running-now",
  "ready-to-continue",
  "flow-complete"
]);

function inboxRouteAttributes(route) {
  if (!route) return "";
  return [
    `data-operator-route-intent="${escapeHtml(route.intent)}"`,
    `data-route-work-item="${escapeHtml(route.work_item)}"`,
    route.run_id ? `data-route-run-id="${escapeHtml(route.run_id)}"` : "",
    route.stage ? `data-route-stage="${escapeHtml(route.stage)}"` : ""
  ].filter(Boolean).join(" ");
}

function renderStudioInboxItem(item) {
  const route = item.route || null;
  const action = item.primary_action || null;
  const actionMarkup = action && route
    ? `<button ${inboxRouteAttributes(route)} data-inbox-action="${escapeHtml(action.action)}" data-service-action-enabled="${action.enabled === false ? "false" : "true"}" type="button">${escapeHtml(action.label)}</button>`
    : '<span class="inbox-item-no-action">No action available</span>';
  const routeLabel = route
    ? [route.work_item, route.run_id, route.stage].filter(Boolean).join(" / ")
    : "Durable identity unavailable";
  const markerStatus = {
    blocking: "blocked",
    running: "pending",
    ready: "action",
    terminal: "complete",
    malformed: "stale"
  }[item.state];
  return `
    <article class="inbox-item" data-inbox-item="${escapeHtml(item.item_id || item.job_id)}" data-state="${escapeHtml(item.state)}">
      <div class="inbox-item-copy">
        ${renderStatusMarker({status: markerStatus, label: item.status_label})}
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.summary)}</p>
        <dl><div><dt>Context</dt><dd>${escapeHtml(routeLabel)}</dd></div></dl>
      </div>
      <div class="inbox-item-action">${actionMarkup}</div>
    </article>
  `;
}

function runningNowInboxItems(items = []) {
  return items.map((item) => ({
    ...item,
    item_id: item.job_id,
    state: item.route ? "running" : "malformed",
    status_label: item.route ? "Running now" : "Context unavailable",
    title: item.route ? `${item.kind} in progress` : `${item.kind} job`,
    summary: item.last_output_text || item.message || "Waiting for durable runtime output.",
    primary_action: item.route
      ? {action: "open-running-job", label: "Open in Studio", enabled: true}
      : null
  }));
}

function studioInboxSections(inbox) {
  const durable = new Map((inbox?.durable?.sections || []).map((section) => [section.key, section]));
  const sections = new Map(durable);
  sections.set("running-now", {
    key: "running-now",
    label: "Running now",
    items: runningNowInboxItems(inbox?.running_now || [])
  });
  return STUDIO_INBOX_SECTION_ORDER.map((key) => sections.get(key) || {
    key,
    label: key.replaceAll("-", " "),
    items: []
  });
}

function renderStudioInbox() {
  if (!state.inbox) {
    return renderStateSurface({
      kind: "inbox",
      state: "loading",
      title: "Loading Inbox",
      consequence: "Rebuilding project-local decisions from durable evidence."
    });
  }
  const sections = studioInboxSections(state.inbox);
  const count = sections.reduce((total, section) => total + section.items.length, 0);
  const visibleSections = sections.filter((section) => section.items.length);
  return `
    <section class="studio-inbox" data-studio-surface="inbox">
      <header class="surface studio-inbox-header">
        <div>
          <p class="eyebrow">Inbox</p>
          <h2>Operator decisions</h2>
          <p class="muted">Durable workflow state first, with current UI jobs shown as a temporary overlay.</p>
        </div>
        <span class="small-badge">${escapeHtml(count)} items</span>
      </header>
      <div class="studio-inbox-sections">
        ${visibleSections.length ? visibleSections.map((section) => `
          <section class="surface inbox-section" data-inbox-section="${escapeHtml(section.key)}">
            <div class="surface-title">
              <span>${escapeHtml(section.label)}</span>
              <span class="small-badge">${escapeHtml(section.items.length)}</span>
            </div>
            <div class="inbox-section-items">
              ${section.items.map(renderStudioInboxItem).join("")}
            </div>
          </section>
        `).join("") : renderStateSurface({
          kind: "inbox",
          state: "empty",
          title: "Inbox is clear",
          consequence: "No durable operator decision is waiting in this project."
        })}
      </div>
    </section>
  `;
}
