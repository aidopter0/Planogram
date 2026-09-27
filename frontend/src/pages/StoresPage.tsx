import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type Store } from "../api";
import { useEffect } from "react";

type CreateResult = {
  store: Store & { active_layout_id?: number };
  layout: { id: number; status: string; confidence_pct: number | null; source_filename: string };
  ingest: { state: string; error_message: string };
};

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [name, setName] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

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

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setMsg("Choose a DWG, DXF, RVT, or IFC file first.");
      return;
    }
    setUploading(true);
    setMsg("Uploading & extracting layout…");
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (name.trim()) fd.append("name", name.trim());
      const res = await api<CreateResult>("/api/stores/create-with-layout/", {
        method: "POST",
        body: fd,
      });
      if (res.ingest.state !== "ready") {
        setMsg(res.ingest.error_message || "Import failed");
        // Still open store if created
        if (res.store?.id) {
          setTimeout(() => navigate(`/stores/${res.store.id}`), 1200);
        }
        return;
      }
      setMsg(
        `Layout ready${res.layout.confidence_pct != null ? ` · ${res.layout.confidence_pct}% confidence` : ""}. Opening floor…`,
      );
      navigate(`/stores/${res.store.id}`);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="page">
      <div className="toolbar">
        <div>
          <h1 className="page-title">Stores</h1>
          <p className="page-sub" style={{ marginBottom: 0 }}>
            Open a floor canvas. New stores start with a CAD / BIM layout upload.
          </p>
        </div>
        <button className="btn" type="button" onClick={() => setShowNew(true)}>
          New store
        </button>
      </div>

      {showNew && (
        <form className="upload-card" onSubmit={onUpload}>
          <h2 className="page-title" style={{ fontSize: "1.25rem" }}>
            Import store layout
          </h2>
          <p className="page-sub">
            Drop DWG / DXF / RVT / IFC. We extract walls, doors, and columns where
            identifiable — then open the floor canvas.
          </p>
          <label className="page-sub">
            Store name (optional)
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Coastal Market"
              style={{ display: "block", width: "100%", marginTop: 6, padding: 10 }}
            />
          </label>
          <input
            ref={fileRef}
            type="file"
            accept=".dwg,.dxf,.rvt,.ifc,application/dxf,image/vnd.dxf"
            style={{ marginTop: 12 }}
          />
            <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
            <button className="btn" type="submit" disabled={uploading}>
              {uploading ? "Importing…" : "Upload & open floor"}
            </button>
            <button
              className="btn ghost"
              type="button"
              onClick={() => {
                setShowNew(false);
                setMsg(null);
              }}
            >
              Cancel
            </button>
            <a className="btn ghost" href="/static/samples/sample-store.dxf" download>
              Download sample DXF
            </a>
          </div>
          {msg && <p className="page-sub">{msg}</p>}
        </form>
      )}

      {loading && <div className="loading">Loading stores…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && stores.length === 0 && !showNew && (
        <div className="empty">No stores yet. Start with a CAD upload.</div>
      )}
      <div className="grid-stores">
        {stores.map((s) => (
          <Link key={s.id} to={`/stores/${s.id}`} className="store-tile">
            <span className="badge store">Floor canvas</span>
            <h3>{s.name}</h3>
            <p>
              {s.code || "—"} · {s.status}
              {s.cluster_tag ? ` · ${s.cluster_tag}` : ""}
            </p>
          </Link>
        ))}
      </div>
    </main>
  );
}
