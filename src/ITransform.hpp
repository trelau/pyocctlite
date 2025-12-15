#pragma once

#include "occtlite.hpp"

#include <gp_Trsf.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"

// Interface class for a 3D transformation
class ITransform {
public:

  // Make a mirror transformation defined by a point and a normal vector.
  static ITransform MakeMirror(const IPoint& origin, const IVector& normal);
  
  // Construct a transformation from a gp_Trsf
  explicit ITransform(const gp_Trsf& t) : trsf_(t) {}

  // Conversion operator to gp_Trsf
  operator gp_Trsf() const {
    return trsf_;
  }

private:
  gp_Trsf trsf_;
};

// Python bindings
void bind_ITransform(py::module& m);
