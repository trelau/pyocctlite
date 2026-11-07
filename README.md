# pyOCCT Lite
A lightweight, Python-first wrapper around OpenCascade (OCCT).

🚧 Early development / experimental.

APIs are unstable and subject to change. This project is mostly to experiment with different API
design patterns.

## Goal
Provide a small, opinionated C++/nanobind layer that exposes a **simple, Pythonic API**
for working with geometry, topology, and basic CAD workflows.

This project intentionally:
- Wraps only a **minimal subset** of OCCT
- Favors **clarity over completeness**
- Keeps the C++ layer thin and explicit
- Avoids auto-generated bindings

## Scope (for now)
- Basic geometry (points, vectors, curves, surfaces)
- Topological shapes (edges, faces, solids)
- Simple construction and transformation operations
- Basic analysis (length, area, volume, bounding box, centroid) and STEP export
- Rendering shapes to PNG images, with no GPU or display needed
- Engineering drawings with hidden-line views and dimensions, written to PNG, SVG or PDF
- Python bindings via `nanobind`

More advanced features (meshing, STEP import, interactive viewers) may be added later.

## Non-Goals
- Full OCCT coverage
- GUI tools or interactive editors

## License
MIT
