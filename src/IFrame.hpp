#pragma once

#include "occtlite.hpp"

#include <gp_Ax2.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"
#include "IAxis.hpp"

// Interface class for a 3D coordinate frame
class IFrame {
public:

  // Make a frame at the given origin with standard orientation
  static IFrame MakeByOrigin(const IPoint& origin);

  // Construct from gp_Ax2
  explicit IFrame(const gp_Ax2& f) : frame_(f) {}

  // Get the origin point of the frame
  IPoint Origin() const {
    gp_Pnt origin = frame_.Location();
    return IPoint(origin);
  }

  // Get the axis of the frame
  IAxis Axis() const {
    return IAxis(frame_.Axis());
  }

  // Get the X-direction of the frame
  IVector XDirection() const {
    gp_Dir xDir = frame_.XDirection();
    return IVector(xDir);
  }

  // Get the Y-direction of the frame
  IVector YDirection() const {
    gp_Dir yDir = frame_.YDirection();
    return IVector(yDir);
  }

  // Get the Z-direction of the frame
  IVector ZDirection() const {
    gp_Dir zDir = frame_.Direction();
    return IVector(zDir);
  }

  // Conversion operator to gp_Ax2
  operator gp_Ax2() const {
    return frame_;
  }

private:
  gp_Ax2 frame_;
};

// Python bindings
void bind_IFrame(py::module& m);
