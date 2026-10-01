import { can, PERMISSIONS } from "../permissions";

describe("permisos de la UI", () => {
  it("separa quien ejecuta, quien aprueba y quien genera", () => {
    expect(can("tech_lead", "pipeline:run")).toBe(true);
    expect(can("tech_lead", "release:approve")).toBe(false);
    expect(can("approver", "release:approve")).toBe(true);
    expect(can("approver", "pipeline:run")).toBe(false);
    expect(can("approver", "initiative:create")).toBe(false);
    expect(can("analyst", "release:create")).toBe(false);
  });

  it("nadie tiene a la vez ejecutar/crear y aprobar", () => {
    for (const perms of Object.values(PERMISSIONS)) {
      const generates = perms.includes("pipeline:run") || perms.includes("initiative:create") || perms.includes("ai:generate");
      expect(generates && perms.includes("release:approve")).toBe(false);
    }
  });

  it("un rol desconocido no tiene permisos", () => {
    expect(can(undefined, "initiative:read")).toBe(false);
  });
});
