#pragma once

#include "occtlite.hpp"

#include "IFrame.hpp"

// Data structure for cylindrical surface data
struct ICylindricalData {
  IFrame Frame;
  double Radius = 0.0;
};

// Python bindings
void bind_ISurfaceData(nb::module_& m);
