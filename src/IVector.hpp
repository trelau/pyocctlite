#pragma once

#include "occtlite.hpp"

#include <gp_Dir.hxx>
#include <gp_Vec.hxx>

// Interface class for a 3D vector
class IVector {
public:

  // Make a vector by its X, Y, Z components
  static IVector MakeByXYZ(double x, double y, double z);

  // Construct from gp_Vec
  explicit IVector(const gp_Vec& v) : vec_(v) {}

  // Construct from gp_Dir
  explicit IVector(const gp_Dir& d) : vec_(d) {}

  // Construct a vector by its X, Y, Z components
  IVector(double x, double y, double z) : vec_(x, y, z) {}

  // Getters for X, Y, Z components
  double X() const {
    return vec_.X();
  }

  double Y() const {
    return vec_.Y();
  }

  double Z() const {
    return vec_.Z();
  }

  // Make a scaled copy of this vector
  IVector Scaled(const double scale) const {
    return IVector(vec_.Scaled(scale));
  }

  // Conversion operator to gp_Vec
  operator gp_Vec() const {
    return vec_;
  }

private:
  gp_Vec vec_;
};

// Python bindings
void bind_IVector(py::module& m);
