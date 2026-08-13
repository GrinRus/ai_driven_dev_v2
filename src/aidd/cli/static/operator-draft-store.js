const OPERATOR_DRAFT_STORAGE_KEY = "aidd.operator.drafts.v1";
const OPERATOR_DRAFT_VERSION = 1;
const OPERATOR_DRAFT_TTL_MS = 24 * 60 * 60 * 1000;
const OPERATOR_DRAFT_MAX_COUNT = 32;
const OPERATOR_DRAFT_MAX_BYTES = 64 * 1024;
const OPERATOR_DRAFT_TOTAL_BYTES = 256 * 1024;
const OPERATOR_DRAFT_FORMS = new Set(["question", "intervention", "follow-up", "clone"]);
const OPERATOR_DRAFT_IDENTITY_FIELDS = ["project", "workItem", "run", "stage", "form", "sourceId"];
const OPERATOR_DRAFT_SENSITIVE_KEY = /(?:credential|password|secret|token|api[_-]?key)/i;

function operatorDraftIdentity(form, sourceId) {
  const currentState = typeof state === "undefined" ? {} : state;
  return Object.freeze({
    project: String(currentState?.dashboard?.project_root || currentState?.onboarding?.project?.workspace_root || window.location?.pathname || "operator"),
    workItem: String(currentState?.dashboard?.work_item || currentState?.activeRouteWorkItem || "no-work-item"),
    run: String(currentState?.activeRunId || "no-run"),
    stage: String(currentState?.activeStage || "idea"),
    form: String(form || ""),
    sourceId: String(sourceId || "default")
  });
}
const OPERATOR_DRAFT_PURPOSES = Object.freeze({
  intervention: Object.freeze({form: "intervention", label: "Intervention"}),
  remediation: Object.freeze({form: "intervention", label: "Remediation"}),
  "follow-up": Object.freeze({form: "follow-up", label: "Follow-up"}),
  clone: Object.freeze({form: "clone", label: "Clone"})
});

function operatorPurposeDraftSpec(purpose) {
  const normalized = String(purpose || "").trim().toLowerCase();
  const spec = OPERATOR_DRAFT_PURPOSES[normalized];
  if (!spec) throw new Error(`Unsupported operator draft purpose: ${purpose}`);
  return Object.freeze({purpose: normalized, ...spec});
}

function operatorPurposeDraftIdentity(purpose, sourceId) {
  const spec = operatorPurposeDraftSpec(purpose);
  return operatorDraftIdentity(spec.form, sourceId);
}

function operatorPurposeDraftValue(purpose, fields = {}) {
  const spec = operatorPurposeDraftSpec(purpose);
  const value = {...fields, purpose: spec.purpose, purpose_label: spec.label};
  if (!Object.prototype.hasOwnProperty.call(value, "destination")) value.destination = null;
  if (!Object.prototype.hasOwnProperty.call(value, "source_evidence")) value.source_evidence = [];
  return Object.freeze(value);
}

function operatorPurposeDraftState({purpose, draft = null, destination = null, submitted = false} = {}) {
  const spec = operatorPurposeDraftSpec(purpose);
  const value = draft?.value || draft || {};
  return Object.freeze({
    purpose: spec.purpose,
    label: spec.label,
    status: submitted ? "submitted" : draft ? "draft" : "empty",
    destination: destination || value.destination || null,
    source_evidence: [...(value.source_evidence || value.targetDocuments || value.selected_sources || [])],
    value
  });
}

function draftJsonBytes(value) {
  return new TextEncoder().encode(JSON.stringify(value)).byteLength;
}

function normalizeDraftIdentity(identity) {
  const normalized = {};
  for (const field of OPERATOR_DRAFT_IDENTITY_FIELDS) {
    const value = String(identity?.[field] || "").trim();
    if (!value) throw new Error(`Draft identity requires ${field}`);
    normalized[field] = value;
  }
  if (!OPERATOR_DRAFT_FORMS.has(normalized.form)) {
    throw new Error(`Unsupported draft form: ${normalized.form}`);
  }
  return Object.freeze(normalized);
}

function operatorDraftEntryKey(identity) {
  const normalized = normalizeDraftIdentity(identity);
  return JSON.stringify(OPERATOR_DRAFT_IDENTITY_FIELDS.map((field) => normalized[field]));
}

function draftContainsSensitiveKey(value) {
  if (!value || typeof value !== "object") return false;
  if (Array.isArray(value)) return value.some(draftContainsSensitiveKey);
  return Object.entries(value).some(([key, nested]) => (
    OPERATOR_DRAFT_SENSITIVE_KEY.test(key) || draftContainsSensitiveKey(nested)
  ));
}

function emptyDraftBucket() {
  return {version: OPERATOR_DRAFT_VERSION, entries: {}};
}

function draftRecordMatchesKey(key, record) {
  try {
    return operatorDraftEntryKey(record) === key;
  } catch (_error) {
    return false;
  }
}

function loadOperatorDraftBucket(storage = window.sessionStorage, now = Date.now()) {
  let parsed;
  try {
    parsed = JSON.parse(storage.getItem(OPERATOR_DRAFT_STORAGE_KEY) || "null");
  } catch (_error) {
    parsed = null;
  }
  const bucket = parsed?.version === OPERATOR_DRAFT_VERSION && parsed.entries
    && typeof parsed.entries === "object" && !Array.isArray(parsed.entries)
    ? parsed
    : emptyDraftBucket();
  const entries = {};
  for (const [key, record] of Object.entries(bucket.entries)) {
    if (!record || typeof record !== "object") continue;
    if (!draftRecordMatchesKey(key, record)) continue;
    if (record.dirty !== true || !Number.isFinite(record.updated_at_ms)) continue;
    if (!Number.isFinite(record.expires_at_ms) || record.expires_at_ms <= now) continue;
    if (draftContainsSensitiveKey(record.value)) continue;
    if (draftJsonBytes(record) > OPERATOR_DRAFT_MAX_BYTES) continue;
    entries[key] = record;
  }
  return {version: OPERATOR_DRAFT_VERSION, entries};
}

function orderedDraftEntries(entries, protectedKey = "") {
  return Object.entries(entries).sort(([leftKey, left], [rightKey, right]) => {
    if (leftKey === protectedKey) return 1;
    if (rightKey === protectedKey) return -1;
    return left.updated_at_ms - right.updated_at_ms || leftKey.localeCompare(rightKey);
  });
}

function compactOperatorDraftBucket(bucket, protectedKey = "") {
  const entries = {...bucket.entries};
  const ordered = orderedDraftEntries(entries, protectedKey);
  while (
    Object.keys(entries).length > OPERATOR_DRAFT_MAX_COUNT
    || draftJsonBytes({version: OPERATOR_DRAFT_VERSION, entries}) > OPERATOR_DRAFT_TOTAL_BYTES
  ) {
    const candidate = ordered.shift();
    if (!candidate) break;
    delete entries[candidate[0]];
  }
  return {version: OPERATOR_DRAFT_VERSION, entries};
}

function persistOperatorDraftBucket(bucket, storage = window.sessionStorage) {
  storage.setItem(OPERATOR_DRAFT_STORAGE_KEY, JSON.stringify(bucket));
}

function writeOperatorDraft(identity, value, {storage = window.sessionStorage, now = Date.now()} = {}) {
  const normalized = normalizeDraftIdentity(identity);
  if (draftContainsSensitiveKey(value)) throw new Error("Draft values cannot contain secret fields");
  const key = operatorDraftEntryKey(normalized);
  const record = {
    version: OPERATOR_DRAFT_VERSION,
    ...normalized,
    value,
    dirty: true,
    updated_at_ms: now,
    expires_at_ms: now + OPERATOR_DRAFT_TTL_MS
  };
  if (draftJsonBytes(record) > OPERATOR_DRAFT_MAX_BYTES) {
    throw new Error("Draft exceeds the 64 KiB per-draft limit");
  }
  const bucket = loadOperatorDraftBucket(storage, now);
  bucket.entries[key] = record;
  const compacted = compactOperatorDraftBucket(bucket, key);
  if (!compacted.entries[key]) throw new Error("Draft cannot fit within the bounded session store");
  persistOperatorDraftBucket(compacted, storage);
  return Object.freeze({...record});
}

function readOperatorDraft(identity, {storage = window.sessionStorage, now = Date.now()} = {}) {
  const key = operatorDraftEntryKey(identity);
  const bucket = loadOperatorDraftBucket(storage, now);
  persistOperatorDraftBucket(bucket, storage);
  const record = bucket.entries[key];
  return record ? Object.freeze({...record}) : null;
}

function clearOperatorDraft(identity, {storage = window.sessionStorage, now = Date.now()} = {}) {
  const key = operatorDraftEntryKey(identity);
  const bucket = loadOperatorDraftBucket(storage, now);
  const existed = Boolean(bucket.entries[key]);
  delete bucket.entries[key];
  persistOperatorDraftBucket(bucket, storage);
  return existed;
}

function hasDirtyOperatorDraft(project, {storage = window.sessionStorage, now = Date.now()} = {}) {
  const normalizedProject = String(project || "").trim();
  if (!normalizedProject) return false;
  const bucket = loadOperatorDraftBucket(storage, now);
  persistOperatorDraftBucket(bucket, storage);
  return Object.values(bucket.entries).some((record) => record.project === normalizedProject);
}
