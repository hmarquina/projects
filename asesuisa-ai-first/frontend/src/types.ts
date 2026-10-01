export type Role = "viewer" | "analyst" | "tech_lead" | "security" | "approver" | "admin";

export interface Initiative { id: number; title: string; description: string; status: string; created_by: string; created_at: string }
export interface Dimension { name: string; score: number; weight: number }
export interface Ambiguity { term: string; matched_text: string; reason: string; clarifying_question: string; quote: string }
export interface RequirementAnalysis { score: number; rating: string; ready: boolean; dimensions: Dimension[]; ambiguities: Ambiguity[]; missing: string[] }
export interface AnalysisOut {
  id: number; initiative_id: number; score: number; ready: boolean; rating: string; prompt_label: string; model: string;
  pii_redactions: Record<string, number>; injection_flags: number; result: RequirementAnalysis; created_by: string; created_at: string;
}

export type ArtifactKind = "stories" | "acceptance_criteria" | "risks" | "architecture" | "api_contract";
export interface ArtifactOut {
  id: number; initiative_id: number; kind: ArtifactKind; version: number; status: string; prompt_label: string; model: string;
  analysis_id: number; requirement_ref: string; content: Record<string, unknown>; created_by: string; created_at: string;
}
export interface Story { id: string; actor: string; want: string; benefit: string; benefit_confirmed: boolean; source_quote: string }
export interface SystemRequirement { id: string; text: string }
export interface Criterion { id: string; story_id: string; origin: string; given: string; when: string; then: string; measurable_constraints: string[] }
export interface Risk { id: string; category: string; description: string; likelihood: string; impact: string; severity: number; controls: string[]; evidence: string; origin: string; owner_role: string }
export interface Component { name: string; kind: string; responsibility: string }
export interface Relation { source: string; target: string; protocol: string }
export interface Decision { decision: string; rationale: string; alternatives: string }

export interface Step { name: string; status: string; blocking: boolean; detail: string; duration_ms: number }
export interface TraceRow { ac_id: string; tests: string[]; status: string; reason: string }
export interface Readiness { score: number; threshold: number; components: Record<string, number>; unverified: string[] }
export interface Evidence {
  tests: { total: number; passed: number; failed: number };
  security: {
    bandit: { status: string; high: number; medium: number; low: number; reason?: string };
    secrets: { ok: boolean; findings: { file: string; type: string }[]; env_sourced: boolean };
    dependencies: { status: string; reason?: string; vulnerabilities: number };
  };
}
export interface RunOut {
  id: number; initiative_id: number; status: string; steps: Step[]; readiness: Readiness; traceability: TraceRow[];
  files: Record<string, string>; evidence: Evidence; evidence_ref: string; created_by: string; created_at: string;
  approval: { decision: string; approver: string; comment: string; risk_acknowledged: boolean; at: string } | null;
  release_id: number | null;
}
export interface ReleaseOut { id: number; run_id: number; version: string; package_sha256: string; manifest: Record<string, unknown>; created_by: string; created_at: string }
export interface AuditEvent {
  id: number; timestamp: string; user: string; role: string; action: string; ai_model: string; prompt_version: string;
  input_ref: string; output_ref: string; approval: string; decision: string; resulting_artifact: string; hash: string;
}

export interface OrgMetric {
  key: string; label: string; unit: string; baseline: number; target_base: number; target_stretch: number; better: "up" | "down";
  current: number | null; trend: number[]; confidence: string; source: string; status: string;
}
export interface Metrics {
  organizational: OrgMetric[];
  platform: {
    initiatives: number; analyses: number; requirement_quality_avg: number | null; requirement_quality_series: number[];
    ready_rate: number | null; ai_artifacts: Record<string, number>; pipeline_runs: number; pipeline_blocked_rate: number | null;
    readiness_avg: number | null; readiness_series: number[]; automated_criteria_coverage: number | null; approvals: number;
    rejections: number; releases: number; audit_events: number; audit_intact: boolean;
  };
  model: {
    scenarios: Record<string, { capacity: number; value_capacity: number }>; demand_growth: number;
    required_scope_removed_for_2x_base: number; note: string;
    simulation: { value_median: number; value_p10: number; value_p90: number; p_value_ge_1_3: number; p_value_ge_1_5: number; p_value_ge_2_0: number };
  };
  disclaimer: string;
}
