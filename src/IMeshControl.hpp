#pragma once

#include <optional>

#include "IShape.hpp"
#include "IMeshErrors.hpp"


// Interface class for mesh controls
class IMeshControl {
public:

  // Fatory methods to create mesh controls
  static IMeshControl Make1D(const IShape& shape, std::optional<double> edge_size = std::nullopt, std::optional<double> deflection = std::nullopt);

  static IMeshControl Make2D(const IShape& shape, std::optional<double> edge_size = std::nullopt, std::optional<double> deflection = std::nullopt, bool quads = false);

  static IMeshControl Make3D(const IShape& shape, std::optional<double> max_edge_size = std::nullopt, std::optional<double> deflection = std::nullopt);

  int Dimension() const { return dim_; }

  const IShape& Shape() const { return shape_; }

  const std::optional<double>& EdgeSize() const { return edge_size_; }
  const std::optional<double>& Deflection() const { return deflection_; }
  const bool AllowQuads() const { return quads_;  }

private:
  IMeshControl(int dim, const IShape& target, std::optional<double> max_edge_size, std::optional<double> deflection, bool quads);

  int dim_;
  IShape shape_;
  std::optional<double> edge_size_;
  std::optional<double> deflection_;
  bool quads_;
};

// Python bindings
void bind_IMeshControl(py::module& m);