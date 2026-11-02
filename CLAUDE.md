# pyocctlite

pyOCCT Lite is a lightweight C++/nanobind wrapper around OpenCASCADE (OCCT) that exposes a Pythonic API for CAD geometry workflows. It is intentionally narrow in scope — wrapping only a minimal OCCT subset and favoring clarity over completeness. APIs are unstable; this is an experimental project.

## Environment Setup

Dependencies are managed via Conda:

```bash
conda env create -f environment.yml
conda activate pyocctlite
```

## Build

The project uses CMake. The compiled extension (`_occtlite`) must be rebuilt whenever C++ source files change.

```bash
cmake -B build
cmake --build build --config Release
cmake --install build  # installs _occtlite.pyd into pyocctlite/
```

## Running Tests

Tests use `unittest`:

```bash
python -m unittest discover -s tests
```

## Architecture

The codebase has two distinct layers:

### C++ Layer (`src/`)
Thin, hand-written nanobind bindings. Every bound class follows the naming pattern `I<Name>` (e.g., `IPoint`, `IShape`, `ICurve`). The module entry point is `src/occtlite.cpp`, which registers all bindings into the `_occtlite` nanobind module via `bind_<ClassName>(m)` calls.

### Python Layer (`pyocctlite/`)
High-level Pythonic wrappers around the C++ bindings. Each Python class wraps the corresponding `I*` object, stored as `self._i<name>` and exposed via an `i<name>` property. Construction uses class methods (e.g., `Point.by_xyz(x, y, z)`) rather than overloaded `__init__`.

### Adding a New Binding

When adding a new C++ class (e.g., `IFoo`):
1. Create `src/IFoo.hpp` and `src/IFoo.cpp` with a `bind_IFoo(nb::module_& m)` function
2. Include and call it in `src/occtlite.cpp`
3. Rebuild with CMake
4. Add a Python wrapper class in the appropriate `pyocctlite/*.py` module

The Python wrapper should accept the `I*` object in `__init__`, store it as `self._ifoo`, expose it via an `ifoo` property, and use `@classmethod` factory methods for construction.
