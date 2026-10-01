import type { Initiative, Role } from "./types";

export type ViewKey =
  | "dashboard" | "initiatives" | "requirements" | "analysis" | "architecture" | "development"
  | "testing" | "security" | "approvals" | "releases" | "metrics" | "audit";

export interface Ctx {
  role: Role;
  username: string;
  initiatives: Initiative[];
  initiative: Initiative | null;
  select: (id: number | null) => void;
  refresh: () => void;
  go: (view: ViewKey) => void;
}

export const VIEWS: { key: ViewKey; label: string; hint: string }[] = [
  { key: "dashboard", label: "Dashboard", hint: "Resumen y acciones" },
  { key: "initiatives", label: "Initiatives", hint: "Registro de iniciativas" },
  { key: "requirements", label: "Requirements", hint: "Texto y calidad" },
  { key: "analysis", label: "AI Analysis", hint: "Análisis y artefactos" },
  { key: "architecture", label: "Architecture", hint: "Arquitectura y contrato" },
  { key: "development", label: "Development", hint: "Pipeline y código" },
  { key: "testing", label: "Testing", hint: "Pruebas y trazabilidad" },
  { key: "security", label: "Security", hint: "Controles de seguridad" },
  { key: "approvals", label: "Approvals", hint: "Decisión humana" },
  { key: "releases", label: "Releases", hint: "Paquetes publicados" },
  { key: "metrics", label: "Metrics", hint: "Modelo y métricas" },
  { key: "audit", label: "Audit", hint: "Registro verificable" },
];
