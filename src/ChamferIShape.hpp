#pragma once

#include "occtlite.hpp"

#include <BRepFilletAPI_MakeChamfer.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to chamfer shapes
class ChamferIShape {
public:
  // Construct chamfer tool with the shape
  ChamferIShape(const IShape& shape) : tool_(shape) {}

  MAKE_SHAPE_METHODS(tool_);

  // Add an edge to be chamfered with the given distance on both adjacent faces
  void AddEdge(const IShape& edge, double distance) { tool_.Add(distance, edge.AsEdge()); }

private:
  BRepFilletAPI_MakeChamfer tool_;
};

// Python bindings
void bind_ChamferIShape(nb::module_& m);
