cmake_minimum_required(VERSION 4.1)
project(pyocctlite VERSION 0.0.1 LANGUAGES CXX)

# --------------------------------------------------------------------------- #
# SETTINGS
# --------------------------------------------------------------------------- #

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# --------------------------------------------------------------------------- #
# PYTHON and PYBIND11
# --------------------------------------------------------------------------- #
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)

# --------------------------------------------------------------------------- #
# VTK
# --------------------------------------------------------------------------- #
message(STATUS "Searching for VTK...")
find_package(VTK REQUIRED CommonCore)

# --------------------------------------------------------------------------- #
# Freetype
# --------------------------------------------------------------------------- #
message(STATUS "Searching for freetype...")
find_package(Freetype REQUIRED)

# --------------------------------------------------------------------------- #
# GLEW
# --------------------------------------------------------------------------- #
message(STATUS "Searching for GLEW...")
find_package(GLEW REQUIRED)

# --------------------------------------------------------------------------- #
# OpenCASCADE
# --------------------------------------------------------------------------- #
find_package(OpenCASCADE REQUIRED)
message(STATUS "OpenCASCADE include directory: ${OpenCASCADE_INCLUDE_DIR}")
message(STATUS "OpenCASCADE library directory: ${OpenCASCADE_LIBRARY_DIR}")
include_directories(${OpenCASCADE_INCLUDE_DIR})
link_directories(${OpenCASCADE_LIBRARY_DIR})

# --------------------------------------------------------------------------- #
# SMESH
# --------------------------------------------------------------------------- #
if(CMAKE_SIZEOF_VOID_P STREQUAL 8)
    add_definitions(-DSALOME_USE_64BIT_IDS)
endif(CMAKE_SIZEOF_VOID_P STREQUAL 8)

message(STATUS "Searching for SMESH...")
find_package(SMESH REQUIRED)

# --------------------------------------------------------------------------- #
# BOOST
# --------------------------------------------------------------------------- #
message(STATUS "Searching for Boost...")
find_package(Boost REQUIRED COMPONENTS filesystem thread serialization)

if(MSVC)
  # Find the shared boost libs
  add_definitions(-DBOOST_ALL_DYN_LINK)
  # Set postfix for debug libs
  if(NOT CMAKE_DEBUG_POSTFIX)
      set(CMAKE_DEBUG_POSTFIX d)
  endif()
endif()

message(STATUS "Boost include directory: ${Boost_INCLUDE_DIR}")
message(STATUS "Boost libraires: ${Boost_LIBRARIES}")
include_directories(${Boost_INCLUDE_DIR})

# --------------------------------------------------------------------------- #
# pyOCCT Lite
# --------------------------------------------------------------------------- #
file(GLOB SRCS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
pybind11_add_module(_occtlite ${SRCS})
target_link_libraries(_occtlite PRIVATE ${OpenCASCADE_LIBRARIES} ${SMESH_LIBRARIES})
install(TARGETS _occtlite DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/pyocctlite)