import type { Metrics, OrgMetric } from "../types";
import { Card, Spark } from "../ui";

const fmt = (v: number): string => (Number.isInteger(v) ? String(v) : v.toFixed(1));

export function OrgTable({ metrics }: { metrics: OrgMetric[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Métrica</th><th>Baseline (caso)</th><th>Target base</th><th>Stretch</th>
            <th>Current</th><th>Trend</th><th>Confianza</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.key}>
              <td>{m.label} <span className="muted">({m.unit})</span></td>
              <td>{fmt(m.baseline)}</td>
              <td>{fmt(m.target_base)}</td>
              <td>{fmt(m.target_stretch)}</td>
              <td className="nodata" title={m.status}>{m.current === null ? "sin dato" : fmt(m.current)}</td>
              <td><Spark values={m.trend} label={`Tendencia de ${m.label}`} /></td>
              <td>{m.confidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const SCENARIO_LABEL: Record<string, string> = { conservative: "Conservador", base: "Base", stretch: "Stretch" };

export function ModelCard({ model }: { model: Metrics["model"] }) {
  const s = model.simulation;
  const pct = (x: number): string => `${Math.round(x * 100)}%`;
  return (
    <Card title="Modelo de capacidad (supuestos)">
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Escenario</th><th>Capacidad</th><th>Capacidad de valor</th><th>¿Cubre +50% de demanda?</th></tr>
          </thead>
          <tbody>
            {Object.entries(model.scenarios).map(([k, v]) => (
              <tr key={k}>
                <td>{SCENARIO_LABEL[k] ?? k}</td>
                <td>{v.capacity.toFixed(2)}×</td>
                <td>{v.value_capacity.toFixed(2)}×</td>
                <td>{v.capacity >= model.demand_growth ? "sí" : v.value_capacity >= model.demand_growth ? "solo en valor" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">
        <strong>2× de valor es el techo de los rangos supuestos, no un valor esperado.</strong> Simulación con adopción parcial:
        mediana {s.value_median.toFixed(2)}× (P10 {s.value_p10.toFixed(2)}× – P90 {s.value_p90.toFixed(2)}×);
        P(≥1.3×) {pct(s.p_value_ge_1_3)}, P(≥1.5×) {pct(s.p_value_ge_1_5)}, P(≥2.0×) {pct(s.p_value_ge_2_0)}.
        Con el caso Base, llegar a 2× exige diferir ≈ {pct(model.required_scope_removed_for_2x_base)} del alcance de bajo valor.
      </p>
    </Card>
  );
}
