#pragma once

#include "occtlite.hpp"

#include <gp_Ax22d.hxx>

#include "IPoint2D.hpp"
#include "IVector2D.hpp"

// Interface class for a 2D coordinate frame
class IFrame2D {
public:

  // Make a frame at the given origin with standard orientation
  static IFrame2D MakeByOrigin(const IPoint2D& origin);

  static IFrame2D MakeByVector(const IPoint2D& origin, const IVector2D& xVector);

  // Construct from gp_Ax22d
  explicit IFrame2D(const gp_Ax22d& f) : frame_(f) {}

  // Get the origin point of the frame
  IPoint2D Origin() const {
    gp_Pnt2d origin = frame_.Location();
    return IPoint2D(origin);
  }

  // Get the X-direction of the frame
  IVector2D XDirection() const {
    gp_Dir2d xDir = frame_.XDirection();
    return IVector2D(xDir);
  }

  // Get the Y-direction of the frame
  IVector2D YDirection() const {
    gp_Dir2d yDir = frame_.YDirection();
    return IVector2D(yDir);
  }

  // Conversion operator to gp_Ax22d
  operator gp_Ax22d() const {
    return frame_;
  }

private:
  gp_Ax22d frame_;
};

// Python bindings
void bind_IFrame2D(py::module& m);
