#pragma once

#include "occtlite.hpp"

#include <BRepBuilderAPI_Copy.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to copy shapes
class CopyIShape : public MakeIShape {
public:
  // Make a copy of the shape
  CopyIShape(const IShape& shape, const bool copyGeom = true, const bool copyMesh = false)
      : tool_(shape, copyGeom, copyMesh) {}

  // Get the modified shape from the input shape
  IShape ModifiedShape(const IShape& shape) const;

private:
  BRepBuilderAPI_MakeShape& Tool() override { return tool_; }
  BRepBuilderAPI_Copy tool_;
};

// Python bindings
void bind_CopyIShape(nb::module_& m);