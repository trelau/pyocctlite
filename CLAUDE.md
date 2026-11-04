# pyocctlite

pyOCCT Lite is a lightweight C++/nanobind wrapper around OpenCASCADE (OCCT) that exposes a Pythonic API for CAD geometry workflows. It is intentionally narrow in scope — wrapping only a minimal OCCT subset and favoring clarity over completeness. APIs are unstable; this is an experimental project.

## Commands

Run everything inside the conda env. Use the env's cmake: the system one may be older than the required 4.1.

```bash
conda env create -f environment.yml
conda activate pyocctlite
pre-commit install  # once per clone: ruff + mypy on every commit

# Rebuild after any C++ change; install puts _occtlite.pyd and its .pyi stub in pyocctlite/
cmake -B build
cmake --build build --config Release
cmake --install build

python -m unittest discover -s tests
python -m mypy
ruff check pyocctlite tests examples
```

`pyocctlite/_occtlite.pyi` (generated) is the reference for the C++ binding API.

A Claude Code hook (`.claude/settings.json`) runs ruff and mypy after every Python edit. Fix what it reports before moving on.

## Tone and Style

Unless otherwise instructed, when communicating with a user, be direct. Say (or write) only what needs to be said (or written). No more. No less.

## Workflow

- Before adding anything, find the closest existing analog and mirror it.
- Follow the rules below. To break one, say so and ask first. When a rule is settled or changed, update this file in the same change.
- Non-trivial features get a design doc in `docs/features/<name>.md` (copy `_TEMPLATE.md`) before code. Read the relevant doc before working on a feature.
- A new binding touches: `src/<Name>.hpp/.cpp`, registration in `src/occtlite.cpp`, the wrapper in `pyocctlite/`, and tests.
- Done means:
  - The build has no warnings, and install succeeds.
  - Tests, mypy and ruff are clean.
  - `examples/` still run.
  - A new module gets a `docs/source/*.rst` page.
  - CLAUDE.md is updated.
- Canonical examples to mirror:
  - Value type: `IPoint` / `Point`
  - Kind family: `ICurve` / `Curve`, `Line`
  - Kind data: `ICurveData`
  - Shape tool: `FilletIShape`, `MakeIShape.hpp` / `ShapeTool`, `UniteShapes`
  - Composite: `Cylinder`
  - Collection tool: `MapIShape` / `MapShape`
  - Errors: `IErrors.hpp` / `errors.py`

## Design Rules

### Principles

- Narrow scope. Wrap only the OCCT needed for a simple Pythonic API.
- Flat architecture. No new base classes, registries, plugin systems, or metaprogramming without asking.
- Immutability. Types never change after construction; operations return new objects. Nothing mutates its inputs.
- SI units (meters, radians) in C++. Unit conversion, if any, belongs in Python.
- Python 3.12 is the minimum version (`pyproject.toml` checks against it). Don't use newer language or stdlib features.
- Single-threaded. No threading, async, or GIL manipulation.

### Two layers

| | C++ (`src/` → `_occtlite`) | Python (`pyocctlite/`) |
|---|---|---|
| Role | Thin, explicit OCCT wrapper | Public, Pythonic API |
| Naming | PascalCase, `I` prefix | PascalCase classes, snake_case members |
| Bindings | Hand-written, 1:1 with C++ names | Free to rename and reshape |
| Logic | OCCT calls and memory safety only | Validation, defaults, convenience, composition |

The public Python API takes and returns Python wrappers. `I` objects are reachable only through the `i<name>` property.

### Building blocks

- **Types** wrap one OCCT value or handle (`gp_*`, `Handle(Geom_*)`, `TopoDS_Shape`): state plus queries.
- **Tools** wrap one OCCT algorithm. They are stateful (construct → configure → execute → query).
  - Named `<Verb>I<Noun>[s]` in C++ (`FilletIShape`, `UniteIShapes`, `ProjectIPointToICurve`). Python drops the `I`.
- **Kinds.** A polymorphic OCCT family (shapes, curves, surfaces) is one `I` type with a `Kind()` enum (`I<Name>Kind`, mirroring OCCT's enum where one exists).
  - Python mirrors it with a base class plus one subclass per supported kind.
  - The base's static `by_i<name>()` dispatches on kind, and each subclass's `__init__` checks its kind.
  - An argument that selects a kind takes the class (`shape.map(Edge)`), not an enum. A Python enum `<Name>Kind` exists only where kind is exposed as a value (`Shape.kind`). Its members are UPPER_CASE, and their values are the C++ enum values.
- **Kind data.** Parameters specific to one kind come back as an `I<Kind>Data` struct from `<Kind>Data()`, wrapped in `std::optional`. OCCT subclasses are never exposed.
- **2D** counterparts take a `2D` suffix and follow the 3D naming and patterns. They don't need the same coverage.
- **Composites** (objects with named parts, e.g. primitives) are Python-only, built from existing types and tools.
  - They override kind-preserving operations to return the composite, mapping each named part through the tool's history.

### C++ rules

- One type or tool per `.hpp`/`.cpp` pair, with `bind_<Name>` at the bottom of the `.cpp`. Trivial members go inline in the header.
- Store OCCT objects by value, with the wrapped algorithm as `tool_`. Never hold references or pointers to temporaries.
- Each `I` type has an `explicit` constructor from its OCCT type and a conversion operator back.
- Types are created only through static `Make<What>` factories (plus the OCCT constructor). Tools use constructors.
- Accessors have no `Get` prefix. Predicates start with `Is*`, and counts with `Num*` (not `Nb*`).
- `As<Kind>()` validates the kind, then downcasts. It is C++ only.
- A query that may not apply returns `std::optional`.
- An OCCT base API shared by many tools is wrapped once, as a macro plus a binding template (`MakeIShape.hpp`). Ask before adding another.
- Tool queries build on demand.
- Domain errors live in `IErrors.hpp` and are bound with a built-in base:
  - `IKindMismatch` → `TypeError`
  - `IBuildFailed` → `RuntimeError`
- Don't swallow OCCT exceptions.
- Use standard containers in signatures.
- Bindings use `nb::arg` for every parameter, mirror the C++ defaults, and have a one-line docstring.
- Default tolerances follow OCCT's.
- Comments are brief and single-line.

### Python rules

- A wrapper stores its object as `self._i<name>` (`self._itool` for tools) and exposes it through a read-only `i<name>` property.
- `__init__` accepts only the `I` object (a composite accepts its parts). Alternate constructors are `by_*` classmethods that return `cls(...)`.
- C++ results are wrapped in the most specific class, via `by_i<name>`.
- `@property` is for argument-free state queries. Use `@cached_property` when the query builds a wrapper object or calls an OCCT computation (types are immutable, so caching is safe). Use methods for operations, anything with arguments, and anything that returns a tool or collection.
- Shapes compare and hash by `IsSame`. Geometry doesn't define `__eq__`; it offers `is_equal(other, tol)` instead.
- Placement goes last and is optional: size arguments come first, then `frame=None`, which defaults to the global origin.
- Never call `Build()`. Getting the result builds the tool.
- Convenience methods (`shape.fillet(...)`) wrap a tool and return only its result. Use the tool directly for history or intermediate shapes.
- Collection-like tools implement `__len__`, `__iter__` and `__getitem__` and are `Generic[T]`.
- Indices are 0-based; convert OCCT's 1-based indices at the boundary. "Not found" is `None`.
- Errors:
  - `TypeError` for a wrong type or kind.
  - `ValueError` for bad values.
  - `NotImplementedError` for unsupported kinds or inputs.
  - `RuntimeError` when an operation reports failure (e.g. a `False` status from C++).
  - `assert` only for internal invariants.
  - C++ domain errors are re-exported under Python names in `pyocctlite.errors` (`KindMismatch`, `BuildFailed`). Add new ones there.
- `from __future__ import annotations`. Type hints are as specific as they can be, using generics and `Self`. When the result type is fixed by the input type, narrow it: override the method in each shape subclass (`Face.extrude -> Solid`), and use `@overload` on a generic tool's type parameter (`ExtrudeShape[Face].shape() -> Solid`).
- Sphinx-style docstrings (`:param:`, `:return:`, `:rtype:`) in the passive voice on all public API.

### Tests

- `unittest`, one file per module (`tests/test_<module>.py`).
- Cover the Python API: every `by_*` constructor, every property, and error cases. No tests for raw bindings.
- Compare floats with `assertAlmostEqual` (or `is_equal` for points).

### Open questions

Record inconsistencies here; decide before either variant spreads.

- None currently.
