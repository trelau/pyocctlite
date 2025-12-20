#pragma once

#include "occtlite.hpp"

#include <BRepAlgoAPI_Cut.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool to cut shapes (boolean subtraction)
class CutIShapes {
public:

  // Constructor to cut two shapes
  CutIShapes(const IShape& target, const IShape& tool) : tool_(target, tool) {}

  // Constructor to cut a target shape with multiple tool shapes
  CutIShapes(const IShape& target, const std::vector<IShape>& tools);

  // Constructor to cut multiple target shapes with a tool shape
  CutIShapes(const std::vector<IShape>& targets, const IShape& tool);

  // Constructor to cut multiple target shapes with multiple tool shapes
  CutIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools);

  MAKE_SHAPE_METHODS(tool_);

  // Get the intersection edges resulting from the cut operation
  std::vector<IShape> IntersectionEdges();

private:
  BRepAlgoAPI_Cut tool_;
};

// Python bindings
void bind_CutIShapes(py::module& m);
