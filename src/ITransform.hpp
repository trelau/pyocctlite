#pragma once

#include "occtlite.hpp"

#include <gp_Trsf.hxx>

#include "IAxis.hpp"
#include "IPoint.hpp"
#include "IVector.hpp"

// Interface class for a 3D transformation
class ITransform {
public:
  // Make a mirror transformation defined by a point and a normal vector.
  static ITransform MakeMirror(const IPoint& origin, const IVector& normal);

  // Make a rotation transformation about an axis by an angle in radians.
  static ITransform MakeRotation(const IAxis& axis, double angle);

  // Make a translation transformation along a vector.
  static ITransform MakeTranslation(const IVector& vector);

  // Construct a transformation from a gp_Trsf
  explicit ITransform(const gp_Trsf& t) : trsf_(t) {}

  // Conversion operator to gp_Trsf
  operator gp_Trsf() const { return trsf_; }

private:
  gp_Trsf trsf_;
};

// Python bindings
void bind_ITransform(nb::module_& m);
