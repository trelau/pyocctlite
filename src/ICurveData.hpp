#pragma once

#include "occtlite.hpp"

#include "IPoint.hpp"
#include "IVector.hpp"
#include "IFrame.hpp"

// Data structure for line data
struct ILineData {
  IPoint Origin;
  IVector Direction;
};

// Data structure for circle data
struct ICircleData {
  IFrame Frame;
  double Radius = 0.0;
};

// Python bindings
void bind_ICurveData(py::module& m);
