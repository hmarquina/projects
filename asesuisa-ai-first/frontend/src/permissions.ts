import type { Role } from "./types";

// Espejo de backend/app/security.py. El backend es quien decide; esto solo oculta acciones que fallarían.
// `scripts/check_ui_permissions.py` verifica que no se desvíe.
export const PERMISSIONS: Record<Role, readonly string[]> = {
  viewer: ["initiative:read"],
  analyst: ["initiative:read", "initiative:create", "initiative:update", "ai:analyze", "ai:generate"],
  tech_lead: ["initiative:read", "ai:analyze", "ai:generate", "pipeline:run", "release:create"],
  security: ["initiative:read", "security:review", "audit:read"],
  approver: ["initiative:read", "release:approve", "audit:read"],
  admin: ["initiative:read", "audit:read", "user:manage"],
};

export const can = (role: Role | undefined, permission: string): boolean =>
  role !== undefined && PERMISSIONS[role].includes(permission);
