#pragma once

#include "occtlite.hpp"

#include <gp_Dir2d.hxx>
#include <gp_Vec2d.hxx>

// Interface class for a 2D vector
class IVector2D {
public:

  // Make a vector by its X, Y components
  static IVector2D makeByXY(double x, double y);

  // Construct from gp_Vec2d
  explicit IVector2D(const gp_Vec2d& v) : vec_(v) {}

  // Construct from gp_Dir
  explicit IVector2D(const gp_Dir2d& d) : vec_(d) {}

  // Construct a vector by its X, Y, Z components
  IVector2D(double x, double y) : vec_(x, y) {}

  // Getters for X, Y, Z components
  double X() const {
    return vec_.X();
  }

  double Y() const {
    return vec_.Y();
  }

  // Make a scaled copy of this vector
  IVector2D Scaled(const double scale) const {
    return IVector2D(vec_.Scaled(scale));
  }

  // Conversion operator to gp_Vec2d
  operator gp_Vec2d() const {
    return vec_;
  }

private:
  gp_Vec2d vec_;
};

// Python bindings
void bind_IVector2D(py::module& m);
