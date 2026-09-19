function meroHubModule(api) {
  var count = 0;
  try {
    count = Number(localStorage.getItem("mero_hub_runs") || "0") + 1;
    localStorage.setItem("mero_hub_runs", String(count));
  } catch (error) {
    api.report("module.v2.storage.error", error);
  }
  api.setStatus("MODULE V2 ACTIVE");
  api.setDetail("Live update loaded without reboot or document replacement");
  api.report("module.v2.executed", "count=" + count);
  api.report("module.v2.document", document.documentElement.nodeName);
  api.report("module.v2.location", String(location.href));
}
