#pragma once

#include "occtlite.hpp"

#include <TopExp_Explorer.hxx>

#include "IShape.hpp"

// Tool to explore shapes
class ExploreIShape {
public:

  // Constructor
  ExploreIShape(const IShape& shape, const IShapeKind find, const IShapeKind avoid = IShapeKind::Shape)
    : tool_(shape, static_cast<TopAbs_ShapeEnum>(find), static_cast<TopAbs_ShapeEnum>(avoid)) {
  }

  // Check if there are more shapes to explore
  bool More() const {
    return tool_.More();
  }

  // Move to the next shape
  void Next() {
    tool_.Next();
  }

  // Get the current shape
  IShape Current() const {
    return IShape(tool_.Current());
  }

private:
  TopExp_Explorer tool_;
};

// Python bindings
void bind_ExploreIShape(py::module& m);