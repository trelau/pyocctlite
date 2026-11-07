#pragma once

#include "occtlite.hpp"

#include "IFrame.hpp"
#include "IFrame2D.hpp"
#include "IPoint.hpp"
#include "IPoint2D.hpp"
#include "IVector.hpp"
#include "IVector2D.hpp"

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

// Data structure for ellipse data
struct IEllipseData {
  IFrame Frame;
  double MajorRadius = 0.0;
  double MinorRadius = 0.0;
};

// Data structure for 2D line data
struct ILine2DData {
  IPoint2D Origin;
  IVector2D Direction;
};

// Data structure for 2D circle data
struct ICircle2DData {
  IFrame2D Frame;
  double Radius = 0.0;
};

// Data structure for 2D ellipse data
struct IEllipse2DData {
  IFrame2D Frame;
  double MajorRadius = 0.0;
  double MinorRadius = 0.0;
};

// Python bindings
void bind_ICurveData(nb::module_& m);
