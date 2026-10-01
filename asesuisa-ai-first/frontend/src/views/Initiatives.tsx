import { useState, type FormEvent } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import { Badge, Card, Empty, ErrorNote, fmtDate, useAction } from "../ui";

const EXAMPLE =
  "El sistema debe ser rápido y fácil de usar para gestionar reclamos de asegurados, con un proceso adecuado, etc.";

export default function Initiatives({ ctx }: { ctx: Ctx }) {
  const [title, setTitle] = useState("Digitalización del proceso de reclamos");
  const [description, setDescription] = useState(EXAMPLE);
  const { busy, error, run } = useAction();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const created = await run(() => api.createInitiative(title, description));
    if (created) {
      ctx.refresh();
      ctx.select(created.id);
      ctx.go("requirements");
    }
  };

  return (
    <>
      <Card title="Iniciativas">
        {ctx.initiatives.length === 0 ? (
          <Empty>Aún no hay iniciativas.</Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Id</th><th>Título</th><th>Estado</th><th>Creada por</th><th>Fecha</th><th /></tr></thead>
              <tbody>
                {ctx.initiatives.map((i) => (
                  <tr key={i.id} className={ctx.initiative?.id === i.id ? "selected" : ""}>
                    <td>{i.id}</td><td>{i.title}</td><td><Badge status={i.status} /></td><td>{i.created_by}</td>
                    <td>{fmtDate(i.created_at)}</td>
                    <td><button onClick={() => ctx.select(i.id)}>Seleccionar</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      {can(ctx.role, "initiative:create") ? (
        <Card title="Registrar iniciativa">
          <form onSubmit={submit} className="form">
            <label>Título
              <input value={title} onChange={(e) => setTitle(e.target.value)} minLength={3} maxLength={200} required />
            </label>
            <label>Requerimiento (datos sintéticos; no se aceptan datos personales)
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={5} maxLength={10000} />
            </label>
            <p className="note">El texto de ejemplo es deliberadamente pobre: el siguiente paso lo analiza y lo bloquea.</p>
            <ErrorNote error={error} />
            <button className="primary" disabled={busy}>{busy ? "Registrando…" : "Registrar y analizar"}</button>
          </form>
        </Card>
      ) : (
        <p className="note">Tu rol ({ctx.role}) no puede registrar iniciativas.</p>
      )}
    </>
  );
}
