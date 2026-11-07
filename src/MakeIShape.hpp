#pragma once

#include "occtlite.hpp"

#include <BRepBuilderAPI_MakeShape.hxx>

#include "IShape.hpp"

// Base class for tools that wrap a derived tool of OCCT BRepBuilderAPI_MakeShape
class MakeIShape {
public:
  virtual ~MakeIShape() = default;

  // Execute the operation
  void Build() { Tool().Build(); }

  // Check if the operation completed successfully
  bool IsDone() { return Tool().IsDone(); }

  // Get the resulting shape, building if needed
  IShape Shape();

  // Check if the given input shape was deleted by this operation
  bool IsDeleted(const IShape& shape);

  // Get shapes generated from the given input shape
  std::vector<IShape> GeneratedShapes(const IShape& shape);

  // Get shapes modified from the given input shape
  std::vector<IShape> ModifiedShapes(const IShape& shape);

protected:
  // Get the wrapped tool
  virtual BRepBuilderAPI_MakeShape& Tool() = 0;

private:
  // Build the wrapped tool if needed, and throw if it fails
  void CheckBuilt();
};

// Python bindings
void bind_MakeIShape(nb::module_& m);
