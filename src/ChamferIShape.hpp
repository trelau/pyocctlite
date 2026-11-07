#pragma once

#include "occtlite.hpp"

#include <BRepFilletAPI_MakeChamfer.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to chamfer shapes
class ChamferIShape : public MakeIShape {
public:
  // Construct chamfer tool with the shape
  ChamferIShape(const IShape& shape) : tool_(shape) {}

  // Add an edge to be chamfered with the given distance on both adjacent faces
  void AddEdge(const IShape& edge, double distance) { tool_.Add(distance, edge.AsEdge()); }

private:
  BRepBuilderAPI_MakeShape& Tool() override { return tool_; }
  BRepFilletAPI_MakeChamfer tool_;
};

// Python bindings
void bind_ChamferIShape(nb::module_& m);
