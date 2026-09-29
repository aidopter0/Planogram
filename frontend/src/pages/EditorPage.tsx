import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  api,
  type FixtureInstance,
  type Placement,
  type Planogram,
  type Product,
  type SceneGraph,
  type WidthSummary,
} from "../api";
import ElevationCanvas from "../components/ElevationCanvas";

function summarizeLocal(
  available: number,
  placements: Placement[],
): WidthSummary {
  const used = placements.reduce((s, p) => s + (p.width_consumed_mm || 0), 0);
  return {
    available_width_mm: available,
    used_width_mm: used,
    remaining_width_mm: available - used,
    overflow: available - used < 0,
    placements,
  };
}

export default function EditorPage() {
  const [params] = useSearchParams();
  const storeId = params.get("store");

  const [fixtures, setFixtures] = useState<FixtureInstance[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [graph, setGraph] = useState<SceneGraph>({
    schema_version: 5,
    units: "mm",
    blocks: [],
    placements: [],
  });
  const [carrierId, setCarrierId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const productsById = useMemo(() => {
    const m: Record<number, Product> = {};
    products.forEach((p) => {
      m[p.id] = p;
    });
    return m;
  }, [products]);

  const carriers = useMemo(() => {
    return fixtures.flatMap((f) =>
      f.components.map((c) => ({
        ...c,
        fixtureName: f.name,
        fixtureId: f.id,
      })),
    );
  }, [fixtures]);

  const activeCarrier = carriers.find((c) => c.id === carrierId) || carriers[0];

  const carrierPlacements = useMemo(() => {
    if (!activeCarrier) return [];
    return (graph.placements || []).filter(
      (p) => p.carrier_ref?.component_instance_id === activeCarrier.id,
    );
  }, [graph, activeCarrier]);

  const widthSummary = useMemo(() => {
    if (!activeCarrier) {
      return summarizeLocal(0, []);
    }
    return summarizeLocal(activeCarrier.available_width_mm, carrierPlacements);
  }, [activeCarrier, carrierPlacements]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const storesData = await api<{ results?: { id: number }[] } | { id: number }[]>(
          "/api/stores/",
        );
        const stores = Array.isArray(storesData) ? storesData : storesData.results || [];
        const sid = storeId ? Number(storeId) : stores[0]?.id;
        if (!sid) {
          setError("No store available. Create one first.");
          setLoading(false);
          return;
        }

        const [fixData, prodData, pogData] = await Promise.all([
          api<{ results?: FixtureInstance[] } | FixtureInstance[]>(
            `/api/fixtures/?store=${sid}`,
          ),
          api<{ results?: Product[] } | Product[]>("/api/products/"),
          api<{ results?: Planogram[] } | Planogram[]>(`/api/planograms/?store=${sid}`),
        ]);
        const fx = Array.isArray(fixData) ? fixData : fixData.results || [];
        const prods = Array.isArray(prodData) ? prodData : prodData.results || [];
        let pogs = Array.isArray(pogData) ? pogData : pogData.results || [];

        if (pogs.length === 0 && fx[0]) {
          const created = await api<Planogram>("/api/planograms/", {
            method: "POST",
            body: JSON.stringify({
              store: sid,
              name: `${fx[0].name} planogram`,
              target_fixture_ids: [fx[0].id],
              status: "draft",
            }),
          });
          pogs = [created];
        }

        setFixtures(fx);
        setProducts(prods);
        const pog = pogs[0] || null;
        setPlanogram(pog);
        let loadedGraph: SceneGraph = {
          schema_version: 5,
          units: "mm",
          blocks: [],
          placements: [],
        };
        if (pog?.scene?.graph) {
          loadedGraph = pog.scene.graph;
        } else if (pog) {
          const scene = await api<{ graph: SceneGraph }>(
            `/api/planograms/${pog.id}/scene/`,
          );
          loadedGraph = scene.graph;
        }
        setGraph(loadedGraph);

        // Prefer the carrier that already has placements (seeded shelf),
        // otherwise first component on the target fixture.
        const counts = new Map<number, number>();
        for (const p of loadedGraph.placements || []) {
          const cid = p.carrier_ref?.component_instance_id;
          if (cid != null) counts.set(cid, (counts.get(cid) || 0) + 1);
        }
        let preferred: number | null = null;
        let best = 0;
        counts.forEach((n, cid) => {
          if (n > best) {
            best = n;
            preferred = cid;
          }
        });
        const fallback =
          fx.find((f) => (pog?.target_fixture_ids || []).includes(f.id))
            ?.components?.[0]?.id ??
          fx[0]?.components?.[0]?.id ??
          null;
        setCarrierId(preferred ?? fallback);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load editor");
      } finally {
        setLoading(false);
      }
    })();
  }, [storeId]);

  async function placeProduct(product: Product, facings = 1) {
    if (!activeCarrier || !planogram) return;
    const eff =
      product.orientation === "rotated_90"
        ? product.height_mm || product.width_mm
        : product.width_mm;
    const consumed = eff * facings;
    if (widthSummary.used_width_mm + consumed > activeCarrier.available_width_mm) {
      setStatus(
        `Width overflow: need ${consumed} mm, remaining ${widthSummary.remaining_width_mm} mm`,
      );
      return;
    }
    const placement: Placement = {
      id: crypto.randomUUID(),
      product_id: product.id,
      sku: product.sku,
      carrier_ref: {
        fixture_instance_id: activeCarrier.fixtureId,
        component_instance_id: activeCarrier.id,
        kind: "shelf",
        face: activeCarrier.face,
        index: activeCarrier.shelf_index,
      },
      facings,
      sequence: carrierPlacements.length,
      orientation: product.orientation,
      effective_width_mm: eff,
      width_consumed_mm: consumed,
    };
    const next: SceneGraph = {
      ...graph,
      placements: [...graph.placements, placement],
    };
    setGraph(next);
    setStatus(`Placed ${product.sku} × ${facings}`);
  }

  async function saveScene() {
    if (!planogram) return;
    setStatus("Saving…");
    try {
      const res = await api<{
        graph: SceneGraph;
        updated_at: string;
        validation: { ok: boolean; issues: unknown[] };
      }>(`/api/planograms/${planogram.id}/scene/`, {
        method: "PUT",
        body: JSON.stringify({
          graph,
          schema_version: 5,
          updated_at: planogram.scene?.updated_at,
        }),
      });
      setGraph(res.graph);
      setPlanogram((prev) =>
        prev
          ? {
              ...prev,
              scene: {
                schema_version: 5,
                graph: res.graph,
                updated_at: res.updated_at,
              },
            }
          : prev,
      );
      setStatus(
        res.validation.ok
          ? "Saved — width-fit OK"
          : `Saved with ${res.validation.issues.length} validation issue(s)`,
      );
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save failed");
    }
  }

  if (loading) return <div className="loading">Loading editor…</div>;
  if (error) return <div className="error">{error}</div>;

  const usedPct = Math.min(
    100,
    activeCarrier
      ? (widthSummary.used_width_mm / Math.max(1, widthSummary.available_width_mm)) * 100
      : 0,
  );

  return (
    <div className="page wide">
      <div className="editor">
        <div className="editor-top">
          <strong>{planogram?.name || "Planogram editor"}</strong>
          <span className="badge store">Store-local</span>
          <span className="page-sub" style={{ margin: 0 }}>
            Elevation · width-fit (not optimization)
          </span>
          <div style={{ flex: 1 }} />
          {status && (
            <span className="mono" style={{ fontSize: "0.8rem", color: "var(--emerald-700)" }}>
              {status}
            </span>
          )}
          <button className="btn ghost" type="button" onClick={saveScene}>
            Save
          </button>
        </div>

        <aside className="editor-side">
          <p className="panel-title">Products</p>
          <p className="page-sub" style={{ marginTop: 0 }}>
            Click <strong>+1</strong> to place one facing on the selected shelf
            (width-fit). No drag required.
          </p>
          {products.map((p) => (
            <div key={p.id} className="product-row">
              {p.front_image_url ? (
                <img src={p.front_image_url} alt="" />
              ) : (
                <div className="thumb" />
              )}
              <div>
                <div className="mono">{p.sku}</div>
                <div style={{ fontSize: "0.8rem" }}>{p.name}</div>
                <div className="mono" style={{ color: "var(--text-muted)" }}>
                  {p.effective_width_mm} mm
                </div>
              </div>
              <button
                className="btn"
                type="button"
                style={{ marginLeft: "auto", padding: "4px 10px" }}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  placeProduct(p, 1);
                }}
              >
                +1
              </button>
            </div>
          ))}
        </aside>

        <div className="editor-canvas">
          {activeCarrier ? (
            <ElevationCanvas
              carrierWidthMm={activeCarrier.width_mm}
              availableWidthMm={activeCarrier.available_width_mm}
              placements={carrierPlacements}
              productsById={productsById}
            />
          ) : (
            <div className="empty">Place a fixture with shelves to edit.</div>
          )}
        </div>

        <aside className="editor-props">
          <p className="panel-title">Width meter</p>
          <div className="width-meter">
            <div className="track">
              <div
                className={`used ${widthSummary.overflow ? "overflow" : ""}`}
                style={{ width: `${Math.min(usedPct, 100)}%` }}
              />
            </div>
            <div className={`meta ${widthSummary.overflow ? "warn" : ""}`}>
              <span>
                used {widthSummary.used_width_mm} / {widthSummary.available_width_mm} mm
              </span>
              <span>
                {widthSummary.overflow
                  ? `overflow ${Math.abs(widthSummary.remaining_width_mm)} mm`
                  : `free ${widthSummary.remaining_width_mm} mm`}
              </span>
            </div>
          </div>

          <p className="panel-title" style={{ marginTop: 16 }}>
            Carriers
          </p>
          <div className="carrier-list">
            {carriers.map((c) => {
              const used = (graph.placements || [])
                .filter((p) => p.carrier_ref?.component_instance_id === c.id)
                .reduce((s, p) => s + (p.width_consumed_mm || 0), 0);
              return (
                <button
                  key={c.id}
                  type="button"
                  className={c.id === activeCarrier?.id ? "active" : ""}
                  onClick={() => setCarrierId(c.id)}
                >
                  <div>
                    {c.fixtureName} · Face {c.face} · Shelf {c.shelf_index + 1}
                  </div>
                  <div className="mono" style={{ color: "var(--text-muted)" }}>
                    used {used} / {c.available_width_mm} mm
                  </div>
                </button>
              );
            })}
          </div>

          <p className="panel-title" style={{ marginTop: 16 }}>
            Placements
          </p>
          {carrierPlacements.length === 0 && (
            <p className="page-sub">Click +1 on a product to place here.</p>
          )}
          {carrierPlacements.map((p) => (
            <div key={p.id} style={{ fontSize: "0.85rem", marginBottom: 6 }}>
              <span className="mono">{p.sku || p.product_id}</span> × {p.facings} ·{" "}
              {p.width_consumed_mm} mm
            </div>
          ))}
        </aside>
      </div>
    </div>
  );
}
