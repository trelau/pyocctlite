#pragma once

#include "occtlite.hpp"

#include <BRepPrimAPI_MakeRevol.hxx>

#include "IAxis.hpp"
#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to revolve shapes
class RevolveIShape : public MakeIShape {
public:
  // Revolve the shape a full turn about the given axis
  RevolveIShape(const IShape& shape, const IAxis& axis) : tool_(shape, axis) {}

private:
  BRepBuilderAPI_MakeShape& Tool() override { return tool_; }
  BRepPrimAPI_MakeRevol tool_;
};

// Python bindings
void bind_RevolveIShape(nb::module_& m);
