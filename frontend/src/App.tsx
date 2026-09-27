import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { api, ensureCsrf, type User } from "./api";
import EditorPage from "./pages/EditorPage";
import ProductsPage from "./pages/ProductsPage";
import StoresPage from "./pages/StoresPage";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        await ensureCsrf();
        const me = await api<User>("/accounts/me/");
        setUser(me);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load session");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function logout() {
    await api("/accounts/logout/", { method: "POST", body: "{}" });
    window.location.href = "/login/";
  }

  if (loading) {
    return <div className="loading">Loading Planogram…</div>;
  }
  if (error || !user?.authenticated) {
    window.location.href = "/login/";
    return <div className="loading">Redirecting to sign in…</div>;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          Plano<span>gram</span>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Stores
          </NavLink>
          <NavLink to="/products">Product Master</NavLink>
          <NavLink to="/editor">Editor</NavLink>
        </nav>
        <div className="user-chip">
          <span className="badge">{user.role.replace("_", " ")}</span>
          <strong>{user.username}</strong>
          <button className="btn ghost" type="button" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<StoresPage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/editor" element={<EditorPage />} />
        <Route path="/editor/:planogramId" element={<EditorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
