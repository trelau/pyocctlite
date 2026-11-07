#pragma once

#include "occtlite.hpp"

#include <BRep_Builder.hxx>
#include <HLRBRep_Algo.hxx>
#include <HLRBRep_HLRToShape.hxx>

#include "IShape.hpp"
#include "IVector.hpp"

// Tool to find the visible and hidden lines of a shape in an orthographic view, as edges in the
// view's plane. In the results, x is to the right of the view, y is up and z is 0.
class HiddenLineIShape {
public:
  // Construct the tool from a shape, the direction toward the viewer and the up direction, which
  // must not be parallel
  HiddenLineIShape(const IShape& shape, const IVector& direction, const IVector& up);

  // Get the visible sharp edges and silhouettes
  IShape Visible();

  // Get the hidden sharp edges and silhouettes
  IShape Hidden();

  // Get the visible edges between faces that meet smoothly
  IShape VisibleSmooth();

  // Get the hidden edges between faces that meet smoothly
  IShape HiddenSmooth();

private:
  occ::handle<HLRBRep_Algo> algo_;
};

// Python bindings
void bind_HiddenLineIShape(nb::module_& m);
