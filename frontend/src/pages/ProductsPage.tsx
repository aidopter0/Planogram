import { useEffect, useRef, useState } from "react";
import { api, type Product } from "../api";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const zipRef = useRef<HTMLInputElement>(null);

  async function load(query = q) {
    setLoading(true);
    setError(null);
    try {
      const path = query ? `/api/products/?q=${encodeURIComponent(query)}` : "/api/products/";
      const data = await api<{ results?: Product[] } | Product[]>(path);
      setProducts(Array.isArray(data) ? data : data.results || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load products");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onImport(e: React.FormEvent) {
    e.preventDefault();
    const csv = fileRef.current?.files?.[0];
    if (!csv) {
      setImportMsg("Choose a CSV file first.");
      return;
    }
    const fd = new FormData();
    fd.append("file", csv);
    const zip = zipRef.current?.files?.[0];
    if (zip) fd.append("images", zip);
    setImportMsg("Importing…");
    try {
      const res = await api<{
        created_count: number;
        updated_count: number;
        error_count: number;
        state: string;
      }>("/api/products/import/", { method: "POST", body: fd });
      setImportMsg(
        `Import ${res.state}: +${res.created_count} updated ${res.updated_count}, errors ${res.error_count}`,
      );
      await load();
    } catch (err) {
      setImportMsg(err instanceof Error ? err.message : "Import failed");
    }
  }

  return (
    <main className="page">
      <div className="toolbar">
        <div>
          <h1 className="page-title">Product Master</h1>
          <p className="page-sub" style={{ marginBottom: 0 }}>
            <span className="badge org">Org library</span> Shared SKUs across all stores.
            Width drives packing; H/D for visualization.
          </p>
        </div>
      </div>

      <form className="toolbar" onSubmit={onImport}>
        <input
          type="search"
          placeholder="Search SKU or name…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), load())}
        />
        <button className="btn ghost" type="button" onClick={() => load()}>
          Search
        </button>
        <input ref={fileRef} type="file" accept=".csv,text/csv" />
        <input ref={zipRef} type="file" accept=".zip,application/zip" />
        <button className="btn" type="submit">
          Import CSV (+ ZIP)
        </button>
      </form>
      {importMsg && <p className="page-sub">{importMsg}</p>}

      {loading && <div className="loading">Loading products…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !error && (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Front</th>
                <th>SKU</th>
                <th>Name</th>
                <th>Brand</th>
                <th>W×H×D mm</th>
                <th>Eff. W</th>
                <th>Readiness</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 && (
                <tr>
                  <td colSpan={7} className="empty">
                    No products. Import a CSV or run seed_demo.
                  </td>
                </tr>
              )}
              {products.map((p) => (
                <tr key={p.id}>
                  <td>
                    {p.front_image_url ? (
                      <img className="thumb" src={p.front_image_url} alt={p.name} />
                    ) : (
                      <div className="thumb" />
                    )}
                  </td>
                  <td className="mono">{p.sku}</td>
                  <td>{p.name}</td>
                  <td>{p.brand || "—"}</td>
                  <td className="mono">
                    {p.width_mm}×{p.height_mm}×{p.depth_mm}
                  </td>
                  <td className="mono">{p.effective_width_mm}</td>
                  <td>
                    <span className="badge">{p.readiness.replace("_", " ")}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
