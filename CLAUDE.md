# pyocctlite

Pythonic geometry API over a narrow slice of OpenCASCADE (OCCT), via a thin C++/nanobind layer.

## Commands

Setting up the environment (if using conda):
```bash
conda env create -f environment.yml && conda activate pyocctlite
pre-commit install
```

Building and installing the C++ interface:
```bash
cmake -B build && cmake --build build --config Release && cmake --install build
```

Running the test suite:
```bash
python -m unittest discover -s tests
```

Running the format, lint, and type checks:
```bash
pre-commit run --all-files
```

- After a C++ change, build andyes install before running Python checks; mypy reads the regenerated
`pyocctlite/_occtlite.pyi`.
- Temporary work goes in `scratch/`, generated output in `outputs/`.
- Clear with `git clean -fdX <dir>/`.

## Layers

**The Python API is the product; C++ serves it.**

- **C++** (`src/`, `I`-prefixed): private, and exists only to serve the Python API. Receive inputs, 
run OCCT, return results, handle failures. Keep it as simple and thin as possible.
- **Python** (`pyocctlite/`): naming, defaults, composition, validation. Wrappers hold their `I`
object as `i<name>` (`Point.ipoint`).

## Principles

If a change pulls against one of these, no pattern fits, or a conflict blocks a decision, stop and
propose how to reconcile it.

- **Consistency over cleverness.** Code is extended by analogy; follow the exemplar even when
something else looks locally better.
- **Small surface.** Wrap only what the Python API needs. Don't add options you aren't sure you need
yet.
- **OCCT does the modeling.** Python composes; it's not there to reimplement a low-level algorithm.
- **Immutable values.** Values never change; operations return new ones and never mutate inputs.
Tools are configured, then queried.
- **Root causes, not guards.** No speculative validation. When OCCT fails on a valid case, mark it
as an expected failure in a test and report it; don't silently work around it.
- **Familiar to CAD users.** Common CAD terms and conventions.

## Patterns

| Pattern | Use for | Exemplars |
|---|---|---|
| Type | One OCCT value or handle | `IPoint` / `Point` |
| Tool | Configurable algorithm or multiple results | `FilletIShape` / `FilletShape` |
| Kind family | Polymorphic OCCT family: one C++ type, one Python subclass per kind | `ICurve` / `Curve`, `Line` |
| Kind data | Parameters for one kind | `ICurveData` |
| Shared base API | One OCCT base API used by many tools | `MakeIShape.hpp`, `BooleanIShapes.hpp` |
| Collection | Sequence-like results | `MapIShape` / `MapShape` |
| Composite | Python-only object with named parts | `Cylinder`, `Styled` |
| Render | One-call output; the only module-level functions | `RenderIShapes` / `render_image` |
| Errors | Domain errors, both layers | `IErrors.hpp` / `errors.py` |

## Conventions

- Right-handed, Z-up. Order x, y, z; origin first. 0-based indices; radians.
- Constructors are `by_<inputs>` classmethods; `__init__` takes the `I` object or named parts.
- Operations are verbs returning new objects of the most specific type. Methods with a tool delegate
to it.
- Stored values are properties; derived values from C++ are `cached_property`; anything with inputs
is a method.
- Many-shape operations also accept one (`Edge | Iterable[Edge]`).
- Docstrings: one plain technical sentence on what it is or does, then `:param:`, `:return:`, and
`:raises:` where they apply. No types; they come from signatures.
- Public names and docstrings don't mention OCCT.
- Lengths are unitless.

## Workflow

1. New branch per task.
2. Pattern → C++ → Python → tests → docs.
3. Test implemented behavior, regressions, and known limitations, not every edge case.
4. Done: no build warnings; tests and pre-commit pass.
5. Summarize for review, including anything not verified. Commit only when asked.

## Resources

- `docs/pyocctlite-api.md`: public API (generated). `pyocctlite/_occtlite.pyi`: bindings (generated).
- OCCT: `//!` comments in `$CONDA_PREFIX/[Library/]include/opencascade`; guides at
https://dev.opencascade.org/doc/overview/html/
