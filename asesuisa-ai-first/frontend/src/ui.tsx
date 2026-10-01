import { useCallback, useEffect, useState, type ReactNode } from "react";
import { ApiError } from "./api";

export type Tone = "ok" | "bad" | "warn" | "info" | "muted";

const TONES: Record<string, Tone> = {
  passed: "ok", approved: "ok", verified: "ok", smoke: "ok", published: "ok", registered: "info",
  failed: "bad", blocked: "bad", rejected: "bad",
  skipped: "warn", manual: "warn", awaiting_approval: "warn", draft: "warn",
};
export const toneOf = (status: string): Tone => TONES[status] ?? "muted";

export const STATUS_LABEL: Record<string, string> = {
  passed: "pasó", failed: "falló", skipped: "no verificado", blocked: "bloqueado", awaiting_approval: "espera aprobación",
  approved: "aprobado", rejected: "rechazado", verified: "verificado", smoke: "smoke", manual: "manual", draft: "borrador",
  registered: "registrada",
};

export function Badge({ status, tone }: { status: string; tone?: Tone }) {
  return <span className={`badge ${tone ?? toneOf(status)}`}>{STATUS_LABEL[status] ?? status}</span>;
}

export function Card({ title, actions, children }: { title: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="card">
      <header className="card-head">
        <h2>{title}</h2>
        {actions && <div className="card-actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

export function Tile({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value">{value}</div>
      {hint && <div className="tile-hint">{hint}</div>}
    </div>
  );
}

export function Meter({ value, max = 100, marker, label }: { value: number; max?: number; marker?: number; label: string }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className="meter" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}>
      <div className="meter-fill" style={{ width: `${pct}%` }} />
      {marker !== undefined && <div className="meter-marker" style={{ left: `${(marker / max) * 100}%` }} title={`Umbral ${marker}`} />}
    </div>
  );
}

export const Empty = ({ children }: { children: ReactNode }) => <p className="empty">{children}</p>;

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const msg = error instanceof ApiError || error instanceof Error ? error.message : "Error inesperado";
  return <p className="error" role="alert">{msg}</p>;
}

export function useLoad<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps);
  const reload = useCallback(() => {
    setLoading(true);
    run().then((d) => { setData(d); setError(null); }).catch(setError).finally(() => setLoading(false));
  }, [run]);
  useEffect(reload, [reload]);
  return { data, error, loading, reload };
}

export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const run = useCallback(async <R,>(fn: () => Promise<R>): Promise<R | undefined> => {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e);
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);
  return { busy, error, run };
}

export const fmtDate = (iso: string): string => new Date(iso).toLocaleString("es-SV", { dateStyle: "short", timeStyle: "short" });

export function Spark({ values, label }: { values: number[]; label: string }) {
  if (values.length < 2) return <span className="muted">—</span>;
  const w = 80, h = 22, max = Math.max(...values, 1), min = Math.min(...values, 0);
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * h}`).join(" ");
  return (
    <svg width={w} height={h} role="img" aria-label={label} className="spark">
      <polyline points={pts} fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
