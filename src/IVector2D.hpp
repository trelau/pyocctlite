#pragma once

#include "occtlite.hpp"

#include <gp_Dir2d.hxx>
#include <gp_Vec2d.hxx>

class IPoint2D;

// Interface class for a 2D vector
class IVector2D {
public:
  // Make a vector by its X, Y components
  static IVector2D MakeByXY(double x, double y);

  // Make a vector from one point to another
  static IVector2D MakeByPoints(const IPoint2D& p1, const IPoint2D& p2);

  // Construct from gp_Vec2d
  explicit IVector2D(const gp_Vec2d& v) : vec_(v) {}

  // Construct from gp_Dir
  explicit IVector2D(const gp_Dir2d& d) : vec_(d) {}

  // Getters for X, Y components
  double X() const { return vec_.X(); }

  double Y() const { return vec_.Y(); }

  // Get the magnitude of the vector
  double Magnitude() const { return vec_.Magnitude(); }

  // Make a scaled copy of this vector
  IVector2D Scaled(const double scale) const { return IVector2D(vec_.Scaled(scale)); }

  // Make the sum with another vector
  IVector2D Added(const IVector2D& other) const { return IVector2D(vec_.Added(other)); }

  // Make the difference with another vector
  IVector2D Subtracted(const IVector2D& other) const { return IVector2D(vec_.Subtracted(other)); }

  // Make a copy of this vector pointing the opposite way
  IVector2D Reversed() const { return IVector2D(vec_.Reversed()); }

  // Make a unit-length copy of this vector
  IVector2D Normalized() const { return IVector2D(vec_.Normalized()); }

  // Compute the dot product with another vector
  double Dot(const IVector2D& other) const { return vec_.Dot(other); }

  // Compute the scalar cross product with another vector
  double Cross(const IVector2D& other) const { return vec_.Crossed(other); }

  // Check if the magnitudes and directions match within tolerances
  bool IsEqual(const IVector2D& other, double tol = 1.0e-7, double angular_tol = 1.0e-12) const {
    return vec_.IsEqual(other, tol, angular_tol);
  }

  // Conversion operator to gp_Vec2d
  operator gp_Vec2d() const { return vec_; }

private:
  gp_Vec2d vec_;
};

// Python bindings
void bind_IVector2D(nb::module_& m);
