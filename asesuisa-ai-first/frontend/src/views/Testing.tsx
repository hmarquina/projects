import type { Ctx } from "../context";
import { Badge, Card, Empty, Tile } from "../ui";
import { NeedInitiative } from "./need";
import { RunPicker, useInitiativeRuns } from "./runs";

export default function Testing({ ctx }: { ctx: Ctx }) {
  const { runs, run, setPicked } = useInitiativeRuns(ctx);
  if (!ctx.initiative) return <NeedInitiative ctx={ctx} />;
  if (!run) return <Empty>Sin ejecuciones: ejecuta el pipeline en Development.</Empty>;
  const t = run.evidence.tests;
  const auto = run.traceability.filter((r) => r.status === "verified" || r.status === "smoke").length;
  return (
    <>
      <Card title="Pruebas generadas y ejecutadas" actions={<RunPicker runs={runs} run={run} onPick={setPicked} />}>
        <div className="tiles">
          <Tile label="Pruebas" value={t.total} />
          <Tile label="Pasaron" value={t.passed} />
          <Tile label="Fallaron" value={t.failed} />
          <Tile label="Criterios con prueba automática" value={`${auto}/${run.traceability.length}`} hint="Calculado con resultados reales" />
        </div>
        <p className="note">Las pruebas verifican el contrato (todo código HTTP debe estar declarado) y se validan por mutación: si el servicio se rompe, deben fallar.</p>
      </Card>
      <Card title="Trazabilidad criterio de aceptación → prueba">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Criterio</th><th>Estado</th><th>Pruebas</th><th>Nota</th></tr></thead>
            <tbody>
              {run.traceability.map((r) => (
                <tr key={r.ac_id}>
                  <td className="mono">{r.ac_id}</td><td><Badge status={r.status} /></td>
                  <td className="mono">{r.tests.length ? r.tests.join(", ") : "—"}</td><td>{r.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {run.readiness.unverified.length > 0 && (
          <>
            <h3>No verificado</h3>
            <ul>{run.readiness.unverified.map((u) => <li key={u}>{u}</li>)}</ul>
          </>
        )}
      </Card>
    </>
  );
}
