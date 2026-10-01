import type { AnalysisOut, Metrics, RunOut } from "../types";

export const metricsFixture: Metrics = {
  organizational: [
    { key: "lead_time", label: "Lead time", unit: "semanas", baseline: 20, target_base: 12.5, target_stretch: 10, better: "down", current: null, trend: [], confidence: "media", source: "VSM", status: "sin dato: requiere medición real" },
    { key: "rework", label: "Retrabajo y aclaraciones", unit: "%", baseline: 25, target_base: 12, target_stretch: 8, better: "down", current: null, trend: [], confidence: "media-baja", source: "Muestreo", status: "sin dato: requiere medición real" },
  ],
  platform: {
    initiatives: 1, analyses: 1, requirement_quality_avg: 100, requirement_quality_series: [100], ready_rate: 100, ai_artifacts: {},
    pipeline_runs: 1, pipeline_blocked_rate: 0, readiness_avg: 98, readiness_series: [98], automated_criteria_coverage: 87.5,
    approvals: 0, rejections: 0, releases: 0, audit_events: 12, audit_intact: true,
  },
  model: {
    scenarios: { conservative: { capacity: 1.22, value_capacity: 1.28 }, base: { capacity: 1.48, value_capacity: 1.61 }, stretch: { capacity: 1.8, value_capacity: 2.0 } },
    demand_growth: 1.5, required_scope_removed_for_2x_base: 0.258, note: "",
    simulation: { value_median: 1.42, value_p10: 1.31, value_p90: 1.54, p_value_ge_1_3: 0.92, p_value_ge_1_5: 0.19, p_value_ge_2_0: 0 },
  },
  disclaimer: "Las métricas organizacionales no tienen dato.",
};

export const analysisFixture = (over: Partial<AnalysisOut["result"]> = {}, extra: Partial<AnalysisOut> = {}): AnalysisOut => ({
  id: 1, initiative_id: 1, score: 31, ready: false, rating: "insuficiente", prompt_label: "requirement_quality@1.0.0+abc", model: "mock-heuristic-1",
  pii_redactions: {}, injection_flags: 0, created_by: "demo_analyst", created_at: "2026-10-01T10:00:00Z",
  result: {
    score: 31, rating: "insuficiente", ready: false,
    dimensions: [{ name: "claridad", score: 25, weight: 30 }],
    ambiguities: [{ term: "rápido", matched_text: "rápido", reason: "No define un tiempo", clarifying_question: "¿Cuál es el tiempo máximo?", quote: "El sistema debe ser rápido." }],
    missing: ["Falta al menos un criterio medible (tiempo, porcentaje, volumen)."],
    ...over,
  },
  ...extra,
});

export const runFixture = (over: Partial<RunOut> = {}): RunOut => ({
  id: 7, initiative_id: 1, status: "awaiting_approval",
  steps: [{ name: "pruebas", status: "passed", blocking: true, detail: "14/14 pruebas pasaron", duration_ms: 900 }],
  readiness: { score: 98, threshold: 85, components: { pruebas: 25 }, unverified: ["AC-SR-2: requiere verificación manual/operativa"] },
  traceability: [{ ac_id: "AC-US-1-1", tests: ["test_create_ok"], status: "verified", reason: "camino feliz" }],
  files: { "generated_service/app.py": "abc" },
  evidence: {
    tests: { total: 14, passed: 14, failed: 0 },
    security: {
      bandit: { status: "passed", high: 0, medium: 0, low: 3 },
      secrets: { ok: true, findings: [], env_sourced: true },
      dependencies: { status: "skipped", reason: "auditoría deshabilitada", vulnerabilities: 0 },
    },
  },
  evidence_ref: "sha256:abc", created_by: "demo_tech_lead", created_at: "2026-10-01T10:00:00Z", approval: null, release_id: null, ...over,
});
