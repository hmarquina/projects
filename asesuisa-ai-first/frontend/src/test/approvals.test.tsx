import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { api, ApiError } from "../api";
import { DecisionForm } from "../views/Approvals";
import { runFixture } from "./fixtures";

vi.mock("../api", async (orig) => {
  const real = await orig<typeof import("../api")>();
  return { ...real, api: { ...real.api, decide: vi.fn() } };
});

const type = async (text: string) => userEvent.type(screen.getByLabelText(/Comentario de la decisión/), text);

describe("formulario de decisión", () => {
  beforeEach(() => {
    vi.mocked(api.decide).mockReset();
  });

  it("no permite aprobar sin comentario ni sin reconocer los riesgos", async () => {
    render(<DecisionForm run={runFixture()} onDone={vi.fn()} />);
    const approve = screen.getByRole("button", { name: "Aprobar" });
    expect(approve).toBeDisabled();
    await type("Revisado el reporte");
    expect(approve).toBeDisabled(); // falta reconocer riesgos
    await userEvent.click(screen.getByLabelText(/Reconozco los riesgos residuales/));
    expect(approve).toBeEnabled();
  });

  it("exige un comentario mínimo incluso para rechazar", async () => {
    render(<DecisionForm run={runFixture()} onDone={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Rechazar" })).toBeDisabled();
    await type("ok");
    expect(screen.getByRole("button", { name: "Rechazar" })).toBeDisabled();
    await type("ficiente");
    expect(screen.getByRole("button", { name: "Rechazar" })).toBeEnabled();
  });

  it("envía la decisión con el reconocimiento de riesgos", async () => {
    vi.mocked(api.decide).mockResolvedValue(runFixture({ status: "approved" }));
    const onDone = vi.fn();
    render(<DecisionForm run={runFixture()} onDone={onDone} />);
    await type("Revisado el reporte");
    await userEvent.click(screen.getByLabelText(/Reconozco los riesgos residuales/));
    await userEvent.click(screen.getByRole("button", { name: "Aprobar" }));
    expect(api.decide).toHaveBeenCalledWith(7, "approved", "Revisado el reporte", true);
    expect(onDone).toHaveBeenCalled();
  });

  it("muestra el rechazo por segregación de funciones y no da la acción por hecha", async () => {
    vi.mocked(api.decide).mockRejectedValue(new ApiError(403, "Segregación de funciones: no puede decidir quien creó este trabajo"));
    const onDone = vi.fn();
    render(<DecisionForm run={runFixture()} onDone={onDone} />);
    await type("Revisado el reporte");
    await userEvent.click(screen.getByLabelText(/Reconozco los riesgos residuales/));
    await userEvent.click(screen.getByRole("button", { name: "Aprobar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Segregación de funciones");
    expect(onDone).not.toHaveBeenCalled();
  });
});
