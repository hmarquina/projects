import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { api } from "../api";
import type { Ctx } from "../context";
import { runFixture } from "./fixtures";
import Audit from "../views/Audit";
import Development from "../views/Development";
import Initiatives from "../views/Initiatives";
import Security from "../views/Security";
import Testing from "../views/Testing";

vi.mock("../api", async (orig) => {
  const real = await orig<typeof import("../api")>();
  return { ...real, api: { ...real.api, runsOf: vi.fn(), audit: vi.fn() } };
});

const ini = { id: 1, title: "Reclamos", description: "x", status: "registered", created_by: "a", created_at: "2026-10-01T10:00:00Z" };
const ctx = (role: Ctx["role"], withInitiative = true): Ctx => ({
  role, username: `demo_${role}`, initiatives: [ini], initiative: withInitiative ? ini : null, select: vi.fn(), refresh: vi.fn(), go: vi.fn(),
});

beforeEach(() => {
  vi.mocked(api.runsOf).mockResolvedValue([runFixture()]);
  vi.mocked(api.audit).mockResolvedValue([]);
});

describe("acciones según el rol (el backend sigue decidiendo)", () => {
  it("un viewer no ve el formulario de registro", () => {
    render(<Initiatives ctx={ctx("viewer")} />);
    expect(screen.getByText(/no puede registrar iniciativas/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Registrar y analizar/ })).not.toBeInTheDocument();
  });

  it("un analyst puede registrar", () => {
    render(<Initiatives ctx={ctx("analyst")} />);
    expect(screen.getByRole("button", { name: /Registrar y analizar/ })).toBeInTheDocument();
  });

  it("solo el tech_lead ejecuta el pipeline", async () => {
    const { unmount } = render(<Development ctx={ctx("tech_lead")} />);
    expect(await screen.findByRole("button", { name: "Ejecutar pipeline" })).toBeInTheDocument();
    unmount();
    render(<Development ctx={ctx("approver")} />);
    expect(await screen.findByText(/no ejecuta el pipeline/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ejecutar pipeline" })).not.toBeInTheDocument();
  });

  it("un analyst no consulta la auditoría; un security sí", async () => {
    const { unmount } = render(<Audit ctx={ctx("analyst")} />);
    expect(screen.getByText(/no consulta la bitácora/)).toBeInTheDocument();
    unmount();
    render(<Audit ctx={ctx("security")} />);
    expect(await screen.findByRole("button", { name: "Verificar integridad" })).toBeInTheDocument();
  });

  it("sin iniciativa seleccionada las vistas piden seleccionar una", () => {
    render(<Testing ctx={ctx("viewer", false)} />);
    expect(screen.getByText("Selecciona una iniciativa")).toBeInTheDocument();
  });

  it("'no verificado' no se presenta como 'pasó' en Security", async () => {
    render(<Security ctx={ctx("security")} />);
    const row = (await screen.findByText("Dependencias")).closest("tr") as HTMLElement;
    expect(row).toHaveTextContent("no verificado");
    expect(row).not.toHaveTextContent("pasó");
    expect(screen.getByText(/«No verificado» nunca cuenta como «pasó»/)).toBeInTheDocument();
  });

  it("Testing lista lo que quedó sin verificar", async () => {
    render(<Testing ctx={ctx("viewer")} />);
    expect(await screen.findByText(/AC-SR-2: requiere verificación manual/)).toBeInTheDocument();
  });
});
