#pragma once

#include "occtlite.hpp"

#include <BRepOffsetAPI_MakeOffset.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to offset a planar wire within its plane
class OffsetIWire {
public:
  // Offset a wire, finding its plane from its own geometry
  OffsetIWire(const IShape& wire, double distance);

  // Offset a wire on a spine face
  OffsetIWire(const IShape& wire, const IShape& spine, double distance);

  MAKE_SHAPE_METHODS(tool_);

private:
  BRepOffsetAPI_MakeOffset tool_;
};

// Python bindings
void bind_OffsetIWire(nb::module_& m);
