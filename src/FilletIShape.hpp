#pragma once

#include "occtlite.hpp"

#include <BRepFilletAPI_MakeFillet.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to fillet shapes
class FilletIShape : public MakeIShape {
public:
  // Construct fillet tool with the shape
  FilletIShape(const IShape& shape) : tool_(shape) {}

  // Add an edge to be filleted with the given radius
  void AddEdge(const IShape& edge, double radius) { tool_.Add(radius, edge.AsEdge()); }

private:
  BRepBuilderAPI_MakeShape& Tool() override { return tool_; }
  BRepFilletAPI_MakeFillet tool_;
};

// Python bindings
void bind_FilletIShape(nb::module_& m);