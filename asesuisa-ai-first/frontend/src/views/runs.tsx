import { useState } from "react";
import { api } from "../api";
import type { Ctx } from "../context";
import type { RunOut } from "../types";
import { Badge, fmtDate, useLoad } from "../ui";

export function useInitiativeRuns(ctx: Ctx) {
  const id = ctx.initiative?.id;
  const q = useLoad(() => (id ? api.runsOf(id) : Promise.resolve([] as RunOut[])), [id]);
  const [picked, setPicked] = useState<number | null>(null);
  const runs = q.data ?? [];
  const run = runs.find((r) => r.id === picked) ?? runs.at(-1) ?? null;
  return { runs, run, setPicked, reload: q.reload, loading: q.loading, error: q.error };
}

export function RunPicker({ runs, run, onPick }: { runs: RunOut[]; run: RunOut | null; onPick: (id: number) => void }) {
  if (runs.length === 0) return null;
  return (
    <label className="inline-label">Ejecución
      <select value={run?.id ?? ""} onChange={(e) => onPick(Number(e.target.value))}>
        {runs.map((r) => <option key={r.id} value={r.id}>#{r.id} · {fmtDate(r.created_at)} · {r.status}</option>)}
      </select>
    </label>
  );
}

export const RunBadge = ({ status }: { status: string }) => <Badge status={status} />;
