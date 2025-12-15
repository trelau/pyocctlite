#pragma once

#include "occtlite.hpp"

#include <BRepFilletAPI_MakeFillet.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to fillet shapes
class FilletIShape {
public:

  // Construct fillet tool with the shape
  FilletIShape(const IShape& shape) : tool_(shape) {}

  MAKE_SHAPE_METHODS(tool_);

  // Add an edge to be filleted with the given radius
  void AddEdge(const IShape& edge, double radius) {
    tool_.Add(radius, edge.AsEdge());
  }

private:
  BRepFilletAPI_MakeFillet tool_;
};

// Python bindings
void bind_FilletIShape(py::module& m);