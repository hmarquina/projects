import { useState } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import { Badge, Card, Empty, ErrorNote, fmtDate, useAction, useLoad } from "../ui";

interface Verification { intact: boolean; first_tampered_id: number | null }

export default function Audit({ ctx }: { ctx: Ctx }) {
  const allowed = can(ctx.role, "audit:read");
  const events = useLoad(() => (allowed ? api.audit(100) : Promise.resolve([])), [allowed]);
  const verify = useAction();
  const [verified, setVerified] = useState<Verification | null>(null);

  if (!allowed) {
    return (
      <Card title="Auditoría">
        <p className="note">Tu rol ({ctx.role}) no consulta la bitácora. Pueden hacerlo security, approver y admin.</p>
      </Card>
    );
  }

  const check = async () => {
    const r = await verify.run(() => api.verifyAudit());
    if (r) setVerified(r);
  };

  return (
    <Card
      title="Bitácora append-only (hash encadenado)"
      actions={<button disabled={verify.busy} onClick={check}>Verificar integridad</button>}
    >
      {verified && (
        <p className={verified.intact ? "ok-note" : "warn-note"} role="status">
          {verified.intact
            ? "Cadena íntegra: ningún evento fue alterado."
            : `¡Cadena alterada! Primer evento afectado: #${verified.first_tampered_id}.`}
        </p>
      )}
      <ErrorNote error={events.error ?? verify.error} />
      {(events.data ?? []).length === 0 ? <Empty>Sin eventos.</Empty> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>#</th><th>Fecha</th><th>Usuario</th><th>Rol</th><th>Acción</th><th>Modelo</th><th>Prompt</th><th>Decisión</th><th>Aprobación</th><th>Artefacto</th></tr>
            </thead>
            <tbody>
              {(events.data ?? []).map((e) => (
                <tr key={e.id}>
                  <td>{e.id}</td><td>{fmtDate(e.timestamp)}</td><td>{e.user}</td><td>{e.role}</td>
                  <td className="mono">{e.action}</td><td>{e.ai_model || "—"}</td><td className="mono">{e.prompt_version || "—"}</td>
                  <td>{e.decision ? <Badge status={e.decision} /> : "—"}</td><td>{e.approval || "—"}</td>
                  <td className="mono">{e.resulting_artifact || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="note">Se registran referencias (hashes), no el contenido de las entradas ni de las salidas.</p>
    </Card>
  );
}
