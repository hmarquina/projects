import { useEffect, useState } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import { can } from "../permissions";
import type { AnalysisOut } from "../types";
import { Badge, Card, Empty, ErrorNote, Meter, useAction, useLoad } from "../ui";
import { NeedInitiative } from "./need";

export function AnalysisResult({ a }: { a: AnalysisOut }) {
  const r = a.result;
  return (
    <>
      <div className="score">
        <div className="score-number" aria-label="Score de calidad">{r.score}<span>/100</span></div>
        <div className="score-body">
          <Meter value={r.score} marker={75} label="Calidad del requerimiento" />
          <p>
            <Badge status={r.ready ? "passed" : "blocked"} tone={r.ready ? "ok" : "bad"} />{" "}
            {r.ready ? "Cumple la Definition of Ready (≥ 75)." : "No cumple la Definition of Ready (≥ 75): se bloquea la generación."}
          </p>
        </div>
      </div>
      {(a.injection_flags > 0 || Object.keys(a.pii_redactions).length > 0) && (
        <p className="warn-note" role="alert">
          {a.injection_flags > 0 && <>Se detectaron {a.injection_flags} señal(es) de prompt injection (el resultado no se alteró). </>}
          {Object.keys(a.pii_redactions).length > 0 && <>PII redactada antes del modelo: {Object.entries(a.pii_redactions).map(([k, v]) => `${k}×${v}`).join(", ")}.</>}
        </p>
      )}
      <h3>Dimensiones</h3>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Dimensión</th><th>Peso</th><th>Puntaje</th></tr></thead>
          <tbody>
            {r.dimensions.map((d) => (
              <tr key={d.name}><td>{d.name}</td><td>{d.weight}</td><td>{d.score}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3>Ambigüedades ({r.ambiguities.length})</h3>
      {r.ambiguities.length === 0 ? <Empty>Sin ambigüedades detectadas.</Empty> : (
        <ul className="findings">
          {r.ambiguities.map((x) => (
            <li key={x.term}>
              <strong>«{x.matched_text}»</strong> — {x.reason}
              <div className="muted">Cita: {x.quote}</div>
              <div>Pregunta de aclaración: <em>{x.clarifying_question}</em></div>
            </li>
          ))}
        </ul>
      )}
      {r.missing.length > 0 && (
        <>
          <h3>Faltantes</h3>
          <ul>{r.missing.map((m) => <li key={m}>{m}</li>)}</ul>
        </>
      )}
      <p className="muted">Modelo: {a.model} · Prompt: {a.prompt_label}. El análisis es heurístico y determinista, no un LLM.</p>
    </>
  );
}

export default function Requirements({ ctx }: { ctx: Ctx }) {
  const ini = ctx.initiative;
  const analyses = useLoad(() => (ini ? api.analyses(ini.id) : Promise.resolve([])), [ini?.id]);
  const [text, setText] = useState(ini?.description ?? "");
  const save = useAction();
  const analyze = useAction();
  useEffect(() => setText(ini?.description ?? ""), [ini?.id, ini?.description]);
  if (!ini) return <NeedInitiative ctx={ctx} />;

  const latest = analyses.data?.at(-1) ?? null;
  const dirty = text !== ini.description;
  const canEdit = can(ctx.role, "initiative:update");
  const canAnalyze = can(ctx.role, "ai:analyze");

  return (
    <>
      <Card title={`Requerimiento · ${ini.title}`}>
        <label className="block">Texto del requerimiento
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={6} readOnly={!canEdit} />
        </label>
        <ErrorNote error={save.error} />
        <div className="row">
          {canEdit && (
            <button disabled={!dirty || save.busy} onClick={async () => { if (await save.run(() => api.updateInitiative(ini.id, text))) ctx.refresh(); }}>
              Guardar cambios
            </button>
          )}
          {canAnalyze && (
            <button className="primary" disabled={dirty || analyze.busy} title={dirty ? "Guarda los cambios antes de analizar" : ""}
              onClick={async () => { if (await analyze.run(() => api.analyze(ini.id))) analyses.reload(); }}>
              {analyze.busy ? "Analizando…" : "Analizar calidad"}
            </button>
          )}
        </div>
        <ErrorNote error={analyze.error} />
        {dirty && <p className="note">Hay cambios sin guardar: un análisis anterior ya no es vigente para el texto nuevo.</p>}
      </Card>
      <Card title="Resultado del análisis">
        <ErrorNote error={analyses.error} />
        {latest ? <AnalysisResult a={latest} /> : <Empty>Aún no hay análisis para esta iniciativa.</Empty>}
      </Card>
    </>
  );
}
