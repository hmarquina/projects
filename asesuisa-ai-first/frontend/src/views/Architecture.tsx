import { api } from "../api";
import type { Ctx } from "../context";
import type { Component, Decision, Relation } from "../types";
import { Card, Empty, ErrorNote, useLoad } from "../ui";
import { GenerateButtons, latestByKind } from "./AiAnalysis";
import { NeedInitiative } from "./need";

interface OpenApi {
  info: { title: string };
  paths: Record<string, Record<string, { summary: string; responses: Record<string, unknown> }>>;
}

export default function Architecture({ ctx }: { ctx: Ctx }) {
  const ini = ctx.initiative;
  const arts = useLoad(() => (ini ? api.artifacts(ini.id) : Promise.resolve([])), [ini?.id]);
  if (!ini) return <NeedInitiative ctx={ctx} />;
  const latest = latestByKind(arts.data ?? []);
  const arch = latest.architecture?.content as
    | { components: Component[]; relations: Relation[]; decisions: Decision[]; nfr: string[]; assumptions: string[] } | undefined;
  const spec = (latest.api_contract?.content as { openapi?: OpenApi } | undefined)?.openapi;

  return (
    <>
      <Card title="Generar">
        <GenerateButtons id={ini.id} kinds={["architecture", "api_contract"]} role={ctx.role} onDone={arts.reload} />
        <ErrorNote error={arts.error} />
      </Card>
      {!arch && !spec && <Empty>Aún no hay arquitectura ni contrato. Genéralos (requiere un requerimiento listo).</Empty>}
      {arch && (
        <Card title="Propuesta de arquitectura">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Componente</th><th>Tipo</th><th>Responsabilidad</th></tr></thead>
              <tbody>{arch.components.map((c) => <tr key={c.name}><td>{c.name}</td><td>{c.kind}</td><td>{c.responsibility}</td></tr>)}</tbody>
            </table>
          </div>
          <h3>Relaciones</h3>
          <ul>{arch.relations.map((r) => <li key={`${r.source}-${r.target}`}>{r.source} → {r.target} <span className="muted">({r.protocol})</span></li>)}</ul>
          <h3>Decisiones</h3>
          <ul className="findings">
            {arch.decisions.map((d) => (
              <li key={d.decision}><strong>{d.decision}</strong> — {d.rationale}<div className="muted">Alternativas: {d.alternatives}</div></li>
            ))}
          </ul>
          {arch.assumptions.map((a) => <p key={a} className="note">{a}</p>)}
        </Card>
      )}
      {spec && (
        <Card title={`Contrato OpenAPI · ${spec.info.title}`}>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Método</th><th>Ruta</th><th>Descripción</th><th>Respuestas declaradas</th></tr></thead>
              <tbody>
                {Object.entries(spec.paths).flatMap(([path, methods]) =>
                  Object.entries(methods).map(([m, op]) => (
                    <tr key={`${m}-${path}`}>
                      <td className="mono">{m.toUpperCase()}</td><td className="mono">{path}</td><td>{op.summary}</td>
                      <td className="mono">{Object.keys(op.responses).join(", ")}</td>
                    </tr>
                  )),
                )}
              </tbody>
            </table>
          </div>
          <p className="note">Todas las operaciones exigen autenticación y declaran 401 y 403. Es un borrador generado: requiere revisión humana.</p>
        </Card>
      )}
    </>
  );
}
