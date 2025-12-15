#pragma once

#include "occtlite.hpp"

#include <BRepAlgoAPI_Fuse.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to unite shapes
class UniteIShapes {
public:

  // Constructor to unite two shapes
  UniteIShapes(const IShape& target, const IShape& tool) : tool_(target, tool) {}

  // Constructor to unite a target shape with multiple tool shapes
  UniteIShapes(const IShape& target, const std::vector<IShape>& tools);

  // Constructor to unite multiple target shapes with a tool shape
  UniteIShapes(const std::vector<IShape>& targets, const IShape& tool);

  // Constructor to unite multiple target shapes with multiple tool shapes
  UniteIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools);

  MAKE_SHAPE_METHODS(tool_);

  // Get the intersection edges resulting from the unite operation
  std::vector<IShape> IntersectionEdges();

private:
  BRepAlgoAPI_Fuse tool_;
};

// Python bindings
void bind_UniteIShapes(py::module& m);
