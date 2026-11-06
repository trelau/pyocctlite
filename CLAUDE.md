# pyocctlite

Pythonic geometry API over a narrow slice of OpenCASCADE (OCCT), via a C++/nanobind layer.

## Commands

### Environment

conda is the reference setup. Any environment with cmake ≥ 4.1 and the dependencies in `environment.yml` works.

    conda env create -f environment.yml && conda activate pyocctlite
    pre-commit install  # once per clone

### Build

    cmake -B build
    cmake --build build --config Release
    cmake --install build  # installs the extension and its .pyi stub into pyocctlite/

After any C++ change, build and install before editing Python since mypy reads the regenerated stub.

### Test

    python -m unittest discover -s tests
    pre-commit run --all-files  # format, lint, type-check

A hook formats edits and runs ruff and mypy. Fix what it reports before moving on.

### Scratch

`scratch/` is the working folder for temporary work, never a system temp directory; clean it at your discretion. Generated data, like example output, goes in `outputs/`. Run from the repo root:

    python -m scratch.probe  # run a script in scratch/
    python -m examples.bottle  # writes to outputs/
    git clean -fdX scratch/  # delete its contents
    git clean -fdX outputs/  # delete its contents

## Principles

These are guardrails. Use judgment on how to achieve a task. If a change seems to pull against one, discuss it with the user before proceeding.

- **Python experience first.** The Python API is the product, and the C++ layer exists to serve it. Keep bindings simple and explicit. Don't reproduce OCCT's class hierarchy when Python doesn't need it.
- **Consistency over cleverness.** The API should be predictable from one example of each pattern. When in doubt, choose what makes the codebase more uniform.
- **Think big, start small.** Choose first versions that can grow without breaking callers.
- **Small surface.** Wrap only the OCCT the Python API needs, and make what's wrapped reachable from Python. When in doubt, leave it out.
- **Familiar to CAD users.** Terms, orientations, and argument meanings follow common CAD conventions.
- **Implementation stays private.** Public names and docstrings don't reference OCCT.
- **Clear layers.**
  - C++ (`src/` → `_occtlite`, `I`-prefixed) is thin: it takes its inputs, runs the OCCT algorithm, and returns the result or its error. Beyond memory safety, validation and application logic stay out of it. Special-purpose tools like the rasterizer are the exception.
  - Python (`pyocctlite/`) owns everything that makes the API feel Pythonic: defaults, naming, composition, conventions like 0-based indices (OCCT's are usually 1-based), and any validation a real failure has shown is needed.
  - Users work with Python wrappers; `I` objects stay behind `i<name>`.
- **Python features are backed by what's below.** Each Python argument or mode is a direct call or a true composition of lower-layer calls. What isn't implemented yet raises, and an argument that doesn't apply is documented as having no effect.
- **Immutable values.** Objects don't change after construction; operations return new objects and never mutate their inputs.
- **Unitless lengths.** OCCT has no length unit, so callers keep theirs consistent.
- **Root causes, not guards.** Take inputs, run the algorithm, return the result. Don't handle bad data or edge cases speculatively; consider adding logic when something actually fails. Fix the cause of a problem, or report it and leave the code alone. A signature broader than its implementation is unfinished intent, not a bug.
- **Short docs.** A docstring is one sentence on what the thing is or does, followed by its parameters, return value, and errors. No paragraphs on the underlying logic or what-ifs.

## Patterns

Start from existing patterns. If two patterns disagree, or the code disagrees with these patterns, raise it rather than silently picking one. If a new pattern is confirmed, consider adding it to this table.

| Pattern | Use for | Exemplars |
|---|---|---|
| Type | One OCCT value or handle: state plus queries | `IPoint` / `Point` |
| Tool | One OCCT algorithm: construct, configure, query | `FilletIShape` / `ShapeTool`, `UniteShapes` |
| Kind family | A polymorphic OCCT family: one C++ type with a kind, one Python subclass per kind | `ICurve` / `Curve`, `Line` |
| Kind data | Parameters specific to one kind | `ICurveData` |
| Shared OCCT base API | One base API used by many tools, wrapped once | `MakeIShape.hpp`, `BooleanIShapes.hpp` |
| Collection tool | Sequence-like results | `MapIShape` / `MapShape` |
| Composite | Python-only object with named parts | `Cylinder`, `Styled` |
| Render | One-call output built on a C++ tool: stateless Python functions | `RenderIShapes` / `render_image` |
| Errors | Domain errors across both layers | `IErrors.hpp` / `errors.py` |

## Conventions

- Coordinates are right-handed and Z-up.
- Directions and components are ordered x, y, z. An origin comes first (`Frame.by_vectors(origin, xvec, zvec)`).
- Indices are 0-based. Angles are radians.
- Constructors are `by_<inputs>` classmethods. `__init__` takes the `I` object or named parts.
- Operations are named with verbs (`translate`, `scale`, `normalize`) and return new objects.
- Shape methods delegate to a Python tool of the same operation (`fillet` → `FilletShape`).
- Stored or derived values are properties. Anything that takes inputs or runs an operation is a method.
- Operations that accept many shapes also accept one (`Edge | Iterable[Edge]`).
- Collections support Python protocols and may also have named methods.

## Workflow

- Typical order of work: identify pattern → C++ → Python → tests → docs.
- Start each new task on a new branch.
- Done means:
  - No build warnings.
  - Tests, pre-commit, and `examples/` run successfully.
  - Tests should cover implemented behavior and known limitations, not every imaginable edge case.
  - New bindings are registered in `src/occtlite.cpp`; a new module has a `docs/source/*.rst` page.
- When done, stop and summarize the changes for review. Commit only when the user asks.

## Resources

- `docs/pyocctlite-api.md` (generated by `python docs/gen_api.py`): the public Python API. Use `help()` for details.
- `pyocctlite/_occtlite.pyi` (generated on install): the binding API.
- OCCT API docs: `//!` comments in headers under `$CONDA_PREFIX/[Library/]include/opencascade`.
- OCCT concepts and algorithm guides: https://dev.opencascade.org/doc/overview/html/.