import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import type { ArtifactKind, ArtifactOut, Criterion, Risk, Story, SystemRequirement } from "../types";
import { Badge, Card, Empty, ErrorNote, fmtDate, useAction, useLoad } from "../ui";
import { NeedInitiative } from "./need";

export const KIND_LABEL: Record<ArtifactKind, string> = {
  stories: "Historias de usuario", acceptance_criteria: "Criterios de aceptación", risks: "Riesgos",
  architecture: "Arquitectura", api_contract: "Contrato de API",
};
export const ALL_KINDS: ArtifactKind[] = ["stories", "acceptance_criteria", "risks", "architecture", "api_contract"];

export const latestByKind = (items: ArtifactOut[]): Partial<Record<ArtifactKind, ArtifactOut>> => {
  const out: Partial<Record<ArtifactKind, ArtifactOut>> = {};
  for (const a of items) if (!out[a.kind] || (out[a.kind]?.version ?? 0) < a.version) out[a.kind] = a;
  return out;
};

export function GenerateButtons({ id, kinds, onDone, role }: { id: number; kinds: ArtifactKind[]; onDone: () => void; role: Ctx["role"] }) {
  const { busy, error, run } = useAction();
  if (!can(role, "ai:generate")) return <p className="note">Tu rol ({role}) no puede generar artefactos.</p>;
  return (
    <>
      <div className="row">
        {kinds.map((k) => (
          <button key={k} disabled={busy} onClick={async () => { if (await run(() => api.generate(id, k))) onDone(); }}>
            Generar {KIND_LABEL[k].toLowerCase()}
          </button>
        ))}
      </div>
      <ErrorNote error={error} />
    </>
  );
}

export default function AiAnalysis({ ctx }: { ctx: Ctx }) {
  const ini = ctx.initiative;
  const analyses = useLoad(() => (ini ? api.analyses(ini.id) : Promise.resolve([])), [ini?.id]);
  const arts = useLoad(() => (ini ? api.artifacts(ini.id) : Promise.resolve([])), [ini?.id]);
  if (!ini) return <NeedInitiative ctx={ctx} />;
  const latest = latestByKind(arts.data ?? []);
  const stories = latest.stories?.content as { stories?: Story[]; system_requirements?: SystemRequirement[] } | undefined;
  const criteria = (latest.acceptance_criteria?.content as { criteria?: Criterion[] } | undefined)?.criteria;
  const risks = (latest.risks?.content as { risks?: Risk[] } | undefined)?.risks;

  return (
    <>
      <Card title="Historial de análisis">
        <ErrorNote error={analyses.error} />
        {(analyses.data ?? []).length === 0 ? <Empty>Sin análisis. Ve a Requirements.</Empty> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Id</th><th>Score</th><th>Estado</th><th>Modelo</th><th>Prompt (versión+huella)</th><th>Señales</th><th>Fecha</th></tr></thead>
              <tbody>
                {(analyses.data ?? []).map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td><td>{a.score}</td>
                    <td><Badge status={a.ready ? "passed" : "blocked"} tone={a.ready ? "ok" : "bad"} /></td>
                    <td>{a.model}</td><td className="mono">{a.prompt_label}</td>
                    <td>{a.injection_flags > 0 ? `injection×${a.injection_flags}` : "—"}{Object.keys(a.pii_redactions).length ? " · PII redactada" : ""}</td>
                    <td>{fmtDate(a.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <Card title="Artefactos generados por IA (borrador hasta aprobación)">
        <GenerateButtons id={ini.id} kinds={ALL_KINDS} role={ctx.role} onDone={arts.reload} />
        <p className="note">La generación exige un análisis vigente con score ≥ 75 (Definition of Ready). Cada elemento cita el texto fuente.</p>
        <ErrorNote error={arts.error} />
        <ul className="inline">
          {ALL_KINDS.map((k) => (
            <li key={k}>{KIND_LABEL[k]}: {latest[k] ? <>v{latest[k]?.version} <Badge status={latest[k]?.status ?? "draft"} /></> : <span className="muted">sin generar</span>}</li>
          ))}
        </ul>
      </Card>
      {stories?.stories && (
        <Card title="Historias de usuario">
          <ul className="findings">
            {stories.stories.map((s) => (
              <li key={s.id}>
                <strong>{s.id}</strong> Como <em>{s.actor}</em>, quiero {s.want}, para {s.benefit}
                {!s.benefit_confirmed && <> <Badge status="manual" /> beneficio sin confirmar</>}
                <div className="muted">Fuente: «{s.source_quote}»</div>
              </li>
            ))}
          </ul>
          {stories.system_requirements && stories.system_requirements.length > 0 && (
            <>
              <h3>Requisitos del sistema</h3>
              <ul>{stories.system_requirements.map((r) => <li key={r.id}><strong>{r.id}</strong> {r.text}</li>)}</ul>
            </>
          )}
        </Card>
      )}
      {criteria && (
        <Card title="Criterios de aceptación">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Id</th><th>Origen</th><th>Dado</th><th>Cuando</th><th>Entonces</th></tr></thead>
              <tbody>
                {criteria.map((c) => (
                  <tr key={c.id}>
                    <td className="mono">{c.id}</td>
                    <td><Badge status={c.origin === "requirement" ? "verified" : "manual"} tone={c.origin === "requirement" ? "info" : "muted"} />{" "}{c.origin === "requirement" ? "requerimiento" : "control base"}</td>
                    <td>{c.given}</td><td>{c.when}</td><td>{c.then}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
      {risks && (
        <Card title="Riesgos">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Id</th><th>Categoría</th><th>Sev.</th><th>Descripción</th><th>Controles</th><th>Evidencia</th></tr></thead>
              <tbody>
                {risks.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td><td>{r.category}</td><td>{r.severity}</td><td>{r.description}</td>
                    <td>{r.controls.join("; ")}</td><td>{r.origin === "baseline" ? "base de la organización" : `«${r.evidence}»`}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
