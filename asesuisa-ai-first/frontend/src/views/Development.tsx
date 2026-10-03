import { useState } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import { Badge, Card, Empty, ErrorNote, Meter, useAction } from "../ui";
import { BlockBreakdown } from "./BlockBreakdown";
import { NeedInitiative } from "./need";
import { RunPicker, useInitiativeRuns } from "./runs";

export default function Development({ ctx }: { ctx: Ctx }) {
  const { runs, run, setPicked, reload, error } = useInitiativeRuns(ctx);
  const exec = useAction();
  const [path, setPath] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const view = useAction();
  if (!ctx.initiative) return <NeedInitiative ctx={ctx} />;
  const ini = ctx.initiative;

  const open = async (p: string) => {
    if (!run) return;
    const text = await view.run(() => api.file(run.id, p));
    if (text !== undefined) { setPath(p); setContent(text); }
  };

  return (
    <>
      <Card title="Pipeline de entrega" actions={<RunPicker runs={runs} run={run} onPick={setPicked} />}>
        {can(ctx.role, "pipeline:run") ? (
          <button className="primary" disabled={exec.busy}
            onClick={async () => { if (await exec.run(() => api.runPipeline(ini.id))) reload(); }}>
            {exec.busy ? "Ejecutando (genera, prueba y escanea)…" : "Ejecutar pipeline"}
          </button>
        ) : (
          <p className="note">Tu rol ({ctx.role}) no ejecuta el pipeline: ejecuta el líder técnico; aprueba otra persona.</p>
        )}
        <ErrorNote error={exec.error ?? error} />
        <p className="note">Requiere los 5 artefactos vigentes. El código generado pasa una política estática antes de ejecutarse.</p>
      </Card>
      {!run ? <Empty>Sin ejecuciones para esta iniciativa.</Empty> : (
        <>
          <Card title={`Ejecución #${run.id}`} actions={<Badge status={run.status} />}>
            <div className="score">
              <div className="score-number" aria-label="Readiness">{run.readiness.score}<span>/100</span></div>
              <div className="score-body">
                <Meter value={run.readiness.score} marker={run.readiness.threshold} label="Readiness" />
                <p>Umbral de release: {run.readiness.threshold}. Es un agregado heurístico: los bloqueos duros mandan sobre el score.</p>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Paso</th><th>Estado</th><th title="Un paso bloqueante frena la ejecución solo si falla. 'Sin verificar' no bloquea: resta puntos al readiness y queda como riesgo residual.">¿Compuerta?</th><th>Detalle</th><th>ms</th></tr></thead>
                <tbody>
                  {run.steps.map((s) => (
                    <tr key={s.name}>
                      <td className="mono">{s.name}</td><td><Badge status={s.status} /></td>
                      <td>{s.blocking ? (s.status === "skipped" ? "sí · sin verificar (no bloquea)" : "sí") : "no"}</td><td>{s.detail}</td><td>{s.duration_ms}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <BlockBreakdown run={run} />
          <Card title="Archivos generados">
            <ul className="files">
              {Object.keys(run.files).map((f) => (
                <li key={f}><button className="link mono" onClick={() => open(f)}>{f}</button></li>
              ))}
            </ul>
            <ErrorNote error={view.error} />
            {path && (<><h3 className="mono">{path}</h3><pre className="code" tabIndex={0}>{content || "(vacío)"}</pre></>)}
          </Card>
        </>
      )}
    </>
  );
}
