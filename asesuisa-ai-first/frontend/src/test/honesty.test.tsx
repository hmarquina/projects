import { render, screen, within } from "@testing-library/react";
import { vi } from "vitest";
import { api } from "../api";
import type { Ctx } from "../context";
import Dashboard from "../views/Dashboard";
import MetricsView from "../views/MetricsView";
import { metricsFixture, runFixture } from "./fixtures";

vi.mock("../api", async (orig) => {
  const real = await orig<typeof import("../api")>();
  return { ...real, api: { ...real.api, metrics: vi.fn(), runs: vi.fn() } };
});

const ctx = (role: Ctx["role"]): Ctx => ({
  role, username: `demo_${role}`, initiatives: [], initiative: null, select: vi.fn(), refresh: vi.fn(), go: vi.fn(),
});

beforeEach(() => {
  vi.mocked(api.metrics).mockResolvedValue(metricsFixture);
  vi.mocked(api.runs).mockResolvedValue([]);
});

describe("honestidad de los datos", () => {
  it("las métricas organizacionales muestran 'sin dato' y nunca un valor actual", async () => {
    render(<MetricsView />);
    const row = (await screen.findByText(/Lead time/)).closest("tr") as HTMLElement;
    expect(within(row).getByText("sin dato")).toBeInTheDocument();
    expect(within(row).getAllByRole("cell")[4]).toHaveTextContent("sin dato");
  });

  it("declara que el 2× es el techo de los rangos y no un valor esperado", async () => {
    render(<MetricsView />);
    expect(await screen.findByText(/techo de los rangos supuestos/)).toBeInTheDocument();
    expect(screen.getByText(/mediana 1\.42×/)).toBeInTheDocument();
    expect(screen.getByText(/P\(≥2\.0×\) 0%/)).toBeInTheDocument();
  });

  it("el caso Base no se presenta como suficiente por sí solo para el +50% de demanda", async () => {
    render(<MetricsView />);
    const base = (await screen.findByText("Base")).closest("tr") as HTMLElement;
    expect(within(base).getByText("solo en valor")).toBeInTheDocument();
  });

  it("el dashboard avisa que los datos son sintéticos y que el proveedor es un mock", async () => {
    render(<Dashboard ctx={ctx("viewer")} />);
    expect(await screen.findByText(/mock determinista/)).toBeInTheDocument();
    expect(screen.getByText(/Datos 100% sintéticos/)).toBeInTheDocument();
  });

  it("el approver ve su tarea pendiente; el analyst no", async () => {
    vi.mocked(api.runs).mockResolvedValue([runFixture()]);
    const { unmount } = render(<Dashboard ctx={ctx("approver")} />);
    expect(await screen.findByText(/esperan una decisión humana/)).toBeInTheDocument();
    unmount();
    const withInitiative = { ...ctx("analyst"), initiatives: [{ id: 1, title: "R", description: "x", status: "registered", created_by: "a", created_at: "2026-10-01T10:00:00Z" }] };
    render(<Dashboard ctx={withInitiative} />);
    expect(await screen.findByText(/Nada pendiente para tu rol/)).toBeInTheDocument();
  });
});
