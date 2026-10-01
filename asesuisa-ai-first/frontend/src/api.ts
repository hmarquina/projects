import type {
  AnalysisOut, ArtifactKind, ArtifactOut, AuditEvent, Initiative, Metrics, ReleaseOut, Role, RunOut,
} from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let token: string | null = null; // solo en memoria: recargar la página cierra la sesión
export const setToken = (t: string | null): void => {
  token = t;
};

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const data = (await res.json()) as { detail?: unknown };
      if (typeof data.detail === "string") detail = data.detail;
      else if (data.detail !== undefined) detail = "Datos inválidos";
    } catch {
      /* cuerpo no JSON */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string; role: Role }>("POST", "/auth/login", { username, password }),
  initiatives: () => request<Initiative[]>("GET", "/initiatives"),
  createInitiative: (title: string, description: string) => request<Initiative>("POST", "/initiatives", { title, description }),
  updateInitiative: (id: number, description: string) => request<Initiative>("PATCH", `/initiatives/${id}`, { description }),
  analyze: (id: number) => request<AnalysisOut>("POST", `/initiatives/${id}/analyze`),
  analyses: (id: number) => request<AnalysisOut[]>("GET", `/initiatives/${id}/analyses`),
  generate: (id: number, kind: ArtifactKind) => request<ArtifactOut>("POST", `/initiatives/${id}/artifacts/${kind}`),
  artifacts: (id: number) => request<ArtifactOut[]>("GET", `/initiatives/${id}/artifacts`),
  runPipeline: (id: number) => request<RunOut>("POST", `/initiatives/${id}/pipeline`),
  runsOf: (id: number) => request<RunOut[]>("GET", `/initiatives/${id}/pipeline-runs`),
  runs: (status?: string) => request<RunOut[]>("GET", `/pipeline-runs${status ? `?status=${status}` : ""}`),
  file: async (runId: number, path: string): Promise<string> => {
    const res = await fetch(`/pipeline-runs/${runId}/files/${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new ApiError(res.status, "Archivo no disponible");
    return res.text();
  },
  decide: (runId: number, decision: "approved" | "rejected", comment: string, risk_acknowledged: boolean) =>
    request<RunOut>("POST", `/pipeline-runs/${runId}/decision`, { decision, comment, risk_acknowledged }),
  createRelease: (runId: number) => request<ReleaseOut>("POST", `/pipeline-runs/${runId}/release`),
  releases: () => request<ReleaseOut[]>("GET", "/releases"),
  downloadRelease: async (id: number, version: string): Promise<void> => {
    const res = await fetch(`/releases/${id}/download`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new ApiError(res.status, "No se pudo descargar el paquete");
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = `release-${version}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  },
  audit: (limit = 100) => request<AuditEvent[]>("GET", `/audit?limit=${limit}`),
  verifyAudit: () => request<{ intact: boolean; first_tampered_id: number | null }>("GET", "/audit/verify"),
  metrics: () => request<Metrics>("GET", "/metrics/control-tower"),
};
