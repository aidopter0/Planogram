import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import ElevationCanvas from "../components/ElevationCanvas";

type Store = { id: number; name: string; code: string };
type Layout = {
  id: number;
  store: number;
  status: string;
  source_filename: string;
  confidence_pct: number | null;
  needs_review_counts: Record<string, number>;
  underlay: {
    type: string;
    features: Array<{
      properties?: { kind?: string; layer?: string };
      geometry: { type: string; coordinates: number[][] };
    }>;
  };
  extent_min_x: number | null;
  extent_min_y: number | null;
  extent_max_x: number | null;
  extent_max_y: number | null;
};

type FixtureType = {
  id: number;
  code: string;
  name: string;
  family: string;
  default_params: Record<string, number>;
};

type Family = { family: string; label: string; count: number };

type ComponentInstance = {
  id: number;
  fixture: number;
  shelf_index: number;
  face: string;
  width_mm: number;
  available_width_mm: number;
  reserved_insets_mm: number;
  height_mm: number;
};

type FixtureInstance = {
  id: number;
  name: string;
  fixture_type: number;
  fixture_type_code: string;
  fixture_type_name: string;
  fixture_type_family?: string;
  x_mm: number;
  y_mm: number;
  rotation_deg: number;
  bay_width_mm: number;
  params: Record<string, number>;
  components: ComponentInstance[];
};

type Product = {
  id: number;
  sku: string;
  name: string;
  width_mm: number;
  height_mm: number;
  orientation: string;
  effective_width_mm: number;
  front_image_url: string | null;
};

type Placement = {
  id: string;
  product_id: number;
  sku?: string;
  carrier_ref: {
    fixture_instance_id: number;
    component_instance_id: number;
    kind: string;
    face: string;
    index: number;
  };
  facings: number;
  sequence: number;
  orientation: string;
  effective_width_mm: number;
  width_consumed_mm: number;
};

type SceneGraph = {
  schema_version: number;
  units: string;
  blocks: unknown[];
  placements: Placement[];
};

type Planogram = {
  id: number;
  name: string;
  target_fixture_ids: number[];
  scene?: { graph: SceneGraph; updated_at: string };
};

const FAMILY_COLORS: Record<string, string> = {
  gondola: "#10b981",
  produce: "#84cc16",
  chilled: "#0ea5e9",
  frozen: "#38bdf8",
  bakery: "#f59e0b",
  deli: "#f43f5e",
  bulk: "#a78bfa",
  checkout: "#64748b",
};

function listify<T>(data: { results?: T[] } | T[]): T[] {
  return Array.isArray(data) ? data : data.results || [];
}

function footprint(fi: FixtureInstance) {
  const w = fi.bay_width_mm || fi.params?.bay_width_mm || 900;
  const d = fi.params?.depth_mm || 450;
  return { w, d };
}

export default function StoreFloorPage() {
  const { storeId } = useParams();
  const navigate = useNavigate();
  const sid = Number(storeId);

  const [store, setStore] = useState<Store | null>(null);
  const [layout, setLayout] = useState<Layout | null>(null);
  const [families, setFamilies] = useState<Family[]>([]);
  const [family, setFamily] = useState("");
  const [types, setTypes] = useState<FixtureType[]>([]);
  const [fixtures, setFixtures] = useState<FixtureInstance[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [planogram, setPlanogram] = useState<Planogram | null>(null);
  const [graph, setGraph] = useState<SceneGraph>({
    schema_version: 5,
    units: "mm",
    blocks: [],
    placements: [],
  });
  const [carrierId, setCarrierId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dragOver, setDragOver] = useState(false);

  const svgRef = useRef<SVGSVGElement>(null);
  const draggingPose = useRef<{ id: number; ox: number; oy: number } | null>(null);

  const selected = fixtures.find((f) => f.id === selectedId) || null;

  const extent = useMemo(() => {
    const pad = 800;
    const minX = (layout?.extent_min_x ?? 0) - pad;
    const minY = (layout?.extent_min_y ?? 0) - pad;
    const maxX = (layout?.extent_max_x ?? 24000) + pad;
    const maxY = (layout?.extent_max_y ?? 18000) + pad;
    return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY };
  }, [layout]);

  const productsById = useMemo(() => {
    const m: Record<number, Product> = {};
    products.forEach((p) => {
      m[p.id] = p;
    });
    return m;
  }, [products]);

  const activeCarrier =
    selected?.components.find((c) => c.id === carrierId) ||
    selected?.components[0] ||
    null;

  const carrierPlacements = useMemo(() => {
    if (!activeCarrier) return [];
    return (graph.placements || []).filter(
      (p) => p.carrier_ref?.component_instance_id === activeCarrier.id,
    );
  }, [graph, activeCarrier]);

  const usedWidth = carrierPlacements.reduce(
    (s, p) => s + (p.width_consumed_mm || 0),
    0,
  );
  const avail = activeCarrier?.available_width_mm || 0;
  const remaining = avail - usedWidth;

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [st, lay, fams, fixData, prodData] = await Promise.all([
        api<Store>(`/api/stores/${sid}/`),
        api<Layout>(`/api/stores/${sid}/layout/`),
        api<Family[]>("/api/catalog/fixture-types/families/"),
        api<{ results?: FixtureInstance[] } | FixtureInstance[]>(
          `/api/fixtures/?store=${sid}`,
        ),
        api<{ results?: Product[] } | Product[]>("/api/products/"),
      ]);
      setStore(st);
      setLayout(lay);
      setFamilies(fams);
      setFixtures(listify(fixData));
      setProducts(listify(prodData));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load store floor");
    } finally {
      setLoading(false);
    }
  }, [sid]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  useEffect(() => {
    (async () => {
      const qs = family ? `?family=${family}` : "";
      const data = await api<{ results?: FixtureType[] } | FixtureType[]>(
        `/api/catalog/fixture-types/${qs}`,
      );
      setTypes(listify(data));
    })().catch(() => undefined);
  }, [family]);

  useEffect(() => {
    if (!selected) {
      setPlanogram(null);
      return;
    }
    (async () => {
      const pogs = listify(
        await api<{ results?: Planogram[] } | Planogram[]>(
          `/api/planograms/?store=${sid}`,
        ),
      );
      let pog =
        pogs.find((p) => (p.target_fixture_ids || []).includes(selected.id)) ||
        null;
      if (!pog) {
        pog = await api<Planogram>("/api/planograms/", {
          method: "POST",
          body: JSON.stringify({
            store: sid,
            name: `${selected.name} planogram`,
            target_fixture_ids: [selected.id],
            status: "draft",
          }),
        });
      }
      setPlanogram(pog);
      const scene = await api<{ graph: SceneGraph; updated_at: string }>(
        `/api/planograms/${pog.id}/scene/`,
      );
      setGraph(scene.graph);
      setPlanogram({
        ...pog,
        scene: { graph: scene.graph, updated_at: scene.updated_at },
      });
      setCarrierId(selected.components[0]?.id ?? null);
    })().catch((e) =>
      setStatus(e instanceof Error ? e.message : "Planogram load failed"),
    );
  }, [selected?.id, sid]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setSelectedId(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function clientToWorld(clientX: number, clientY: number) {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const loc = pt.matrixTransform(ctm.inverse());
    // SVG y is flipped via transform; world y is already in model space
    return { x: loc.x, y: loc.y };
  }

  async function dropFixtureType(ft: FixtureType, clientX: number, clientY: number) {
    const { x, y } = clientToWorld(clientX, clientY);
    setStatus(`Placing ${ft.name}…`);
    try {
      const inst = await api<FixtureInstance>("/api/fixtures/place/", {
        method: "POST",
        body: JSON.stringify({
          store_id: sid,
          fixture_type_id: ft.id,
          x_mm: Math.round(x),
          y_mm: Math.round(y),
          name: ft.name,
        }),
      });
      setFixtures((prev) => [...prev, inst]);
      setSelectedId(inst.id);
      setStatus(`Placed ${ft.name}`);
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Place failed");
    }
  }

  async function savePose(id: number, x: number, y: number) {
    const updated = await api<FixtureInstance>(`/api/fixtures/${id}/pose/`, {
      method: "PATCH",
      body: JSON.stringify({ x_mm: Math.round(x), y_mm: Math.round(y) }),
    });
    setFixtures((prev) => prev.map((f) => (f.id === id ? { ...f, ...updated } : f)));
  }

  function placeProductOnCarrier(product: Product) {
    if (!activeCarrier || !selected || !planogram) return;
    const eff =
      product.orientation === "rotated_90"
        ? product.height_mm || product.width_mm
        : product.width_mm;
    if (usedWidth + eff > avail) {
      setStatus(`No width: need ${eff} mm, free ${remaining} mm`);
      return;
    }
    const placement: Placement = {
      id: crypto.randomUUID(),
      product_id: product.id,
      sku: product.sku,
      carrier_ref: {
        fixture_instance_id: selected.id,
        component_instance_id: activeCarrier.id,
        kind: "shelf",
        face: activeCarrier.face,
        index: activeCarrier.shelf_index,
      },
      facings: 1,
      sequence: carrierPlacements.length,
      orientation: product.orientation,
      effective_width_mm: eff,
      width_consumed_mm: eff,
    };
    setGraph((g) => ({ ...g, placements: [...g.placements, placement] }));
    setStatus(`Placed ${product.sku}`);
  }

  async function saveScene() {
    if (!planogram) return;
    setStatus("Saving…");
    try {
      const res = await api<{
        graph: SceneGraph;
        updated_at: string;
        validation: { ok: boolean };
      }>(`/api/planograms/${planogram.id}/scene/`, {
        method: "PUT",
        body: JSON.stringify({
          graph,
          schema_version: 5,
          updated_at: planogram.scene?.updated_at,
        }),
      });
      setGraph(res.graph);
      setPlanogram({
        ...planogram,
        scene: { graph: res.graph, updated_at: res.updated_at },
      });
      setStatus(res.validation.ok ? "Saved — width-fit OK" : "Saved with issues");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Save failed");
    }
  }

  if (loading) return <div className="loading">Opening floor layout…</div>;
  if (error) return <div className="error">{error}</div>;

  const viewBox = `${extent.minX} ${-extent.maxY} ${extent.w} ${extent.h}`;

  return (
    <div className="page wide canvas-shell">
      <div className="canvas-top">
        <button className="btn ghost" type="button" onClick={() => navigate("/")}>
          ← Stores
        </button>
        <strong>{store?.name}</strong>
        <span className="badge store">Store-local floor</span>
        {layout?.source_filename && (
          <span className="mono" style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {layout.source_filename}
            {layout.confidence_pct != null ? ` · ${layout.confidence_pct}% conf` : ""}
          </span>
        )}
        <div style={{ flex: 1 }} />
        {status && (
          <span className="mono" style={{ fontSize: "0.8rem", color: "var(--emerald-700)" }}>
            {status}
          </span>
        )}
        {selected && (
          <button className="btn ghost" type="button" onClick={() => setSelectedId(null)}>
            Back to floor (Esc)
          </button>
        )}
      </div>

      <div className={`canvas-body ${selected ? "split" : ""}`}>
        <aside className="library-rail">
          {!selected ? (
            <>
              <p className="panel-title">Fixture library</p>
              <p className="page-sub" style={{ marginTop: 0 }}>
                <span className="badge org">Org library</span> Drag onto the floor
              </p>
              <div className="chip-row" style={{ marginBottom: 10 }}>
                <button
                  type="button"
                  className={`chip ${family === "" ? "active" : ""}`}
                  onClick={() => setFamily("")}
                >
                  All
                </button>
                {families.map((f) => (
                  <button
                    key={f.family}
                    type="button"
                    className={`chip ${family === f.family ? "active" : ""}`}
                    onClick={() => setFamily(f.family)}
                  >
                    {f.label.split(" ")[0]}
                  </button>
                ))}
              </div>
              <div className="library-cards">
                {types.map((t) => (
                  <div
                    key={t.id}
                    className="library-card"
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData(
                        "application/x-fixture-type",
                        JSON.stringify(t),
                      );
                      e.dataTransfer.effectAllowed = "copy";
                    }}
                  >
                    <div
                      className="library-swatch"
                      style={{ background: FAMILY_COLORS[t.family] || "#94a3b8" }}
                    />
                    <div>
                      <div className="library-card-title">{t.name}</div>
                      <div className="mono" style={{ fontSize: "0.7rem" }}>
                        {t.family} · {t.default_params?.bay_width_mm || "—"} mm
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <p className="panel-title">Products</p>
              <p className="page-sub" style={{ marginTop: 0 }}>
                Drag pack fronts onto the shelf — or click +1
              </p>
              <div className="library-cards">
                {products.map((p) => (
                  <div
                    key={p.id}
                    className="library-card product"
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData(
                        "application/x-product",
                        JSON.stringify(p),
                      );
                      e.dataTransfer.effectAllowed = "copy";
                    }}
                  >
                    {p.front_image_url ? (
                      <img src={p.front_image_url} alt="" />
                    ) : (
                      <div className="thumb" />
                    )}
                    <div>
                      <div className="mono">{p.sku}</div>
                      <div style={{ fontSize: "0.75rem" }}>{p.name}</div>
                    </div>
                    <button
                      className="btn"
                      type="button"
                      style={{ padding: "4px 8px" }}
                      onClick={() => placeProductOnCarrier(p)}
                    >
                      +1
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}
        </aside>

        {!selected ? (
          <div
            className={`floor-stage ${dragOver ? "drop-active" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const raw = e.dataTransfer.getData("application/x-fixture-type");
              if (!raw) return;
              try {
                const ft = JSON.parse(raw) as FixtureType;
                dropFixtureType(ft, e.clientX, e.clientY);
              } catch {
                /* ignore */
              }
            }}
          >
            <svg
              ref={svgRef}
              viewBox={viewBox}
              className="floor-svg"
              preserveAspectRatio="xMidYMid meet"
            >
              <g transform={`scale(1,-1)`}>
                {/* underlay */}
                {(layout?.underlay?.features || []).map((f, i) => {
                  const coords = f.geometry?.coordinates || [];
                  if (coords.length < 2) return null;
                  const d = coords
                    .map((c, idx) => `${idx === 0 ? "M" : "L"}${c[0]},${c[1]}`)
                    .join(" ");
                  const kind = f.properties?.kind || "other";
                  const stroke =
                    kind === "doors"
                      ? "#10b981"
                      : kind === "walls"
                        ? "#334155"
                        : kind === "rooms"
                          ? "#94a3b8"
                          : "#64748b";
                  return (
                    <path
                      key={i}
                      d={d}
                      fill="none"
                      stroke={stroke}
                      strokeWidth={kind === "walls" ? 60 : 40}
                      vectorEffect="non-scaling-stroke"
                      opacity={0.85}
                    />
                  );
                })}
                {fixtures.map((fi) => {
                  const { w, d } = footprint(fi);
                  const color =
                    FAMILY_COLORS[fi.fixture_type_family || ""] || "#10b981";
                  return (
                    <g
                      key={fi.id}
                      transform={`translate(${fi.x_mm},${fi.y_mm}) rotate(${fi.rotation_deg})`}
                      style={{ cursor: "grab" }}
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        draggingPose.current = {
                          id: fi.id,
                          ox: e.clientX,
                          oy: e.clientY,
                        };
                        const onMove = (ev: MouseEvent) => {
                          if (!draggingPose.current) return;
                          const start = clientToWorld(
                            draggingPose.current.ox,
                            draggingPose.current.oy,
                          );
                          // Use delta in screen → approximate via successive points
                          const now = clientToWorld(ev.clientX, ev.clientY);
                          const dx = now.x - start.x;
                          const dy = now.y - start.y;
                          setFixtures((prev) =>
                            prev.map((f) =>
                              f.id === fi.id
                                ? {
                                    ...f,
                                    x_mm: Math.round(fi.x_mm + dx),
                                    y_mm: Math.round(fi.y_mm + dy),
                                  }
                                : f,
                            ),
                          );
                        };
                        const onUp = (ev: MouseEvent) => {
                          window.removeEventListener("mousemove", onMove);
                          window.removeEventListener("mouseup", onUp);
                          draggingPose.current = null;
                          const now = clientToWorld(ev.clientX, ev.clientY);
                          const start = clientToWorld(e.clientX, e.clientY);
                          const nx = Math.round(fi.x_mm + (now.x - start.x));
                          const ny = Math.round(fi.y_mm + (now.y - start.y));
                          const moved =
                            Math.abs(ev.clientX - e.clientX) > 4 ||
                            Math.abs(ev.clientY - e.clientY) > 4;
                          if (moved) {
                            savePose(fi.id, nx, ny).catch(() => undefined);
                          } else {
                            setSelectedId(fi.id);
                          }
                        };
                        window.addEventListener("mousemove", onMove);
                        window.addEventListener("mouseup", onUp);
                      }}
                    >
                      <rect
                        x={0}
                        y={0}
                        width={w}
                        height={d}
                        fill={color}
                        fillOpacity={0.85}
                        stroke="#0f172a"
                        strokeWidth={20}
                      />
                      <text
                        x={w / 2}
                        y={d / 2}
                        fill="#fff"
                        fontSize={140}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        transform={`scale(1,-1) translate(0,${-d})`}
                        style={{ pointerEvents: "none", fontFamily: "Sora, sans-serif" }}
                      >
                        {fi.name.slice(0, 18)}
                      </text>
                    </g>
                  );
                })}
              </g>
            </svg>
            {fixtures.length === 0 && (
              <div className="floor-hint">Drag a fixture from the left onto the floor</div>
            )}
          </div>
        ) : (
          <div
            className="elevation-stage"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const raw = e.dataTransfer.getData("application/x-product");
              if (!raw) return;
              try {
                placeProductOnCarrier(JSON.parse(raw) as Product);
              } catch {
                /* ignore */
              }
            }}
          >
            <div className="elevation-header">
              <div>
                <strong>{selected.name}</strong>
                <span className="badge store" style={{ marginLeft: 8 }}>
                  Elevation · placements SoT
                </span>
              </div>
              <button className="btn" type="button" onClick={saveScene}>
                Save
              </button>
            </div>
            <div className="carrier-pills">
              {selected.components.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={`chip ${c.id === activeCarrier?.id ? "active" : ""}`}
                  onClick={() => setCarrierId(c.id)}
                >
                  Shelf {c.shelf_index + 1}
                </button>
              ))}
              {selected.components.length === 0 && (
                <span className="page-sub">No shelf carriers on this fixture</span>
              )}
            </div>
            <div className="elevation-canvas-wrap">
              {activeCarrier ? (
                <ElevationCanvas
                  carrierWidthMm={activeCarrier.width_mm}
                  availableWidthMm={activeCarrier.available_width_mm}
                  placements={carrierPlacements}
                  productsById={productsById}
                />
              ) : (
                <div className="empty">This fixture has no shelves to merchandise.</div>
              )}
              <div className="on-canvas-meter">
                <div className="track">
                  <div
                    className={`used ${remaining < 0 ? "overflow" : ""}`}
                    style={{
                      width: `${Math.min(100, (usedWidth / Math.max(1, avail)) * 100)}%`,
                    }}
                  />
                </div>
                <div className={`meta ${remaining < 0 ? "warn" : ""}`}>
                  <span>
                    {usedWidth} / {avail} mm
                  </span>
                  <span>{remaining < 0 ? `overflow ${-remaining}` : `free ${remaining}`}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
