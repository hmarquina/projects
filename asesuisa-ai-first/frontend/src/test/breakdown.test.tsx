import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BlockBreakdown } from "../views/BlockBreakdown";
import { runFixture } from "./fixtures";

const blockedRun = runFixture({
  status: "blocked",
  steps: [
    { name: "pruebas", status: "passed", blocking: true, detail: "13/13", duration_ms: 1 },
    { name: "dependencias", status: "skipped", blocking: true, detail: "auditoría deshabilitada", duration_ms: 0 },
  ],
  readiness: {
    score: 78, threshold: 85, unverified: [],
    components: { calidad_requerimiento: 20, pruebas: 25, sast: 10, secretos: 7, dependencias: 0, trazabilidad: 1.4, documentacion: 5, evidencia_completa: 10 },
  },
  traceability: [
    { ac_id: "A1", tests: ["t"], status: "verified", reason: "" },
    { ac_id: "A2", tests: ["t"], status: "smoke", reason: "" },
    ...Array.from({ length: 19 }, (_, i) => ({ ac_id: `M${i}`, tests: [], status: "manual", reason: "" })),
  ],
});

describe("desglose del bloqueo", () => {
  it("explica la brecha de puntos y ordena por lo que más se pierde", () => {
    render(<BlockBreakdown run={blockedRun} />);
    expect(screen.getByText(/faltan 7 puntos/)).toBeInTheDocument();
    expect(screen.getByText(/2 de 21 criterios/)).toBeInTheDocument();
    expect(screen.getByText(/no verificado no suma/)).toBeInTheDocument();
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("Trazabilidad");
    expect(rows[1]).toHaveTextContent("Auditoría de dependencias");
    expect(rows).toHaveLength(2);
  });

  it("nombra un paso bloqueante fallido", () => {
    const run = runFixture({ ...blockedRun, steps: [{ name: "politica_estatica", status: "failed", blocking: true, detail: "import prohibido", duration_ms: 1 }] });
    render(<BlockBreakdown run={run} />);
    expect(screen.getByText(/politica_estatica/)).toBeInTheDocument();
    expect(screen.getByText(/no admite aprobación ni release/)).toBeInTheDocument();
  });

  it("no muestra nada si no está bloqueada y no se pierden puntos", () => {
    const full = { calidad_requerimiento: 20, pruebas: 25, sast: 10, secretos: 7, dependencias: 8, trazabilidad: 15, documentacion: 5, evidencia_completa: 10 };
    const { container } = render(<BlockBreakdown run={runFixture({ readiness: { score: 100, threshold: 85, components: full, unverified: [] } })} />);
    expect(container).toBeEmptyDOMElement();
  });
});
