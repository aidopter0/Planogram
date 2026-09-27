# Planogram

AI-assisted grocery retail space visualization and planogram authoring.

Stack (architecture-owned): **Django 5 + DRF + session auth** · **PostgreSQL** (SQLite fallback for local demo) · **Vite / React / React Three Fiber** SPA · Design Language **v1** (slate / emerald).

## Quick start (local demo)

```bash
# Backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # leave DATABASE_URL empty → SQLite
python manage.py migrate
python manage.py seed_demo    # users, catalog, Coastal store + DXF underlay, products
python manage.py runserver 127.0.0.1:8451

# Frontend (second terminal)
cd frontend && npm install && npm run dev   # http://127.0.0.1:4521 (Vite HMR)
```

Open **[http://127.0.0.1:8451/login/](http://127.0.0.1:8451/login/)** — `designer` / `designer123`.

### Visual canvas journey

1. **New store** → upload DWG/DXF/RVT/IFC (sample DXF: `/media/layouts/sample-store.dxf`) → floor opens  
2. **Floor canvas** → drag fixtures from the left org library onto the CAD underlay  
3. **Click a fixture** → elevation / shelf strip → drag pack-front products onto shelves (width meter on canvas). Esc returns to floor.

| User | Password | Role |
| --- | --- | --- |
| `designer` | `designer123` | Designer |
| `steward` | `steward123` | Product Steward |
| `viewer` | `viewer123` | Viewer |
| `admin` | `admin123` | Admin |

### PostgreSQL

Set `DATABASE_URL=postgres://USER:PASS@HOST:5432/planogram` in `.env`.

## What this slice includes

1. Django apps: `accounts`, `stores`, `layouts`, `catalog`, `fixtures`, `products`, `planograms`, `api`, `core`
2. Session login / logout + role profile stub
3. CAD layout ingest (DXF native via `ezdxf`; DWG/RVT actionable reject; IFC stub footprint)
4. Org-global Fixture / Component / Display / Store Asset catalogs (Appendix A representative)
5. Planogram scene API + `available_width` width-fit (D3); floor pose SoT / elevation placement SoT (D2)
6. React SPA: **import-first new store → floor DnD fixtures → elevation DnD products**
7. R3F elevation facing strip + on-canvas width meter
8. `fixtures/cad/sample-store.dxf` + `fixtures/products/` CSV+ZIP seed
9. Binding decisions D1–D6 · Design Language v1

```bash
python manage.py seed_catalog
python manage.py seed_demo
```

## Ports

| Service | Port |
| --- | --- |
| Django API + login + SPA shell | **8451** |
| Vite dev (HMR modules) | **4521** |

## Test fixtures

- CAD: [`fixtures/cad/`](fixtures/cad/) — sample DXF + converter notes (D4)
- Products: [`fixtures/products/`](fixtures/products/) — CSV + ZIP (D5)
