import { api } from "../api";
import { Card, ErrorNote, Spark, useLoad } from "../ui";
import { ModelCard, OrgTable } from "./shared";

export default function MetricsView() {
  const m = useLoad(() => api.metrics(), []);
  if (!m.data) return <ErrorNote error={m.error} />;
  const p = m.data.platform;
  return (
    <>
      <ModelCard model={m.data.model} />
      <Card title="Métricas organizacionales">
        <OrgTable metrics={m.data.organizational} />
        <p className="note">{m.data.disclaimer}</p>
      </Card>
      <Card title="Series de la plataforma (uso del MVP)">
        <ul className="inline">
          <li>Calidad del requerimiento: <Spark values={p.requirement_quality_series} label="Serie de calidad del requerimiento" /></li>
          <li>Readiness de ejecuciones: <Spark values={p.readiness_series} label="Serie de readiness" /></li>
        </ul>
        <p className="note">Con pocos datos sintéticos las series no tienen significado estadístico: muestran el mecanismo, no un resultado.</p>
      </Card>
    </>
  );
}
