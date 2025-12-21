# pyOCCT Lite Development Guidelines

## Project Philosophy
- **Lightweight & Python-First**: This is a minimal, opinionated wrapper around OpenCascade (OCCT) and Salome Mesh (SMESH).
- **Clarity over Completeness**: Do not aim for full OCCT coverage. Expose only what is needed for a simple, Pythonic API.
- **Explicit C++ Layer**: Keep the C++ layer thin and explicit. Avoid auto-generated bindings.
- **Pythonic API**: The Python layer should feel natural to Python users (snake_case, properties, type hints).
- **Follow Existing Patterns**: AI coding assistance should strictly follow existing coding style and design patterns. Do not invent new ones without asking.
- **Immutable Design**: Prefer immutable design patterns in both C++ and Python.
    - **Types**: Must return new objects from operations; never mutate internal state.
    - **Mutation**: Isolate mutation to specialized Tools or explicitly named mutators.
- **Numeric Units**: All C++ geometry operates in **SI units (meters, radians)**. Any unit handling or conversion belongs in the Python layer only.
- **Threading**: Assume **single-threaded use** unless explicitly documented otherwise. Do not introduce threading, async, or GIL manipulation without a specific request.
- **API Stability**: Public Python APIs (`pyocctlite/*`) are considered **stable once released**. Breaking changes require explicit request or a major version bump. Internal `_occtlite` APIs may change if the Python façade is preserved.
- **Golden Rule for AI**: **If unsure, ask before inventing.** When multiple reasonable designs exist, choose the simplest or request guidance.
- **No Over-Engineering**: Avoid adding base classes, registries, or plugin systems unless explicitly requested. Keep the architecture flat and simple.

## Quick Start for New Contributors

### Human Contributors
1. **Read This Document**: Understanding the philosophy and patterns is crucial before writing code.
2. **Set Up Environment**: Use `conda env create -f environment.yml && conda activate pyocctlite`
3. **Build & Test**: Follow the "Development Workflow" section below.
4. **Start Small**: Look for `TODO` comments or issues labeled "good first issue."
5. **When in Doubt**: Ask in discussions rather than guessing architectural intent.

### AI Assistants
1. **Always Check Existing Patterns**: Before writing new code, examine similar existing functionality.
2. **Never Introduce New Paradigms**: Stick to established patterns in the codebase.
3. **Ask Before Major Changes**: If a change affects multiple files or layers, describe the plan first.
4. **Test Your Changes**: Always provide test cases for new functionality.

## Project Structure
The project is organized into types (e.g., `Shape`, `Point`, `Vector`) and tools (e.g., `Unite`, `Copy`, `Extrude`). This pattern is followed in both layers.

- `src/` (C++ Interface Layer):
  - Primary "interface" layer wrapping OCCT/SMESH objects using `pybind11`.
  - **Types**: `I`-prefixed classes (e.g., `IShape`, `IPoint`, `IVector`) that represent basic OCCT entities.
  - **Tools**: Classes that perform operations (e.g., `UniteIShapes`, `ExtrudeIShape`, `FilletIShape`).
  - `occtlite.hpp`: Global includes and namespace aliases for the C++ layer.
  - `occtlite.cpp`: The main `PYBIND11_MODULE` definition where all bindings are registered.
- `pyocctlite/` (Python High-Level API):
  - The public-facing Python library that users interact with.
  - **_occtlite**: Raw C++ bindings. These MUST be 1:1 with the C++ API (PascalCase, identical names).
  - **pyocctlite**: High-level façade. Free to rename, reshape, and use Pythonic patterns (snake_case).
  - `geometry.py`: High-level wrappers for points, vectors, curves, and surfaces.
  - `topology.py`: High-level wrappers for topological shapes (Vertex, Edge, Face, etc.) and topological tools.
  - `mesh.py`: High-level wrappers for meshing functionality.
  - `_occtlite.*.pyd`: The compiled C++ extension (not tracked in Git).
- `tests/`: Python tests using `unittest`, organized by module (e.g., `test_geometry.py`).
- `examples/`: Example scripts and tutorials demonstrating library usage.
- `docs/`: Sphinx documentation source files.
- `environment.yml`: Conda environment definition for development and dependencies.
- `CMakeLists.txt`: Build configuration for the C++ extension.

## Change Impact Assessment

When making changes, consider the ripple effects across layers:

### High Impact Changes (Require Multi-Layer Updates)
- **New C++ Types**: Requires C++ class → pybind11 binding → Python wrapper → tests → documentation
- **API Breaking Changes**: Must update all dependent code and bump version
- **New Dependencies**: Update `environment.yml`, `CMakeLists.txt`, and documentation

### Medium Impact Changes
- **New Methods on Existing Types**: C++ method → binding → Python method → tests
- **New Tool Classes**: Follow the established `MakeShape` or custom tool patterns

### Low Impact Changes
- **Python-Only Features**: Can be added without touching C++ layer
- **Documentation Updates**: Generally safe but check for API accuracy
- **Test Improvements**: Low risk but verify they actually test the intended behavior

### Change Checklist
Before implementing significant changes:
1. **Does this follow existing patterns?** Check similar functionality first.
2. **What layers are affected?** C++, bindings, Python, tests, docs?
3. **Is this a breaking change?** If yes, document migration path.
4. **Performance implications?** Avoid creating performance bottlenecks in Python.

## Performance Guidelines

### What to Optimize
- **Bulk Operations**: Implement batch processing in C++ layer when handling many objects
- **Memory Allocations**: Minimize temporary object creation in tight loops
- **OCCT Object Lifetimes**: Store expensive-to-create objects (e.g., BRep builders) appropriately

### What NOT to Optimize
- **Python Loops**: If calling into C++ frequently, move the loop to C++ instead
- **Individual Operations**: Single geometry operations should prioritize clarity over micro-optimizations
- **Premature Optimization**: Don't optimize without profiling real usage patterns

### Performance Red Flags
- Creating temporary `I*` objects in loops
- Frequent conversion between Python and C++ containers
- Multiple OCCT operations that could be batched

## Coding Patterns

### C++ (Interface Layer)
- **Naming**: Use PascalCase for classes and methods (e.g., `IShape::Kind()`).
- **Accessors**: Prefer simple names over "Get" prefixes (e.g., `NumFaces()` instead of `GetNumFaces()`).
- **Prefixes**: Interface classes wrapping OCCT objects must start with `I` (e.g., `IVector`, `ICurve`).
- **Lifetimes**: 
    - Store `TopoDS_*` objects by value.
    - Store `Handle(Geom_*)` objects by value.
    - NEVER store references or pointers to temporary OCCT objects.
- **Types**: Use static factory methods for different ways of creating types instead of overloaded constructors (e.g., `IShape::MakeEdge`).
- **Tools**: Use constructors to initialize tool objects.
- **Bindings**: Manual pybind11 bindings in `bind_X` functions. The Python bindings API must match the C++ API exactly (methods, names, etc.) so users know when they are calling the C++ layer.
- **Comments**: Only brief single-line comments are needed; no extensive docstrings in C++.

### Python (High-Level Layer)
- **Naming**: Use PascalCase for classes and snake_case for methods/properties.
- **Alternative Constructors**: Use `@classmethod` or `@staticmethod` with the `by_` prefix for alternative creation paths:
  ```python
  @classmethod
  def by_xyz(cls, x: float, y: float, z: float) -> Point:
      ...
  ```
- **Type Hinting**: Use modern type hinting (including `from __future__ import annotations`).
- **Properties**: Use `@property` for getters.
- **Delegation**: High-level Python classes should store the underlying C++ `I`-object in a private attribute (e.g., `self._ishape`) and expose it via a read-only property (`self.ishape`).
- **Public vs Internal API**: 
    - Anything imported into `pyocctlite.__all__` is considered public API.
    - Underscore-prefixed attributes, methods, or modules (`_foo`) are internal and subject to change.
    - Do not expose new public symbols without explicit request.

## Testing
- **Priority**: The high-level Python bindings are the most important. Tests for C++ files or raw bindings are not required.
- **Coverage**: Ideally, provide test cases for:
  - Every way of creating types in Python (alternative constructors).
  - Every property.
  - Error conditions and edge cases.
  - Any other logical behavior that is important to preserve.
- **Test Organization**: One test file per Python module (e.g., `test_geometry.py` for `geometry.py`)
- **Precision**: Use appropriate tolerances for floating-point comparisons
- Use `unittest` for testing. Tests should be concise and focus on the Pythonic API. Run tests using:
  ```bash
  python -m unittest discover tests
  ```

## Documentation
- **Tone and Style**: Use passive voice for documentation. Avoid using first-person pronouns like "we" or "I".
- **Python**: Use Google-style or Sphinx-style docstrings for Python methods. Document parameters and return types clearly. High-level documentation is prioritized.
- **C++**: No extensive docstrings needed. Use brief single-line comments.
- **Examples**: Every major feature should have a corresponding example in `examples/`
- **API Changes**: Document breaking changes and migration paths in release notes

## Development Workflow

### 1. Environment Setup
- Use the provided `environment.yml` to create a Conda environment:
  ```bash
  conda env create -f environment.yml
  conda activate pyocctlite
  ```

### 2. Building the Extension
- The project uses CMake. To build and install the extension into the `pyocctlite/` folder:
  ```bash
  mkdir build
  cd build
  cmake .. -G "Visual Studio 17 2022" -A x64
  cmake --build . --config Release --target install
  ```
- Note: The `install` target is configured to copy the `.pyd` file directly into the `pyocctlite/` directory for easy development.

### 3. Running Tests
- Run tests from the root directory using:
  ```bash
  python -m unittest discover tests
  ```

### 4. Development Iteration
- **Make Changes**: Edit C++ or Python files
- **Rebuild**: Only needed if C++ changes were made
- **Test**: Run relevant test modules for quick feedback
- **Full Test**: Run complete test suite before committing

## Advanced Tips & OCCT Gotchas

### 1. OCCT Memory Management (Handles & Value Types)
- **Geometric Objects** (curves, surfaces, etc.): OCCT uses smart pointers called `Handle`. In the C++ layer, always store and pass these using `Handle(T)` (e.g., `Handle(Geom_Curve)`).
- **Topological Objects** (shapes, vertices, edges, etc.): These are lightweight wrapper objects (e.g., `TopoDS_Shape`) that perform their own internal reference counting. Do **NOT** use `Handle` with `TopoDS_*` types; store them by value.
- **Safety**: NEVER store references or pointers to temporary OCCT objects. Always store `TopoDS_*` and `Handle(Geom_*)` by value to ensure correct lifetime management.

### 2. Downcasting
- Use `Handle(T)::DownCast(base_handle)` for geometric objects.
- Use `TopoDS::Vertex(shape)`, `TopoDS::Edge(shape)`, etc., for topological objects (as seen in `IShape.hpp`).

### 3. Error Handling in C++
Follow this taxonomy to avoid scattered try/catch blocks:
- **Domain errors**: Use custom exceptions in `*Errors.hpp` for expected tool failures (e.g., `IsDone() == false`).
- **Programmer errors**: Use `std::logic_error` or `assert` for API misuse.
- **Unexpected failures**: Let OCCT exceptions propagate or wrap them once at the tool boundary.
Avoid swallowing exceptions or using generic `RuntimeError` where a specific domain error is more appropriate.

### 4. OCCT Precision and Tolerance
- OCCT uses different tolerance values for different operations
- Default linear tolerance is typically 1e-7 meters
- Angular tolerance is typically 1e-12 radians
- Use OCCT's precision classes (`Precision::Confusion()`) rather than hardcoded values where applicable

### 5. Common OCCT Patterns
- **Builder Pattern**: Many OCCT operations use builders (e.g., `BRepBuilderAPI_MakeEdge`)
- **Algorithm Pattern**: Complex operations often separate algorithm setup from execution
- **Iterator Pattern**: Use OCCT iterators for traversing topology (e.g., `TopExp_Explorer`)

## Extension & Community Guidelines
To make the project accessible for community contributions without requiring deep C++ expertise, follow these established patterns:

### 1. Leverage Patterns for OCCT Inheritance
OCCT often uses deep inheritance hierarchies (e.g., `BRepBuilderAPI_MakeShape`). To keep the C++ interface layer thin and consistent:
- **General Pattern**: Use macros and templates to wrap common OCCT base class functionality.
- **Example**: Use `MAKE_SHAPE_METHODS(tool_)` in the class definition and `bind_MakeShape<T>(cls)` in the bindings for any tool inheriting from `BRepBuilderAPI_MakeShape`. This avoids repeating boilerplate for `Build()`, `IsDone()`, `Shape()`, etc.

### 2. Standardized Type Conversion
- Every `I`-prefixed class should provide an `explicit` constructor from its corresponding OCCT type (e.g., `IShape(const TopoDS_Shape& s)`) and a conversion operator back to that type (e.g., `operator const TopoDS_Shape&() const`).
- This allows `I`-objects to be passed directly into native OCCT functions.

### 3. Separation of Concerns
- **Types vs Tools**:
    - **Types** (e.g., `IShape`, `IPoint`): Represent state + lightweight queries. They should have no heavy compute and must be immutable.
    - **Tools** (e.g., `UniteIShapes`, `ExtrudeIShape`): Represent operations. They can be stateful, heavy, and perform complex OCCT logic.
    - **Tool Execution Contract**: Tools must follow the pattern: **Construct → Execute → Query**. Tools should not perform irreversible operations implicitly on construction unless this matches the underlying OCCT behavior exactly. Tools should not mutate their inputs.
- **C++ Layer**: Focus strictly on executing the OCCT/SMESH operation and memory safety.
- **Python Layer**: Handle complex business logic, input validation (that doesn't affect memory safety), and convenience features (e.g., default values derived from other parameters).

### 4. Standardized Error Handling
- Define custom exception types in a corresponding `*Errors.hpp` file (following the `IShapeErrors.hpp` pattern) and bind them to Python.
- This allows Python users to catch specific domain errors (e.g., `ShapeTypeMismatch`) instead of generic `RuntimeError`s.

### 5. Use pybind11 Automatic Conversion
- Favor `std::vector` and standard containers in C++ signatures. The project is configured to automatically convert between Python lists and C++ vectors via `<pybind11/stl.h>`.

### 6. Contribution Workflow
1. Define the `I`-class/tool in `src/`.
2. Add the `bind_` function and register it in `occtlite.cpp`.
3. Implement the high-level Python class in `pyocctlite/`.
4. Add a test case in `tests/`.
5. Add example usage in `examples/` (for major features).
6. Update documentation as needed.