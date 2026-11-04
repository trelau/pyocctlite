#pragma once

#include "occtlite.hpp"

#include <BRepBuilderAPI_Transform.hxx>

#include "IShape.hpp"
#include "ITransform.hpp"
#include "MakeIShape.hpp"

// Tool to transform shapes
class TransformIShape {
public:
  // Constructor
  TransformIShape(const IShape& shape, const ITransform& trsf, const bool copyGeom = false,
                  const bool copyMesh = false)
      : tool_(shape, trsf, copyGeom, copyMesh) {}

  MAKE_SHAPE_METHODS(tool_);

  // Get the modified shape from the input shape
  IShape ModifiedShape(const IShape& shape) const;

private:
  BRepBuilderAPI_Transform tool_;
};

// Python bindings
void bind_TransformIShape(nb::module_& m);