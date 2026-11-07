#pragma once

#include "occtlite.hpp"

#include <BRepOffsetAPI_ThruSections.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to loft shapes
class LoftIShape : public MakeIShape {
public:
  // Make a lofted shape
  LoftIShape(const bool isSolid = false, const bool isRuled = false, const double tol = 1.0e-6)
      : tool_(isSolid, isRuled, tol) {}

  void AddWire(const IShape& wire) { tool_.AddWire(wire.AsWire()); }

private:
  BRepBuilderAPI_MakeShape& Tool() override { return tool_; }
  BRepOffsetAPI_ThruSections tool_;
};

// Python bindings
void bind_LoftIShape(nb::module_& m);