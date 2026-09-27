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
python manage.py seed_demo    # users, catalog, Coastal store, products, sample POG
python manage.py runserver 127.0.0.1:8451

# Frontend (second terminal)
cd frontend && npm install && npm run dev   # http://127.0.0.1:4521 (Vite HMR)
```

Open **[http://127.0.0.1:8451/login/](http://127.0.0.1:8451/login/)** — the Django shell loads the Vite SPA after sign-in.

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
3. Product Master: models, CSV (+ ZIP images) import, list/detail API, image upload
4. Fixture Type catalog + place Fixture Instance / batch bays on a store
5. Planogram editor API: scene graph, carriers, placements, `available_width` / width-fit validate (D3)
6. React SPA: login → stores → product master → elevation editor with pack-front proxies + width meter
7. R3F orthographic elevation canvas (facing strip)
8. `fixtures/cad/sample-store.dxf` + `fixtures/products/` CSV+ZIP seed
9. Binding decisions D1–D6 applied (see product decisions v0.9)

## Ports

| Service | Port |
| --- | --- |
| Django API + login + SPA shell | **8451** |
| Vite dev (HMR modules) | **4521** |

## Production-ish SPA build

```bash
cd frontend && npm run build   # → static/spa/
DJANGO_DEBUG=0 python manage.py runserver 127.0.0.1:8451
```

## Test fixtures

- CAD: [`fixtures/cad/`](fixtures/cad/) — sample DXF + converter notes (D4)
- Products: [`fixtures/products/`](fixtures/products/) — CSV + ZIP (D5)
