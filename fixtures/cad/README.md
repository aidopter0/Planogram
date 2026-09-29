# CAD / BIM sample fixtures (D4 / D5)

| File | Format | Notes |
| --- | --- | --- |
| `sample-store.dxf` | DXF | Minimal sales-floor outline (walls, doors, room labels). Native parse path. |

## Converter stubs (Must formats)

Pipeline **accepts** DWG, DXF, RVT, IFC. Parse depth:

| Format | Path | If converter missing |
| --- | --- | --- |
| **DXF** | Native (`ezdxf`) | — |
| **DWG** | Convert → DXF via ODA File Converter / LibreDWG / `dwg2dxf` | Reject with actionable error — do not silent-skip |
| **RVT** | Convert/export to IFC or DXF (pinned tool) | Reject with “supply IFC/DXF or install converter” |
| **IFC** | Best-effort footprint extract (`ifcopenshell`) where identifiable | Partial extract OK; confidence / needs-review counts |

Place converter binaries on the VM and document paths in deploy notes. Confidence % is advisory; needs-review counts are primary.
