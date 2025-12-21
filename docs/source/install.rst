Installation
============

Prerequisites
-------------

Before installing pyOCCT Lite, ensure you have the following installed:

*   **Conda** (Miniconda or Anaconda)
*   **CMake** (version 4.1 or higher)
*   **C++ Compiler**:

    *   Windows: Visual Studio 2022
    *   Linux: GCC or Clang
    *   macOS: Xcode

Environment Setup
-----------------

The use of a Conda environment is recommended to manage dependencies. A pre-configured `environment.yml` file is provided in the project root.

1.  Clone the repository:

    .. code-block:: bash

        git clone https://github.com/trelau/pyocctlite.git
        cd pyocctlite

2.  Create and activate the Conda environment:

    .. code-block:: bash

        conda env create -f environment.yml
        conda activate pyocctlite

Building from Source
--------------------

pyOCCT Lite uses CMake for its build system. To build and install the C++ extension into the ``pyocctlite/`` folder:

1.  Create a build directory:

    .. code-block:: bash

        mkdir build
        cd build

2.  Configure the project:

    *   **Windows (Visual Studio 2022)**:

        .. code-block:: bash

            cmake .. -G "Visual Studio 17 2022" -A x64

    *   **Linux / macOS**:

        .. code-block:: bash

            cmake ..

3.  Build and install the extension:

    .. code-block:: bash

        cmake --build . --config Release --target install

This will compile the C++ source files and place the resulting binary (e.g., ``_occtlite.pyd`` or ``_occtlite.so``) directly into the ``pyocctlite/`` directory.

Verifying the Installation
--------------------------

To ensure that pyOCCT Lite is correctly installed and functioning, run the test suite from the project root:

.. code-block:: bash

    python -m unittest discover tests

If all tests pass, your installation is successful.
