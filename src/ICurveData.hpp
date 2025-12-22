#pragma once

#include "occtlite.hpp"

#include "IFrame.hpp"

// Data structure for circle data
struct ICircleData {
  IFrame frame;
  double radius = 0.0;
};

// Python bindings
void bind_ICurveData(py::module& m);
