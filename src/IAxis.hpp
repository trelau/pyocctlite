#pragma once

#include "occtlite.hpp"

#include <gp_Ax1.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"

// Interface class for a 3D axis
class IAxis {
public:

  // Construct a point from a gp_Ax1
  explicit IAxis(const gp_Ax1& a) : axis_(a) {}

  // Get the origin point of the axis
  IPoint Origin() const {
    return IPoint(axis_.Location());
  }

  // Get the direction vector of the axis
  IVector Direction() const {
    return IVector(axis_.Direction());
  }

  // Conversion operator to gp_Ax1
  operator gp_Ax1() const {
    return axis_;
  }

private:
  gp_Ax1 axis_;
};

// Python bindings
void bind_IAxis(py::module& m);
