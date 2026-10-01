import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import { Card, Empty, ErrorNote, fmtDate, useAction, useLoad } from "../ui";

export default function Releases({ ctx }: { ctx: Ctx }) {
  const rel = useLoad(() => api.releases(), []);
  const runs = useLoad(() => api.runs("approved"), []);
  const act = useAction();
  const unreleased = (runs.data ?? []).filter((r) => r.release_id === null);
  const refresh = () => { rel.reload(); runs.reload(); };
  return (
    <>
      <ErrorNote error={rel.error ?? runs.error} />
      {unreleased.length > 0 && (
        <Card title="Aprobadas, pendientes de publicar">
          <ul className="actions">
            {unreleased.map((r) => (
              <li key={r.id}>
                <span>Ejecución #{r.id} aprobada por {r.approval?.approver}.</span>{" "}
                {can(ctx.role, "release:create")
                  ? <button className="primary" disabled={act.busy} onClick={async () => { if (await act.run(() => api.createRelease(r.id))) refresh(); }}>Publicar release</button>
                  : <span className="muted">Publica el líder técnico.</span>}
              </li>
            ))}
          </ul>
          <ErrorNote error={act.error} />
        </Card>
      )}
      <Card title="Releases publicados">
        {(rel.data ?? []).length === 0 ? <Empty>Aún no hay releases.</Empty> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Versión</th><th>Ejecución</th><th>Aprobó</th><th>Readiness</th><th>SHA-256 del paquete</th><th>Fecha</th><th /></tr></thead>
              <tbody>
                {(rel.data ?? []).map((r) => (
                  <tr key={r.id}>
                    <td>{r.version}</td><td>#{r.run_id}</td><td>{String(r.manifest.approved_by ?? "")}</td>
                    <td>{String(r.manifest.readiness ?? "")}</td><td className="mono hash">{r.package_sha256}</td>
                    <td>{fmtDate(r.created_at)}</td>
                    <td><button onClick={() => act.run(() => api.downloadRelease(r.id, r.version))}>Descargar</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="note">El paquete es un zip determinista con MANIFEST.json (hash por archivo) y evidence.json. Verifica con <code>sha256sum</code>.</p>
      </Card>
    </>
  );
}
