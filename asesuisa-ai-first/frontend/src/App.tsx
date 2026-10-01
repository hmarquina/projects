import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { api, setToken } from "./api";
import { VIEWS, type Ctx, type ViewKey } from "./context";
import type { Initiative, Role } from "./types";
import { ErrorNote, useAction } from "./ui";
import AiAnalysis from "./views/AiAnalysis";
import Approvals from "./views/Approvals";
import Architecture from "./views/Architecture";
import Audit from "./views/Audit";
import Dashboard from "./views/Dashboard";
import Development from "./views/Development";
import Initiatives from "./views/Initiatives";
import MetricsView from "./views/MetricsView";
import Releases from "./views/Releases";
import Requirements from "./views/Requirements";
import Security from "./views/Security";
import Testing from "./views/Testing";

interface Session { username: string; role: Role }

export function Login({ onLogin }: { onLogin: (s: Session) => void }) {
  const [username, setUsername] = useState("demo_analyst");
  const [password, setPassword] = useState("");
  const { busy, error, run } = useAction();
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const res = await run(() => api.login(username, password));
    if (res) { setToken(res.access_token); onLogin({ username, role: res.role }); }
  };
  return (
    <main className="login">
      <h1>AI Engineering Control Tower</h1>
      <p className="muted">Demo con datos sintéticos. La contraseña la define quien levanta la demo (<code>DEMO_PASSWORD</code>).</p>
      <form onSubmit={submit} className="form">
        <label>Usuario
          <select value={username} onChange={(e) => setUsername(e.target.value)}>
            {["analyst", "tech_lead", "approver", "security", "viewer", "admin"].map((r) => <option key={r} value={`demo_${r}`}>demo_{r}</option>)}
          </select>
        </label>
        <label>Contraseña
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
        </label>
        <ErrorNote error={error} />
        <button className="primary" disabled={busy}>{busy ? "Entrando…" : "Entrar"}</button>
      </form>
    </main>
  );
}

function Shell({ session, onLogout }: { session: Session; onLogout: () => void }) {
  const [view, setView] = useState<ViewKey>("dashboard");
  const [initiatives, setInitiatives] = useState<Initiative[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const refresh = useCallback(() => {
    api.initiatives().then((list) => {
      setInitiatives(list);
      setSelectedId((cur) => (cur !== null && list.some((i) => i.id === cur) ? cur : list.at(-1)?.id ?? null));
    }).catch(() => setInitiatives([]));
  }, []);
  useEffect(refresh, [refresh]);

  const ctx: Ctx = useMemo(() => ({
    role: session.role, username: session.username, initiatives,
    initiative: initiatives.find((i) => i.id === selectedId) ?? null,
    select: setSelectedId, refresh, go: setView,
  }), [session, initiatives, selectedId, refresh]);

  const body = {
    dashboard: <Dashboard ctx={ctx} />, initiatives: <Initiatives ctx={ctx} />, requirements: <Requirements ctx={ctx} />,
    analysis: <AiAnalysis ctx={ctx} />, architecture: <Architecture ctx={ctx} />, development: <Development ctx={ctx} />,
    testing: <Testing ctx={ctx} />, security: <Security ctx={ctx} />, approvals: <Approvals ctx={ctx} />,
    releases: <Releases ctx={ctx} />, metrics: <MetricsView />, audit: <Audit ctx={ctx} />,
  }[view];
  const current = VIEWS.find((v) => v.key === view);

  return (
    <div className="shell">
      <nav aria-label="Secciones" className="side">
        <div className="brand">Control Tower</div>
        <ul>
          {VIEWS.map((v) => (
            <li key={v.key}>
              <button className={v.key === view ? "nav active" : "nav"} aria-current={v.key === view ? "page" : undefined} onClick={() => setView(v.key)}>
                {v.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="main">
        <header className="top">
          <div>
            <h1>{current?.label}</h1>
            <span className="muted">{current?.hint}</span>
          </div>
          <div className="top-right">
            <label className="inline-label">Iniciativa
              <select aria-label="Iniciativa seleccionada" value={selectedId ?? ""} onChange={(e) => setSelectedId(e.target.value ? Number(e.target.value) : null)}>
                <option value="">— ninguna —</option>
                {initiatives.map((i) => <option key={i.id} value={i.id}>#{i.id} {i.title}</option>)}
              </select>
            </label>
            <span className="user">{session.username} · <strong>{session.role}</strong></span>
            <button onClick={onLogout}>Salir</button>
          </div>
        </header>
        <div className="content">{body}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const logout = () => { setToken(null); setSession(null); };
  return session ? <Shell session={session} onLogout={logout} /> : <Login onLogin={setSession} />;
}
