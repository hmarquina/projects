import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import { Card, ErrorNote, Tile, useLoad } from "../ui";
import { ModelCard, OrgTable } from "./shared";

const dash = (v: number | null, suffix = ""): string => (v === null ? "—" : `${v}${suffix}`);

export default function Dashboard({ ctx }: { ctx: Ctx }) {
  const m = useLoad(() => api.metrics(), []);
  const runs = useLoad(() => api.runs(), []);
  const pending = (runs.data ?? []).filter((r) => r.status === "awaiting_approval");
  const blocked = (runs.data ?? []).filter((r) => r.status === "blocked");
  const toRelease = (runs.data ?? []).filter((r) => r.status === "approved" && r.release_id === null);

  const actions: { text: string; go: () => void; label: string }[] = [];
  if (ctx.initiatives.length === 0 && can(ctx.role, "initiative:create"))
    actions.push({ text: "No hay iniciativas registradas.", label: "Registrar la primera", go: () => ctx.go("initiatives") });
  if (pending.length && can(ctx.role, "release:approve"))
    actions.push({ text: `${pending.length} ejecución(es) esperan una decisión humana.`, label: "Ir a Approvals", go: () => ctx.go("approvals") });
  if (blocked.length)
    actions.push({ text: `${blocked.length} ejecución(es) bloqueadas por los controles.`, label: "Ver en Development", go: () => ctx.go("development") });
  if (toRelease.length && can(ctx.role, "release:create"))
    actions.push({ text: `${toRelease.length} ejecución(es) aprobadas sin release.`, label: "Ir a Releases", go: () => ctx.go("releases") });

  const p = m.data?.platform;
  return (
    <>
      <p className="banner" role="note">
        Datos 100% sintéticos · Proveedor de IA: <strong>mock determinista</strong> (no es un LLM) ·
        Las métricas organizacionales no tienen dato: el caso solo aporta el baseline.
      </p>
      <ErrorNote error={m.error} />
      <Card title="Acciones pendientes">
        {actions.length === 0 ? (
          <p className="empty">Nada pendiente para tu rol en este momento.</p>
        ) : (
          <ul className="actions">
            {actions.map((a) => (
              <li key={a.label}><span>{a.text}</span> <button className="link" onClick={a.go}>{a.label}</button></li>
            ))}
          </ul>
        )}
      </Card>
      {p && (
        <Card title="Uso de la plataforma (datos reales del MVP)">
          <div className="tiles">
            <Tile label="Iniciativas" value={p.initiatives} />
            <Tile label="Calidad promedio del requerimiento" value={dash(p.requirement_quality_avg, "/100")} hint="Umbral de Ready: 75" />
            <Tile label="Requerimientos listos" value={dash(p.ready_rate, "%")} />
            <Tile label="Ejecuciones del pipeline" value={p.pipeline_runs} hint={`Tasa de bloqueo: ${dash(p.pipeline_blocked_rate, "%")}`} />
            <Tile label="Readiness promedio" value={dash(p.readiness_avg, "/100")} hint="Umbral de release: 85" />
            <Tile label="Criterios con prueba automática" value={dash(p.automated_criteria_coverage, "%")} />
            <Tile label="Aprobaciones / rechazos" value={`${p.approvals} / ${p.rejections}`} />
            <Tile label="Releases" value={p.releases} />
            <Tile label="Auditoría" value={p.audit_intact ? "íntegra" : "ALTERADA"} hint={`${p.audit_events} eventos`} />
          </div>
        </Card>
      )}
      {m.data && <ModelCard model={m.data.model} />}
      {m.data && (
        <Card title="Baseline · Target · Current · Trend · Confianza">
          <OrgTable metrics={m.data.organizational} />
          <p className="note">{m.data.disclaimer}</p>
        </Card>
      )}
    </>
  );
}
