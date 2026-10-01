import type { Ctx } from "../context";
import { Badge, Card, Empty } from "../ui";
import { NeedInitiative } from "./need";
import { RunPicker, useInitiativeRuns } from "./runs";

const LABEL: Record<string, string> = {
  calidad_requerimiento: "Calidad del requerimiento (20)", pruebas: "Pruebas (25)", sast: "SAST (10)",
  secretos: "Secretos (7)", dependencias: "Dependencias (8)", trazabilidad: "Trazabilidad (15)",
  documentacion: "Documentación (5)", evidencia_completa: "Evidencia completa (10)",
};

export default function Security({ ctx }: { ctx: Ctx }) {
  const { runs, run, setPicked } = useInitiativeRuns(ctx);
  if (!ctx.initiative) return <NeedInitiative ctx={ctx} />;
  if (!run) return <Empty>Sin ejecuciones: ejecuta el pipeline en Development.</Empty>;
  const sec = run.evidence.security;
  const policy = run.steps.find((s) => s.name === "politica_estatica");
  return (
    <>
      <Card title="Controles de seguridad del código generado" actions={<RunPicker runs={runs} run={run} onPick={setPicked} />}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Control</th><th>Estado</th><th>Detalle</th></tr></thead>
            <tbody>
              <tr><td>Política estática (antes de ejecutar)</td><td>{policy && <Badge status={policy.status} />}</td><td>{policy?.detail}</td></tr>
              <tr><td>SAST (bandit)</td><td><Badge status={sec.bandit.status} /></td><td>alta {sec.bandit.high} · media {sec.bandit.medium} · baja {sec.bandit.low}{sec.bandit.reason ? ` (${sec.bandit.reason})` : ""}</td></tr>
              <tr><td>Escaneo de secretos</td><td><Badge status={sec.secrets.ok ? "passed" : "failed"} /></td><td>{sec.secrets.findings.length} hallazgo(s) · secreto leído de entorno: {sec.secrets.env_sourced ? "sí" : "no"}</td></tr>
              <tr><td>Dependencias</td><td><Badge status={sec.dependencies.status} /></td><td>{sec.dependencies.reason || `${sec.dependencies.vulnerabilities} vulnerabilidad(es)`}</td></tr>
            </tbody>
          </table>
        </div>
        <p className="note"><strong>«No verificado» nunca cuenta como «pasó».</strong> Una auditoría de dependencias sin red queda sin verificar y resta puntos de readiness.</p>
      </Card>
      <Card title="Composición del readiness">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Componente</th><th>Puntos</th></tr></thead>
            <tbody>
              {Object.entries(run.readiness.components).map(([k, v]) => <tr key={k}><td>{LABEL[k] ?? k}</td><td>{v}</td></tr>)}
              <tr><td><strong>Total</strong></td><td><strong>{run.readiness.score}</strong></td></tr>
            </tbody>
          </table>
        </div>
      </Card>
      <Card title="Límites que debes conocer">
        <ul>
          <li>El sandbox es de <strong>proceso</strong>, no de contenedor. Para un LLM real en producción: contenedor efímero, sin red.</li>
          <li>La política estática reduce la superficie; no prueba la ausencia de comportamiento malicioso.</li>
          <li>No hay DAST ni prueba de intrusión: NRP-23 Art. 20 i) exige pruebas anuales (proceso, no software).</li>
        </ul>
      </Card>
    </>
  );
}
