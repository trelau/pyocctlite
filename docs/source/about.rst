About
=====
pyOCCT Lite is a lightweight, Python-first wrapper around the OpenCascade (OCCT) geometry kernel and the Salome Mesh (SMESH) library.

Why pyOCCT Lite?
----------------
The OpenCascade Technology (OCCT) is a powerful and comprehensive CAD kernel, but its sheer size and complexity can be daunting. Many existing Python bindings for OCCT aim for full coverage, which often results in APIs that feel more like C++ than Python, or require navigating thousands of classes to perform simple operations.

pyOCCT Lite exists to provide a **simple, opinionated API** for common geometry and CAD workflows. It prioritizes clarity over completeness, exposing only the most essential parts of the underlying kernels through a clean, Pythonic interface.

Key Philosophy:

*   **Pythonic First**: Designed to feel natural to Python users, using `snake_case`, properties, and standard Python types.
*   **Clarity over Completeness**: We don't aim to wrap every OCCT function. We wrap what you actually need.
*   **Immutable Design**: Operations generally return new objects rather than mutating existing ones, leading to more predictable code.
*   **Thin C++ Layer**: The C++ interface layer is kept minimal and explicit, using `pybind11` for robust and efficient bindings.

Technology Stack
----------------
pyOCCT Lite is built on top of several industry-standard libraries:

*   **OpenCascade (OCCT)**: The core geometry and topology kernel used for 3D modeling.
*   **Salome Mesh (SMESH)**: A powerful library for mesh generation and manipulation.
*   **pybind11**: Used to create seamless C++ bindings for Python.
*   **Python**: The primary interface for users, providing a high-level and productive environment.

Project Status
--------------
pyOCCT Lite is currently in early development. While the core geometry and topology modules are functional, the API is subject to change as we refine the design patterns.
