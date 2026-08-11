const STUDIO_INBOX_SECTION_ORDER = Object.freeze([
  "needs-input",
  "running",
  "ready",
  "complete"
]);

const STUDIO_INBOX_SECTION_LABELS = Object.freeze({
  "needs-input": "Needs input",
  running: "Running",
  ready: "Ready",
  complete: "Complete"
});

// Older persisted fixtures may still use the pre-Wave-42 presentation keys. They
// are accepted as input only; the DOM always exposes the core-owned vocabulary.
const CORE_INBOX_SECTION_ALIASES = Object.freeze({
  "needs-input": "needs-input",
  running: "running",
  ready: "ready",
  complete: "complete",
  "needs-decision": "needs-input",
  "running-now": "running",
  "ready-to-continue": "ready",
  "flow-complete": "complete"
});

function inboxRouteAttributes(route) {
  if (!route) return "";
  return [
    `data-operator-route-intent="${escapeHtml(route.intent)}"`,
    `data-route-work-item="${escapeHtml(route.work_item)}"`,
    route.run_id ? `data-route-run-id="${escapeHtml(route.run_id)}"` : "",
    route.stage ? `data-route-stage="${escapeHtml(route.stage)}"` : ""
  ].filter(Boolean).join(" ");
}

function inboxProjectProgressText(projectItem) {
  if (!projectItem) return "";
  if (typeof workItemProgressText === "function") return workItemProgressText(projectItem);
  if (projectItem.stage_progress_label) return String(projectItem.stage_progress_label);
  return `${Number(projectItem.stage_progress_count || 0)} of ${Number(projectItem.stage_total_count || 0)} stages complete`;
}

function renderStudioInboxItem(item, {selectedWorkItem = ""} = {}) {
  const route = item.route || null;
  const action = item.primary_action || null;
  const projectItem = (state.projectHome?.work_items || []).find(
    (candidate) => candidate.work_item === route?.work_item
  ) || null;
  const selected = Boolean(selectedWorkItem && selectedWorkItem === route?.work_item);
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
  const selectionAttributes = selected
    ? `data-selected-work-item="${escapeHtml(route?.work_item)}" aria-current="true"`
    : 'aria-current="false"';
  return `
    <article class="inbox-item${selected ? " selected" : ""}" data-inbox-item="${escapeHtml(item.item_id || item.job_id)}" data-state="${escapeHtml(item.state)}" ${selectionAttributes}>
      <div class="inbox-item-copy">
        ${renderStatusMarker({status: markerStatus, label: item.status_label})}
        <strong>${escapeHtml(projectItem?.intent?.excerpt || item.title)}</strong>
        <small class="inbox-item-identity">${escapeHtml(item.title)}</small>
        <p>${escapeHtml(item.summary)}</p>
        <dl>
          <div><dt>Context</dt><dd>${escapeHtml(routeLabel)}</dd></div>
          ${projectItem ? `<div><dt>Progress</dt><dd>${escapeHtml(inboxProjectProgressText(projectItem))}</dd></div>` : ""}
        </dl>
      </div>
      <div class="inbox-item-action">${selected
        ? `<span class="inbox-item-selected-hint" ${inboxRouteAttributes(route)} data-inbox-selected-route="true">Selected Work Item</span>`
        : actionMarkup}</div>
    </article>
  `;
}

function inboxSelectedWorkItem() {
  return String(
    state.projectHome?.selected_work_item
      || state.dashboard?.work_item
      || state.activeRouteWorkItem
      || ""
  );
}

function inboxSelectedItem(sections, workItem) {
  if (!workItem) return null;
  for (const section of sections) {
    const item = section.items.find((candidate) => candidate.route?.work_item === workItem);
    if (item) return item;
  }
  return null;
}

function renderInboxSelectedContext(item) {
  if (!item?.route?.work_item) return "";
  const route = item.route;
  const action = item.primary_action || null;
  const projectItem = (state.projectHome?.work_items || []).find(
    (candidate) => candidate.work_item === route.work_item
  ) || null;
  const actionMarkup = action
    ? `<button ${inboxRouteAttributes(route)} data-inbox-action="${escapeHtml(action.action)}" data-service-action-enabled="${action.enabled === false ? "false" : "true"}" type="button">${escapeHtml(action.label)}</button>`
    : '<span class="inbox-item-no-action">No primary action available</span>';
  const context = [route.work_item, route.run_id, route.stage].filter(Boolean).join(" / ");
  const progress = projectItem ? inboxProjectProgressText(projectItem) : item.status_label;
  return `
    <aside class="surface inbox-selected-context" data-inbox-inspector data-inbox-selected-context="${escapeHtml(route.work_item)}" aria-label="Selected Work Item">
      <div class="inbox-selected-context-head">
        <p class="eyebrow">Selected Work Item</p>
        <span class="small-badge">${escapeHtml(item.status_label)}</span>
      </div>
      <h2>${escapeHtml(projectItem?.intent?.excerpt || item.title)}</h2>
      <p class="inbox-selected-context-identity">${escapeHtml(context)}</p>
      <p>${escapeHtml(item.summary)}</p>
      <dl class="inbox-selected-context-facts">
        <div><dt>Stage</dt><dd>${escapeHtml(route.stage || "Unavailable")}</dd></div>
        <div><dt>Progress</dt><dd>${escapeHtml(progress)}</dd></div>
      </dl>
      <div class="inbox-selected-context-action">${actionMarkup}</div>
    </aside>
  `;
}

function renderStudioEntryRecommendation(inbox) {
  const recommendation = inbox?.durable?.entry_recommendation;
  const projectItem = recommendation?.work_item
    ? (state.projectHome?.work_items || []).find(
      (candidate) => candidate.work_item === recommendation.work_item
    )
    : null;
  const workItemText = projectItem?.intent?.excerpt || recommendation?.detail || "";
  const actionMarkup = recommendation?.action === "continue-existing-intent" && recommendation.route
    ? `<button ${inboxRouteAttributes(recommendation.route)} data-inbox-action="continue-existing-intent" type="button">${escapeHtml(recommendation.label || "Continue existing Work Item")}</button>`
    : `<button data-new-work-item type="button">${escapeHtml(recommendation?.label || "Create new Work Item")}</button>`;
  const secondaryAction = recommendation?.action === "continue-existing-intent"
    ? `<button data-new-work-item class="secondary" type="button">New Work Item</button>`
    : "";
  return `
    <section class="surface intent-entry-recommendation" data-intent-entry-recommendation="${escapeHtml(recommendation?.action || "create-new-intent")}">
      <div class="intent-entry-copy">
        <p class="eyebrow">Returning to this project</p>
        <h2>${escapeHtml(recommendation?.label || "Create new Work Item")}</h2>
        <p>${escapeHtml(workItemText)}</p>
        ${recommendation?.work_item ? `<span class="small-badge">${escapeHtml(recommendation.work_item)}</span>` : ""}
      </div>
      <div class="intent-entry-actions">
        ${actionMarkup}
        ${secondaryAction}
      </div>
    </section>
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
  const sections = new Map();
  for (const section of durable.values()) {
    const presentationKey = CORE_INBOX_SECTION_ALIASES[section.key] || section.key;
    sections.set(presentationKey, {
      ...section,
      key: presentationKey,
      label: STUDIO_INBOX_SECTION_LABELS[presentationKey] || section.label
    });
  }
  const durableRunning = sections.get("running");
  const runningNow = runningNowInboxItems(inbox?.running_now || []);
  sections.set("running", {
    ...(durableRunning || {}),
    key: "running",
    label: STUDIO_INBOX_SECTION_LABELS.running,
    // A live job is the richer compatibility representation for its same
    // work-item/run; fall back to the durable wait-for-stage item otherwise.
    items: runningNow.length ? runningNow : (durableRunning?.items || [])
  });
  return STUDIO_INBOX_SECTION_ORDER.map((key) => sections.get(key) || {
    key,
    label: STUDIO_INBOX_SECTION_LABELS[key],
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
  const selectedWorkItem = inboxSelectedWorkItem();
  const selectedItem = inboxSelectedItem(sections, selectedWorkItem);
  return `
    <section class="studio-inbox" data-studio-surface="inbox">
      <header class="surface studio-inbox-header">
        <div>
          <p class="eyebrow">Inbox</p>
          <h2>Project inbox</h2>
          <p class="muted">Choose the Work Item that needs attention, or create one before selecting a runtime.</p>
        </div>
        <div class="studio-inbox-actions">
          <span class="small-badge">${escapeHtml(count)} items</span>
          <button data-new-work-item aria-label="New Work Item" type="button">New Work Item</button>
        </div>
      </header>
      ${renderStudioEntryRecommendation(state.inbox)}
      ${renderProjectWorkItemCreator()}
      <div class="studio-inbox-layout">
        <div class="studio-inbox-sections">
        ${sections.map((section) => `
          <section class="surface inbox-section" data-inbox-section="${escapeHtml(section.key)}">
            <div class="surface-title">
              <span>${escapeHtml(section.label)}</span>
              <span class="small-badge">${escapeHtml(section.items.length)}</span>
            </div>
            <div class="inbox-section-items">
              ${section.items.length
                ? section.items.map((item) => renderStudioInboxItem(item, {selectedWorkItem})).join("")
                : '<p class="inbox-section-empty">No Work Items in this group.</p>'}
            </div>
          </section>
        `).join("")}
        ${count ? "" : renderStateSurface({
          kind: "inbox",
          state: "empty",
          title: "Inbox is clear",
          consequence: "No durable operator decision is waiting in this project."
        })}
        </div>
        ${renderInboxSelectedContext(selectedItem)}
      </div>
    </section>
  `;
}
