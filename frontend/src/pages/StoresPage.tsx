import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Store } from "../api";

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api<{ results?: Store[] } | Store[]>("/api/stores/");
      setStores(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load stores");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createStore() {
    setCreating(true);
    try {
      await api<Store>("/api/stores/", {
        method: "POST",
        body: JSON.stringify({
          name: "New Store Draft",
          code: `ST-${Date.now().toString(36).toUpperCase()}`,
          status: "draft",
        }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="page">
      <div className="toolbar">
        <div>
          <h1 className="page-title">Stores</h1>
          <p className="page-sub" style={{ marginBottom: 0 }}>
            Open a store-local layout and planogram. Catalogs stay org-global.
          </p>
        </div>
        <button className="btn" type="button" disabled={creating} onClick={createStore}>
          {creating ? "Creating…" : "New store"}
        </button>
      </div>

      {loading && <div className="loading">Loading stores…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && stores.length === 0 && (
        <div className="empty">No stores yet. Create one to begin.</div>
      )}
      <div className="grid-stores">
        {stores.map((s) => (
          <div key={s.id} className="store-tile" style={{ display: "block" }}>
            <Link to={`/editor?store=${s.id}`} style={{ color: "inherit", textDecoration: "none" }}>
              <span className="badge store">Store-local</span>
              <h3>{s.name}</h3>
              <p>
                {s.code || "—"} · {s.status}
                {s.cluster_tag ? ` · ${s.cluster_tag}` : ""}
              </p>
            </Link>
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <Link className="btn ghost" to={`/fixtures?store=${s.id}`}>
                Fixtures
              </Link>
              <Link className="btn" to={`/editor?store=${s.id}`}>
                Editor
              </Link>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
