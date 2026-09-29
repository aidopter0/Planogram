import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";

type Family = { family: string; label: string; count: number };

type FixtureType = {
  id: number;
  code: string;
  name: string;
  family: string;
  tier: number;
  default_params: Record<string, number>;
  placement_mode_options: string[];
};

type StoreAssetType = {
  id: number;
  code: string;
  name: string;
  family: string;
  placement_mode_options: string[];
  default_params: Record<string, number>;
  participates_in_planogram: boolean;
};

type Store = { id: number; name: string; code: string };

type FixtureInstance = {
  id: number;
  name: string;
  fixture_type_code: string;
  fixture_type_name: string;
  x_mm: number;
  y_mm: number;
  bay_width_mm: number;
};

type StoreAssetInstance = {
  id: number;
  name: string;
  asset_type_code: string;
  asset_type_name: string;
  asset_type_family: string;
  participates_in_planogram: boolean;
  x_mm: number;
  y_mm: number;
};

type Tab = "fixtures" | "store-assets";

function listify<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results || [];
}

export default function FixturesPage() {
  const [params] = useSearchParams();
  const [tab, setTab] = useState<Tab>("fixtures");
  const [stores, setStores] = useState<Store[]>([]);
  const [storeId, setStoreId] = useState<number | null>(
    params.get("store") ? Number(params.get("store")) : null,
  );
  const [families, setFamilies] = useState<Family[]>([]);
  const [family, setFamily] = useState<string>("");
  const [q, setQ] = useState("");
  const [types, setTypes] = useState<FixtureType[]>([]);
  const [assetTypes, setAssetTypes] = useState<StoreAssetType[]>([]);
  const [assetFamily, setAssetFamily] = useState("");
  const [assetFamilies, setAssetFamilies] = useState<Family[]>([]);
  const [pogFilter, setPogFilter] = useState<"all" | "yes" | "no">("all");
  const [instances, setInstances] = useState<FixtureInstance[]>([]);
  const [assets, setAssets] = useState<StoreAssetInstance[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const store = useMemo(
    () => stores.find((s) => s.id === storeId) || stores[0],
    [stores, storeId],
  );

  async function loadStores() {
    const data = await api<{ results?: Store[] } | Store[]>("/api/stores/");
    const list = listify(data);
    setStores(list);
    if (!storeId && list[0]) setStoreId(list[0].id);
  }

  async function loadFixtureCatalog() {
    const fams = await api<Family[]>("/api/catalog/fixture-types/families/");
    setFamilies(fams);
    const qs = new URLSearchParams();
    if (family) qs.set("family", family);
    if (q) qs.set("q", q);
    const data = await api<{ results?: FixtureType[] } | FixtureType[]>(
      `/api/catalog/fixture-types/?${qs}`,
    );
    setTypes(listify(data));
  }

  async function loadAssetCatalog() {
    const fams = await api<Family[]>("/api/catalog/store-asset-types/families/");
    setAssetFamilies(fams);
    const qs = new URLSearchParams();
    if (assetFamily) qs.set("family", assetFamily);
    if (pogFilter === "yes") qs.set("participates_in_planogram", "true");
    if (pogFilter === "no") qs.set("participates_in_planogram", "false");
    const data = await api<{ results?: StoreAssetType[] } | StoreAssetType[]>(
      `/api/catalog/store-asset-types/?${qs}`,
    );
    setAssetTypes(listify(data));
  }

  async function loadPlaced(sid: number) {
    const [fx, sa] = await Promise.all([
      api<{ results?: FixtureInstance[] } | FixtureInstance[]>(
        `/api/fixtures/?store=${sid}`,
      ),
      api<{ results?: StoreAssetInstance[] } | StoreAssetInstance[]>(
        `/api/store-assets/?store=${sid}`,
      ),
    ]);
    setInstances(listify(fx));
    setAssets(listify(sa));
  }

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await loadStores();
        await loadFixtureCatalog();
        await loadAssetCatalog();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load catalog");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    loadFixtureCatalog().catch(() => undefined);
  }, [family, q]);

  useEffect(() => {
    loadAssetCatalog().catch(() => undefined);
  }, [assetFamily, pogFilter]);

  useEffect(() => {
    if (store?.id) loadPlaced(store.id).catch(() => undefined);
  }, [store?.id]);

  async function placeFixture(ft: FixtureType) {
    if (!store) return;
    setStatus(`Placing ${ft.name}…`);
    try {
      const offset = instances.length * 200;
      await api("/api/fixtures/place/", {
        method: "POST",
        body: JSON.stringify({
          store_id: store.id,
          fixture_type_id: ft.id,
          x_mm: 2000 + offset,
          y_mm: 3000,
          name: ft.name,
        }),
      });
      await loadPlaced(store.id);
      setStatus(`Placed ${ft.name} on ${store.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Place failed");
    }
  }

  async function placeAsset(at: StoreAssetType) {
    if (!store) return;
    setStatus(`Placing ${at.name}…`);
    try {
      const offset = assets.length * 200;
      await api("/api/store-assets/place/", {
        method: "POST",
        body: JSON.stringify({
          store_id: store.id,
          asset_type_id: at.id,
          x_mm: 1000 + offset,
          y_mm: 5500,
          name: at.name,
        }),
      });
      await loadPlaced(store.id);
      setStatus(`Placed ${at.name} on ${store.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Place failed");
    }
  }

  if (loading) return <div className="loading">Loading fixture library…</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <main className="page">
      <div className="toolbar">
        <div>
          <h1 className="page-title">Fixtures & assets</h1>
          <p className="page-sub" style={{ marginBottom: 0 }}>
            <span className="badge org">Org library</span> Pick a type, place a{" "}
            <strong>store-local</strong> instance on the selected store layout.
          </p>
        </div>
        <label className="mono" style={{ fontSize: "0.85rem" }}>
          Store{" "}
          <select
            value={store?.id ?? ""}
            onChange={(e) => setStoreId(Number(e.target.value))}
            style={{ marginLeft: 8, padding: "8px 10px", borderRadius: 8 }}
          >
            {stores.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="tab-bar">
        <button
          type="button"
          className={tab === "fixtures" ? "active" : ""}
          onClick={() => setTab("fixtures")}
        >
          Fixture Types
        </button>
        <button
          type="button"
          className={tab === "store-assets" ? "active" : ""}
          onClick={() => setTab("store-assets")}
        >
          Store Asset Types
        </button>
      </div>

      {status && <p className="page-sub">{status}</p>}

      <div className="fixtures-layout">
        <section>
          {tab === "fixtures" ? (
            <>
              <div className="toolbar">
                <div className="chip-row">
                  <button
                    type="button"
                    className={`chip ${family === "" ? "active" : ""}`}
                    onClick={() => setFamily("")}
                  >
                    All ({families.reduce((s, f) => s + f.count, 0)})
                  </button>
                  {families.map((f) => (
                    <button
                      key={f.family}
                      type="button"
                      className={`chip ${family === f.family ? "active" : ""}`}
                      onClick={() => setFamily(f.family)}
                    >
                      {f.label} ({f.count})
                    </button>
                  ))}
                </div>
                <input
                  type="search"
                  placeholder="Search fixture types…"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                />
              </div>
              <div className="type-grid">
                {types.map((t) => (
                  <article key={t.id} className="type-card">
                    <div className="type-card-top">
                      <span className="badge org">{t.family}</span>
                      <span className="mono" style={{ fontSize: "0.7rem" }}>
                        T{t.tier}
                      </span>
                    </div>
                    <h3>{t.name}</h3>
                    <p className="mono">
                      {t.code} · {t.default_params?.bay_width_mm || "—"}×
                      {t.default_params?.depth_mm || "—"}×
                      {t.default_params?.height_mm || "—"} mm
                      {t.default_params?.shelf_count
                        ? ` · ${t.default_params.shelf_count} shelves`
                        : ""}
                    </p>
                    <button className="btn" type="button" onClick={() => placeFixture(t)}>
                      Place on store
                    </button>
                  </article>
                ))}
                {types.length === 0 && (
                  <div className="empty">No fixture types in this filter.</div>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="toolbar">
                <div className="chip-row">
                  <button
                    type="button"
                    className={`chip ${assetFamily === "" ? "active" : ""}`}
                    onClick={() => setAssetFamily("")}
                  >
                    All
                  </button>
                  {assetFamilies.map((f) => (
                    <button
                      key={f.family}
                      type="button"
                      className={`chip ${assetFamily === f.family ? "active" : ""}`}
                      onClick={() => setAssetFamily(f.family)}
                    >
                      {f.label} ({f.count})
                    </button>
                  ))}
                </div>
                <div className="chip-row">
                  <button
                    type="button"
                    className={`chip ${pogFilter === "all" ? "active" : ""}`}
                    onClick={() => setPogFilter("all")}
                  >
                    All roles
                  </button>
                  <button
                    type="button"
                    className={`chip ${pogFilter === "no" ? "active" : ""}`}
                    onClick={() => setPogFilter("no")}
                  >
                    Viz only
                  </button>
                  <button
                    type="button"
                    className={`chip ${pogFilter === "yes" ? "active" : ""}`}
                    onClick={() => setPogFilter("yes")}
                  >
                    Planogram capable
                  </button>
                </div>
              </div>
              <div className="type-grid">
                {assetTypes.map((t) => (
                  <article key={t.id} className="type-card">
                    <div className="type-card-top">
                      <span className="badge org">{t.family}</span>
                      {t.participates_in_planogram ? (
                        <span className="badge">Planogram</span>
                      ) : (
                        <span className="badge store">Viz only</span>
                      )}
                    </div>
                    <h3>{t.name}</h3>
                    <p className="mono">{t.code}</p>
                    <button className="btn" type="button" onClick={() => placeAsset(t)}>
                      Place on store
                    </button>
                  </article>
                ))}
                {assetTypes.length === 0 && (
                  <div className="empty">No store asset types in this filter.</div>
                )}
              </div>
            </>
          )}
        </section>

        <aside className="placed-panel">
          <p className="panel-title">Placed on {store?.name || "store"}</p>
          <span className="badge store">Store-local</span>
          <p className="panel-title" style={{ marginTop: 16 }}>
            Fixture instances ({instances.length})
          </p>
          <ul className="placed-list">
            {instances.map((i) => (
              <li key={i.id}>
                <strong>{i.name}</strong>
                <div className="mono">
                  {i.fixture_type_code} · ({i.x_mm}, {i.y_mm})
                </div>
              </li>
            ))}
            {instances.length === 0 && <li className="page-sub">None yet.</li>}
          </ul>
          <p className="panel-title" style={{ marginTop: 16 }}>
            Store assets ({assets.length})
          </p>
          <ul className="placed-list">
            {assets.map((a) => (
              <li key={a.id}>
                <strong>{a.name}</strong>{" "}
                {a.participates_in_planogram ? (
                  <span className="badge">Planogram</span>
                ) : (
                  <span className="badge store">Viz only</span>
                )}
                <div className="mono">
                  {a.asset_type_code} · ({a.x_mm}, {a.y_mm})
                </div>
              </li>
            ))}
            {assets.length === 0 && <li className="page-sub">None yet.</li>}
          </ul>
        </aside>
      </div>
    </main>
  );
}
