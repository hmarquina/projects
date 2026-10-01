import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { Login } from "../App";
import * as apiModule from "../api";

vi.mock("../api", async (orig) => {
  const real = await orig<typeof import("../api")>();
  return { ...real, api: { ...real.api, login: vi.fn() }, setToken: vi.fn() };
});

describe("Login", () => {
  it("muestra el error del servidor y no inicia sesión con credenciales inválidas", async () => {
    vi.mocked(apiModule.api.login).mockRejectedValue(new apiModule.ApiError(401, "Credenciales inválidas"));
    const onLogin = vi.fn();
    render(<Login onLogin={onLogin} />);
    await userEvent.type(screen.getByLabelText("Contraseña"), "mala");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Credenciales inválidas");
    expect(onLogin).not.toHaveBeenCalled();
    expect(apiModule.setToken).not.toHaveBeenCalled();
  });

  it("guarda el token en memoria y entrega el rol que devuelve el servidor", async () => {
    vi.mocked(apiModule.api.login).mockResolvedValue({ access_token: "tok", role: "analyst" });
    const onLogin = vi.fn();
    render(<Login onLogin={onLogin} />);
    await userEvent.type(screen.getByLabelText("Contraseña"), "buena");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    await waitFor(() => expect(onLogin).toHaveBeenCalledWith({ username: "demo_analyst", role: "analyst" }));
    expect(apiModule.setToken).toHaveBeenCalledWith("tok");
  });

  it("no persiste credenciales ni token en el almacenamiento del navegador", async () => {
    vi.mocked(apiModule.api.login).mockResolvedValue({ access_token: "tok", role: "analyst" });
    render(<Login onLogin={vi.fn()} />);
    await userEvent.type(screen.getByLabelText("Contraseña"), "buena");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));
    await waitFor(() => expect(apiModule.setToken).toHaveBeenCalled());
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
});
