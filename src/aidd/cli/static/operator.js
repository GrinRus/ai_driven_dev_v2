(() => {
  const scripts = [
    "/operator-surface-parity.js",
    "/operator-presentation.js",
    "/operator-api-state.js",
    "/operator-shell-rendering.js",
    "/operator-dashboard-actions.js",
    "/operator-onboarding.js",
    "/operator-artifacts-documents.js",
    "/operator-questions.js",
    "/operator-approvals-interventions.js",
    "/operator-logs-jobs.js",
    "/operator-next-flow-actions.js",
    "/operator-next-flow-view.js",
    "/operator-control-center.js",
    "/operator-stage-cockpit.js",
    "/operator-main.js"
  ];

  function loadScript(index) {
    if (index >= scripts.length) return;
    const script = document.createElement("script");
    script.src = scripts[index];
    script.async = false;
    script.onload = () => loadScript(index + 1);
    script.onerror = () => {
      console.error(`Failed to load AIDD operator asset: ${scripts[index]}`);
    };
    document.head.appendChild(script);
  }

  loadScript(0);
})();
