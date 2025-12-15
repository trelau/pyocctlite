#pragma once

#include "occtlite.hpp"

#include <BRepPrimAPI_MakePrism.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to extrude shapes
class ExtrudeIShape {
public:

  // Extrude the shape along the given vector
  ExtrudeIShape(const IShape& shape, const IVector& vector) : tool_(shape, vector) {}

  MAKE_SHAPE_METHODS(tool_);

  // Get the first shape of the extrusion
  IShape FirstShape() {
    TopoDS_Shape result = tool_.FirstShape();
    return IShape(result);
  }

  // Get the first shape of the extrusion for a given input shape
  IShape FirstShape(const IShape& s) {
    TopoDS_Shape result = tool_.FirstShape(s);
    return IShape(result);
  }

  // Get the last shape of the extrusion
  IShape LastShape() {
    TopoDS_Shape result = tool_.LastShape();
    return IShape(result);
  }

  // Get the last shape of the extrusion for a given input shape
  IShape LastShape(const IShape& s) {
    TopoDS_Shape result = tool_.LastShape(s);
    return IShape(result);
  }

private:
  BRepPrimAPI_MakePrism tool_;
};

// Python bindings
void bind_ExtrudeIShape(py::module& m);