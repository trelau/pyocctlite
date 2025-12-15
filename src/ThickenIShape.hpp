#pragma once

#include "occtlite.hpp"

#include <BRepOffsetAPI_MakeThickSolid.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to make a hollow solid with a uniform thickness
class ThickenIShape {
public:

  // Construct a hollow solid from an open shell using a uniform thickness
  ThickenIShape(const IShape& shape, double thickness);

  // Construct a hollow solid by removing faces and using a uniform thickness
  ThickenIShape(const IShape& shape, const std::vector<IShape>& faces, double thickness, double tol = 1.0e-3);

  MAKE_SHAPE_METHODS(tool_);

private:
  BRepOffsetAPI_MakeThickSolid tool_;
};

// Python bindings
void bind_ThickenIShape(py::module& m);