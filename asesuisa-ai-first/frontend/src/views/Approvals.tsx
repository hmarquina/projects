import { useState } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import type { RunOut } from "../types";
import { Badge, Card, Empty, ErrorNote, fmtDate, useAction, useLoad } from "../ui";

export const MIN_COMMENT = 5;

export function DecisionForm({ run, onDone }: { run: RunOut; onDone: () => void }) {
  const [comment, setComment] = useState("");
  const [ack, setAck] = useState(false);
  const { busy, error, run: act } = useAction();
  const commentOk = comment.trim().length >= MIN_COMMENT;
  const decide = async (d: "approved" | "rejected") => {
    if (await act(() => api.decide(run.id, d, comment.trim(), ack))) onDone();
  };
  return (
    <form className="form" onSubmit={(e) => e.preventDefault()}>
      <label>Comentario de la decisión (mínimo {MIN_COMMENT} caracteres)
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} maxLength={1000} />
      </label>
      <label className="check">
        <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
        Reconozco los riesgos residuales y lo que quedó sin verificar
      </label>
      <ErrorNote error={error} />
      <div className="row">
        <button className="primary" disabled={busy || !commentOk || !ack} onClick={() => decide("approved")}>Aprobar</button>
        <button disabled={busy || !commentOk} onClick={() => decide("rejected")}>Rechazar</button>
      </div>
    </form>
  );
}

export default function Approvals({ ctx }: { ctx: Ctx }) {
  const runs = useLoad(() => api.runs(), []);
  const all = runs.data ?? [];
  const pending = all.filter((r) => r.status === "awaiting_approval");
  const decided = all.filter((r) => r.status === "approved" || r.status === "rejected");
  const canDecide = can(ctx.role, "release:approve");
  return (
    <>
      <ErrorNote error={runs.error} />
      <Card title="Esperan una decisión humana">
        {!canDecide && <p className="note">Tu rol ({ctx.role}) no decide: aprueba una persona con rol approver que <strong>no haya participado</strong> en el trabajo.</p>}
        {pending.length === 0 ? <Empty>No hay ejecuciones pendientes de aprobación.</Empty> : pending.map((r) => (
          <article key={r.id} className="decision">
            <h3>Ejecución #{r.id} · iniciativa {r.initiative_id} <Badge status={r.status} /></h3>
            <p>Readiness <strong>{r.readiness.score}</strong>/{r.readiness.threshold} · pruebas {r.evidence.tests.passed}/{r.evidence.tests.total} · ejecutada por {r.created_by} el {fmtDate(r.created_at)}</p>
            {r.readiness.unverified.length > 0 && (
              <>
                <strong>Sin verificar (lo estás aceptando):</strong>
                <ul>{r.readiness.unverified.map((u) => <li key={u}>{u}</li>)}</ul>
              </>
            )}
            {canDecide && <DecisionForm run={r} onDone={runs.reload} />}
          </article>
        ))}
      </Card>
      <Card title="Decisiones registradas">
        {decided.length === 0 ? <Empty>Aún no hay decisiones.</Empty> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Ejecución</th><th>Decisión</th><th>Aprobador</th><th>Comentario</th><th>Riesgos reconocidos</th><th>Fecha</th></tr></thead>
              <tbody>
                {decided.map((r) => (
                  <tr key={r.id}>
                    <td>#{r.id}</td><td><Badge status={r.status} /></td><td>{r.approval?.approver}</td>
                    <td>{r.approval?.comment}</td><td>{r.approval?.risk_acknowledged ? "sí" : "no"}</td>
                    <td>{r.approval ? fmtDate(r.approval.at) : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
