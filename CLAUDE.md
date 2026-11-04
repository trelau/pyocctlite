# pyocctlite

A lightweight C++/nanobind wrapper exposing a Pythonic API over a narrow subset of OpenCASCADE (OCCT). Experimental; APIs are unstable.

## Commands

Run inside the conda env, whose cmake is new enough (≥4.1).

```bash
conda env create -f environment.yml && conda activate pyocctlite
pre-commit install            # once per clone

cmake -B build                # after any C++ change: build, then install
cmake --build build --config Release
cmake --install build         # puts _occtlite.pyd and its .pyi stub in pyocctlite/

python -m unittest discover -s tests
pre-commit run --all-files    # format, lint, type-check
```

- `pyocctlite/_occtlite.pyi` (generated on install) is the reference for the C++ binding API.
- OCCT API docs are the `//!` comments in its headers: grep `$CONDA_PREFIX/Library/include/opencascade` (Windows) or `$CONDA_PREFIX/include/opencascade`. For concepts and algorithm guides, see https://dev.opencascade.org/doc/overview/html/.
- A Claude Code hook formats every edited file and runs ruff and mypy on Python edits. Fix what it reports before moving on.
- After a C++ change, rebuild and install before editing Python that uses it; mypy reads the regenerated stub.
- Style is whatever the formatters produce. Otherwise prefer common, well-established conventions.

## Tone and Style

Unless otherwise instructed, when communicating with a user, be direct. Say (or write) only what needs to be said (or written). No more. No less.

## Workflow

- Before adding anything, find the closest existing analog and mirror it:
  - Value type: `IPoint` / `Point`
  - Kind family: `ICurve` / `Curve`, `Line`
  - Kind data: `ICurveData`
  - Shape tool: `FilletIShape`, `MakeIShape.hpp` / `ShapeTool`, `UniteShapes`
  - Composite: `Cylinder`
  - Collection tool: `MapIShape` / `MapShape`
  - Errors: `IErrors.hpp` / `errors.py`
- Follow the rules below. To break one, say so and ask first. When a rule is settled or changed, update this file in the same change.
- Non-trivial features get a design doc in `docs/features/<name>.md` (copy `_TEMPLATE.md`) before code. Read the relevant doc before working on a feature.
- Done means:
  - The build has no warnings.
  - Tests and pre-commit pass, and `examples/` still run.
  - A new binding is registered in `src/occtlite.cpp`, and a new module has a `docs/source/*.rst` page.
  - CLAUDE.md is updated.

## Design Rules

### Principles

- Narrow scope. Wrap only the OCCT needed for a simple Pythonic API.
- Flat architecture. No new base classes, registries, plugin systems, or metaprogramming without asking.
- Immutability. Types never change after construction; operations return new objects. Nothing mutates its inputs.
- SI units (meters, radians) in C++. Unit conversion, if any, belongs in Python.
- Python ≥ 3.12. Single-threaded: no threading, async, or GIL manipulation.

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
  - Arguments that select a kind take the class (`shape.map(Edge)`). A Python `<Name>Kind` enum (UPPER_CASE members, C++ values) exists only where kind is returned as a value (`Shape.kind`).
- **Kind data.** Parameters specific to one kind come back as an `I<Kind>Data` struct from `<Kind>Data()`, wrapped in `std::optional`. OCCT subclasses are never exposed.
- **2D** counterparts take a `2D` suffix and follow the 3D naming and patterns, not necessarily its coverage.
- **Composites** (objects with named parts, e.g. primitives) are Python-only, built from existing types and tools. They override kind-preserving operations to return the composite, mapping each part through the tool's history.

### C++ rules

- One type or tool per `.hpp`/`.cpp` pair, with `bind_<Name>` at the bottom of the `.cpp`. Trivial members go inline in the header.
- Store OCCT objects by value, with the wrapped algorithm as `tool_`. Never hold references or pointers to temporaries.
- Each `I` type has an `explicit` constructor from its OCCT type and a conversion operator back.
- Types are created only through static `Make<What>` factories (plus the OCCT constructor). Tools use constructors.
- Accessors have no `Get` prefix. Predicates start with `Is*`, and counts with `Num*` (not `Nb*`).
- `As<Kind>()` validates the kind, then downcasts. It is C++ only.
- A query that may not apply returns `std::optional`. Use standard containers in signatures.
- An OCCT base API shared by many tools is wrapped once, as a macro plus a binding template (`MakeIShape.hpp`). Ask before adding another.
- Tool queries build on demand, so Python never calls `Build()`.
- Domain errors live in `IErrors.hpp`, bound with a built-in base (`IKindMismatch` → `TypeError`, `IBuildFailed` → `RuntimeError`) and re-exported under Python names in `pyocctlite/errors.py`. Don't swallow OCCT exceptions.
- Bindings use `nb::arg` for every parameter, mirror the C++ defaults, and have a one-line docstring.
- Default tolerances follow OCCT's. Comments are brief and single-line.

### Python rules

- A wrapper stores its object as `self._i<name>` (`self._itool` for tools) and exposes it through a read-only `i<name>` property.
- `__init__` accepts only the `I` object (a composite accepts its parts). Alternate constructors are `by_*` classmethods that return `cls(...)`.
- C++ results are wrapped in the most specific class, via `by_i<name>`.
- `@property` for argument-free state queries; `@cached_property` when it builds a wrapper or calls an OCCT computation. Methods for operations, anything with arguments, and anything returning a tool or collection.
- Shapes compare and hash by `IsSame`. Geometry has no `__eq__`; it offers `is_equal(other, tol)`.
- Placement goes last and is optional: size arguments first, then `frame=None` (the global origin).
- Convenience methods (`shape.fillet(...)`) wrap a tool and return only its result. Use the tool directly for history or intermediate shapes.
- Collection-like tools implement `__len__`, `__iter__` and `__getitem__` and are `Generic[T]`.
- Indices are 0-based; convert OCCT's 1-based indices at the boundary. "Not found" is `None`.
- Errors: `TypeError` for a wrong type or kind, `ValueError` for bad values, `NotImplementedError` for unsupported kinds or inputs, `RuntimeError` when an operation reports failure. `assert` only for internal invariants.
- Type hints are as specific as possible (generics, `Self`). When an input type fixes the result type, narrow it: override in each shape subclass (`Face.extrude -> Solid`), or `@overload` on a generic tool's type parameter (`ExtrudeShape[Face].shape() -> Solid`).
- Sphinx-style docstrings (`:param:`, `:return:`, `:rtype:`) in the passive voice on all public API.

### Tests

- `unittest`, one file per module (`tests/test_<module>.py`).
- Cover the Python API: every `by_*` constructor, every property, and error cases. No tests for raw bindings.
- Compare floats with `assertAlmostEqual` (or `is_equal` for points).

### Open questions

Record inconsistencies here; decide before either variant spreads. None currently.
