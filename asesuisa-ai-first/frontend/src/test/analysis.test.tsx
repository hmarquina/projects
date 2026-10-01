import { render, screen } from "@testing-library/react";
import { AnalysisResult } from "../views/Requirements";
import { analysisFixture } from "./fixtures";

describe("resultado del análisis", () => {
  it("bloquea y explica cuando no cumple la Definition of Ready", () => {
    render(<AnalysisResult a={analysisFixture()} />);
    expect(screen.getByLabelText("Score de calidad")).toHaveTextContent("31");
    expect(screen.getByText(/No cumple la Definition of Ready/)).toBeInTheDocument();
    expect(screen.getByRole("meter", { name: "Calidad del requerimiento" })).toHaveAttribute("aria-valuenow", "31");
  });

  it("muestra cada ambigüedad con su cita y su pregunta de aclaración", () => {
    render(<AnalysisResult a={analysisFixture()} />);
    expect(screen.getByText("«rápido»")).toBeInTheDocument();
    expect(screen.getByText(/Cita: El sistema debe ser rápido\./)).toBeInTheDocument();
    expect(screen.getByText("¿Cuál es el tiempo máximo?")).toBeInTheDocument();
  });

  it("indica que está listo cuando alcanza el umbral", () => {
    render(<AnalysisResult a={analysisFixture({ score: 100, ready: true, ambiguities: [], missing: [] })} />);
    expect(screen.getByText(/Cumple la Definition of Ready/)).toBeInTheDocument();
    expect(screen.getByText("Sin ambigüedades detectadas.")).toBeInTheDocument();
  });

  it("alerta de prompt injection y de PII redactada sin alterar el resultado", () => {
    render(<AnalysisResult a={analysisFixture({}, { injection_flags: 2, pii_redactions: { email: 1 } })} />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("2 señal(es) de prompt injection");
    expect(alert).toHaveTextContent("email×1");
    expect(screen.getByLabelText("Score de calidad")).toHaveTextContent("31");
  });

  it("aclara que el análisis no es un LLM", () => {
    render(<AnalysisResult a={analysisFixture()} />);
    expect(screen.getByText(/no un LLM/)).toBeInTheDocument();
  });
});
