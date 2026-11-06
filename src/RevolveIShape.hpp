#pragma once

#include "occtlite.hpp"

#include <BRepPrimAPI_MakeRevol.hxx>

#include "IAxis.hpp"
#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to revolve shapes
class RevolveIShape {
public:
  // Revolve the shape a full turn about the given axis
  RevolveIShape(const IShape& shape, const IAxis& axis) : tool_(shape, axis) {}

  MAKE_SHAPE_METHODS(tool_);

private:
  BRepPrimAPI_MakeRevol tool_;
};

// Python bindings
void bind_RevolveIShape(nb::module_& m);
