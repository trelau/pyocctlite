#pragma once

#include "occtlite.hpp"

#include <gp_Pnt2d.hxx>

#include "IVector2D.hpp"

// Interface class for a 2D point
class IPoint2D {
public:
  // Make a point by its X, Y coordinates.
  static IPoint2D MakeByXY(double x, double y);

  // Construct a point from a gp_Pnt2d
  explicit IPoint2D(const gp_Pnt2d& p) : point_(p) {}

  // Get X, Y, Z coordinates
  double X() const { return point_.X(); }

  double Y() const { return point_.Y(); }

  // Make a copy of this point moved along a vector
  IPoint2D Translated(const IVector2D& vector) const { return IPoint2D(point_.Translated(vector)); }

  // Compute the distance to another point
  double Distance(const IPoint2D& other) const { return point_.Distance(other); }
  // Check if this point is equal to the other within a tolerance
  bool IsEqual(const IPoint2D& other, double tol = 1.0e-7) const {
    return point_.IsEqual(other, tol);
  }

  // Conversion operator to gp_Pnt2d
  operator gp_Pnt2d() const { return point_; }

private:
  gp_Pnt2d point_;
};

// Python bindings
void bind_IPoint2D(nb::module_& m);
