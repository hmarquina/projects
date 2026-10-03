import type { RunOut } from "../types";
import { Card } from "../ui";

const LABEL: Record<string, string> = {
  calidad_requerimiento: "Calidad del requerimiento",
  pruebas: "Pruebas automáticas",
  sast: "SAST (bandit)",
  secretos: "Escaneo de secretos",
  dependencias: "Auditoría de dependencias",
  trazabilidad: "Trazabilidad (criterios con prueba automática)",
  documentacion: "Documentación",
  evidencia_completa: "Evidencia completa",
};

// Respaldo para ejecuciones guardadas antes de que la API devolviera los máximos.
const FALLBACK_MAX: Record<string, number> = {
  calidad_requerimiento: 20, pruebas: 25, sast: 10, secretos: 7, dependencias: 8, trazabilidad: 15, documentacion: 5, evidencia_completa: 10,
};

const CAUSE: Record<string, (run: RunOut) => string> = {
  dependencias: (run) => run.evidence.security.dependencies.status === "skipped"
    ? "La auditoría no se ejecutó (PIPELINE_DEPENDENCY_AUDIT=false o sin red): no verificado no suma."
    : "La auditoría reportó vulnerabilidades o dependencias fuera de la lista permitida.",
  trazabilidad: (run) => {
    const auto = run.traceability.filter((r) => r.status === "verified" || r.status === "smoke").length;
    return `${auto} de ${run.traceability.length} criterios tienen una prueba automática que pasa; el resto exige verificación manual.`;
  },
  pruebas: (run) => `${run.evidence.tests.passed} de ${run.evidence.tests.total} pruebas pasaron.`,
  calidad_requerimiento: () => "El análisis de calidad del requerimiento no alcanzó el máximo: revisa las ambigüedades.",
  sast: () => "Bandit no pasó o no se ejecutó.",
  secretos: () => "Se detectaron secretos literales o no se leyó el secreto desde el entorno.",
  documentacion: () => "Al README generado le faltan secciones obligatorias.",
  evidencia_completa: () => "Faltan artefactos, metadatos de modelo/prompt o la cadena de auditoría no es íntegra.",
};

export function BlockBreakdown({ run }: { run: RunOut }) {
  const { score, threshold, components } = run.readiness;
  const max: Record<string, number> = run.readiness.maximums ?? FALLBACK_MAX;
  const rows = Object.keys(max)
    .map((k) => ({ key: k, got: components[k] ?? 0, max: max[k] ?? 0, lost: (max[k] ?? 0) - (components[k] ?? 0) }))
    .filter((r) => r.lost > 0.05)
    .sort((a, b) => b.lost - a.lost);
  const hard = run.steps.filter((s) => s.blocking && s.status === "failed");
  const testsNotPassed = run.steps.some((s) => s.name === "pruebas" && s.status !== "passed");
  const blocked = run.status === "blocked";
  const gap = threshold - score;
  if (!blocked && rows.length === 0) return null;

  return (
    <Card title={blocked ? "Por qué está bloqueada" : "Dónde se pierden puntos"}>
      {blocked && (
        <ul className="note">
          {hard.map((s) => <li key={s.name}>Paso bloqueante fallido: <b className="mono">{s.name}</b> — {s.detail}</li>)}
          {testsNotPassed && !hard.some((s) => s.name === "pruebas") && <li>El paso <b className="mono">pruebas</b> no pasó.</li>}
          {gap > 0 && <li>Readiness {score} por debajo del umbral {threshold}: faltan {gap} puntos.</li>}
          <li>Un bloqueo es definitivo: esta ejecución no admite aprobación ni release. Corrige la causa y ejecuta de nuevo.</li>
        </ul>
      )}
      {rows.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>Componente</th><th>Puntos</th><th>Se pierden</th><th>Causa</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key}>
                  <td>{LABEL[r.key] ?? r.key}</td>
                  <td>{r.got.toFixed(1)} / {r.max}</td>
                  <td>−{r.lost.toFixed(1)}</td>
                  <td>{CAUSE[r.key]?.(run) ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
