cmake_minimum_required(VERSION 4.1)
project(pyocctlite VERSION 0.0.1 LANGUAGES CXX)

# --------------------------------------------------------------------------- #
# SETTINGS
# --------------------------------------------------------------------------- #

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# --------------------------------------------------------------------------- #
# PYTHON and NANOBIND
# --------------------------------------------------------------------------- #
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

# --------------------------------------------------------------------------- #
# OpenCASCADE
# --------------------------------------------------------------------------- #
find_package(OpenCASCADE REQUIRED)
message(STATUS "OpenCASCADE include directory: ${OpenCASCADE_INCLUDE_DIR}")
message(STATUS "OpenCASCADE library directory: ${OpenCASCADE_LIBRARY_DIR}")
include_directories(${OpenCASCADE_INCLUDE_DIR})
link_directories(${OpenCASCADE_LIBRARY_DIR})

# --------------------------------------------------------------------------- #
# pyOCCT Lite
# --------------------------------------------------------------------------- #
file(GLOB SRCS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
nanobind_add_module(_occtlite ${SRCS})
target_link_libraries(_occtlite PRIVATE ${OpenCASCADE_LIBRARIES})
# Install in-tree: the extension and its stubs go into pyocctlite/
set(CMAKE_INSTALL_PREFIX ${CMAKE_CURRENT_SOURCE_DIR} CACHE PATH "Install into the source tree" FORCE)
install(TARGETS _occtlite DESTINATION pyocctlite)

# Type stubs for _occtlite, generated after install so mypy and readers see the binding API
nanobind_add_stub(
    _occtlite_stub
    INSTALL_TIME
    MODULE pyocctlite._occtlite
    PYTHON_PATH ${CMAKE_CURRENT_SOURCE_DIR}
    OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/pyocctlite/_occtlite.pyi
)
