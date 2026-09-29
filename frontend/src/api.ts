const API_BASE = import.meta.env.VITE_API_BASE || "";

function getCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : null;
}

export async function ensureCsrf(): Promise<string> {
  await fetch(`${API_BASE}/accounts/csrf/`, { credentials: "include" });
  return getCookie("csrftoken") || "";
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    if (method !== "GET" && method !== "HEAD") {
      headers.set("Content-Type", "application/json");
    }
  }
  if (method !== "GET" && method !== "HEAD") {
    const csrf = getCookie("csrftoken") || (await ensureCsrf());
    headers.set("X-CSRFToken", csrf);
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });
  if (res.status === 401) {
    window.location.href = "/login/";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type User = {
  authenticated: boolean;
  id: number;
  username: string;
  role: string;
};

export type Store = {
  id: number;
  name: string;
  code: string;
  cluster_tag: string;
  status: string;
};

export type Product = {
  id: number;
  sku: string;
  name: string;
  brand: string;
  category: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  orientation: string;
  front_image_url: string | null;
  effective_width_mm: number;
  readiness: string;
  image_incomplete: boolean;
};

export type ComponentInstance = {
  id: number;
  fixture: number;
  component_type: number;
  component_type_code: string;
  face: string;
  shelf_index: number;
  height_mm: number;
  width_mm: number;
  depth_mm: number;
  reserved_insets_mm: number;
  available_width_mm: number;
};

export type FixtureInstance = {
  id: number;
  store: number;
  name: string;
  fixture_type_code: string;
  fixture_type_name: string;
  bay_index: number;
  bay_width_mm: number;
  x_mm: number;
  y_mm: number;
  components: ComponentInstance[];
};

export type Planogram = {
  id: number;
  store: number;
  name: string;
  status: string;
  target_fixture_ids: number[];
  scene?: {
    schema_version: number;
    graph: SceneGraph;
    updated_at: string;
  };
};

export type Placement = {
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

export type SceneGraph = {
  schema_version: number;
  units: string;
  blocks: unknown[];
  placements: Placement[];
};

export type WidthSummary = {
  available_width_mm: number;
  used_width_mm: number;
  remaining_width_mm: number;
  overflow: boolean;
  placements: Placement[];
};
