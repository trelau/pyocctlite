#pragma once

#include "occtlite.hpp"

#include <gp_Pnt.hxx>

// Interface class for a 3D point
class IPoint {
public:

  // Make a point by its X, Y, Z coordinates.
  static IPoint MakeByXYZ(double x, double y, double z);

  // Construct a point from a gp_Pnt
  explicit IPoint(const gp_Pnt& p) : point_(p) {}

  // Construct a point by its X, Y, Z coordinates.
  IPoint(double x, double y, double z) : point_(x, y, z) {}

  // Get X, Y, Z coordinates
  double X() const {
    return point_.X();
  }

  double Y() const {
    return point_.Y();
  }

  double Z() const {
    return point_.Z();
  }

  // Compute the distance to another point
  double Distance(const IPoint& other) const {
    return point_.Distance(other);
  }
  // Check if this point is equal to the other within a tolerance
  bool IsEqual(const IPoint& other, double tol = 1.0e-7) const {
    return point_.IsEqual(other, tol);
  }

  // Conversion operator to gp_Pnt
  operator gp_Pnt() const {
    return point_;
  }

private:
  gp_Pnt point_;
};

// Python bindings
void bind_IPoint(py::module& m);
