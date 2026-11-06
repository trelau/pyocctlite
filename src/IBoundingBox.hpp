#pragma once

#include "occtlite.hpp"

#include <Bnd_Box.hxx>

#include "IPoint.hpp"

// Interface class for an axis-aligned bounding box
class IBoundingBox {
public:
  // Construct from Bnd_Box
  explicit IBoundingBox(const Bnd_Box& box) : box_(box) {}

  // Get the corner with the smallest coordinates
  IPoint MinPoint() const { return IPoint(box_.CornerMin()); }

  // Get the corner with the largest coordinates
  IPoint MaxPoint() const { return IPoint(box_.CornerMax()); }

  // Conversion operator to Bnd_Box
  operator Bnd_Box() const { return box_; }

private:
  Bnd_Box box_;
};

// Python bindings
void bind_IBoundingBox(nb::module_& m);
