const OPERATOR_MUTATION_STATE_LIMIT = 128;
const operatorMutationInflight = new Map();
const operatorMutationStates = new Map();
let operatorMutationSequence = 0;

function operatorMutationKey(kind, ...components) {
  const normalizedKind = String(kind || "").trim();
  if (!/^[a-z][a-z0-9-]{0,63}$/.test(normalizedKind)) {
    throw new Error("Mutation key requires a bounded operation kind");
  }
  const values = components.map((component) => {
    const value = String(component || "").trim();
    if (!value || value.length > 160) throw new Error("Mutation key requires bounded identity components");
    return value;
  });
  if (!values.length) throw new Error("Mutation key requires at least one identity component");
  return JSON.stringify([normalizedKind, ...values]);
}

function mutationGuardState(key) {
  const state = operatorMutationStates.get(String(key));
  return state ? Object.freeze({...state}) : Object.freeze({status: "idle"});
}

function compactOperatorMutationStates() {
  if (operatorMutationStates.size <= OPERATOR_MUTATION_STATE_LIMIT) return;
  const removable = [...operatorMutationStates.entries()]
    .filter(([key]) => !operatorMutationInflight.has(key))
    .sort(([, left], [, right]) => left.sequence - right.sequence);
  while (operatorMutationStates.size > OPERATOR_MUTATION_STATE_LIMIT && removable.length) {
    operatorMutationStates.delete(removable.shift()[0]);
  }
}

function setOperatorMutationState(key, status, detail = {}, onState = null) {
  const state = {
    status,
    ...detail,
    sequence: ++operatorMutationSequence
  };
  operatorMutationStates.set(key, state);
  compactOperatorMutationStates();
  if (onState) onState(Object.freeze({...state}));
  return state;
}

function mutationConflict(error) {
  return error?.status === 409;
}

function runGuardedMutation({key, execute, readWinner = null, onState = null}) {
  const normalizedKey = String(key || "").trim();
  if (!normalizedKey) throw new Error("Guarded mutation requires a key");
  if (typeof execute !== "function") throw new Error("Guarded mutation requires execute");
  const existing = operatorMutationInflight.get(normalizedKey);
  if (existing) return existing;

  setOperatorMutationState(normalizedKey, "pending", {error: "", winner: null}, onState);
  const pending = (async () => {
    try {
      const result = await execute();
      setOperatorMutationState(normalizedKey, "succeeded", {result, error: "", winner: null}, onState);
      return Object.freeze({status: "succeeded", result, winner: null});
    } catch (error) {
      if (mutationConflict(error)) {
        if (typeof readWinner !== "function") {
          setOperatorMutationState(normalizedKey, "failed", {error: "Conflict readback is unavailable", winner: null}, onState);
          throw error;
        }
        try {
          const winner = await readWinner(error);
          setOperatorMutationState(normalizedKey, "conflict", {error: error.message, winner}, onState);
          return Object.freeze({status: "conflict", result: null, winner});
        } catch (readError) {
          setOperatorMutationState(normalizedKey, "failed", {error: readError.message, winner: null}, onState);
          throw readError;
        }
      }
      setOperatorMutationState(normalizedKey, "failed", {error: error.message, winner: null}, onState);
      throw error;
    } finally {
      operatorMutationInflight.delete(normalizedKey);
    }
  })();
  operatorMutationInflight.set(normalizedKey, pending);
  return pending;
}
