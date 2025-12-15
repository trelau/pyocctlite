# pyOCCT Lite
A lightweight, Python-first wrapper around OpenCascade (OCCT) and Salome Mesh (SMESH).

🚧 Early development / experimental.

APIs are unstable and subject to change. This project is mostly to experiment with different API
design patterns.

## Goal
Provide a small, opinionated C++/pybind11 layer that exposes a **simple, Pythonic API**
for working with geometry, topology, and basic CAD/CAE workflows.

This project intentionally:
- Wraps only a **minimal subset** of OCCT/SMESH
- Favors **clarity over completeness**
- Keeps the C++ layer thin and explicit
- Avoids auto-generated bindings

## Scope (for now)
- Basic geometry (points, vectors, curves, surfaces)
- Topological shapes (edges, faces, solids)
- Simple construction and transformation operations
- Python bindings via `pybind11`

More advanced features (meshing, analysis, IO, viewers) may be added later.

## Non-Goals
- Full OCCT coverage
- GUI tools or interactive editors

## License
MIT
