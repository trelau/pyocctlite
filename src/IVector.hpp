#pragma once

#include "occtlite.hpp"

#include <gp_Dir.hxx>
#include <gp_Vec.hxx>

class IPoint;

// Interface class for a 3D vector
class IVector {
public:
  // Make a vector by its X, Y, Z components
  static IVector MakeByXYZ(double x, double y, double z);

  // Make a vector from one point to another
  static IVector MakeByPoints(const IPoint& p1, const IPoint& p2);

  // Construct from gp_Vec
  explicit IVector(const gp_Vec& v) : vec_(v) {}

  // Construct from gp_Dir
  explicit IVector(const gp_Dir& d) : vec_(d) {}

  // Getters for X, Y, Z components
  double X() const { return vec_.X(); }

  double Y() const { return vec_.Y(); }

  double Z() const { return vec_.Z(); }

  // Get the magnitude of the vector
  double Magnitude() const { return vec_.Magnitude(); }

  // Make a scaled copy of this vector
  IVector Scaled(const double scale) const { return IVector(vec_.Scaled(scale)); }

  // Make a unit-length copy of this vector
  IVector Normalized() const { return IVector(vec_.Normalized()); }

  // Compute the dot product with another vector
  double Dot(const IVector& other) const { return vec_.Dot(other); }

  // Make the cross product with another vector
  IVector Cross(const IVector& other) const { return IVector(vec_.Crossed(other)); }

  // Conversion operator to gp_Vec
  operator gp_Vec() const { return vec_; }

private:
  gp_Vec vec_;
};

// Python bindings
void bind_IVector(nb::module_& m);
