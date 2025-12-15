#pragma once

#include "occtlite.hpp"

#include <TopTools_IndexedMapOfShape.hxx>

#include "IShape.hpp"

// Tool to map shapes
class MapIShape {
public:

  // Constructor
  MapIShape(const IShape& shape, const IShapeKind kind);

  // Get the extent of the map
  int Extent() const {
    return tool_.Extent();
  }

  // Get the size of the map
  int Size() const {
    return tool_.Size();
  }

  // Find the shape by index
  IShape FindShape(const int index) const {
    return IShape(tool_.FindKey(index));
  }

  // Find the index of the shape
  int FindIndex(const IShape& shape) const {
    return tool_.FindIndex(shape);
  }

  // Check if the map contains the shape
  bool Contains(const IShape& shape) const {
    return tool_.Contains(shape);
  }

private:
  TopTools_IndexedMapOfShape tool_;
};

// Python bindings
void bind_MapIShape(py::module& m);