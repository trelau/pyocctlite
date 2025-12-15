#pragma once

#include "occtlite.hpp"

#include <Geom_Surface.hxx>
#include <Geom_CylindricalSurface.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"
#include "IFrame.hpp"

// Enumeration for surface kinds
enum class ISurfaceKind {
  Unknown = 0,
  Plane,
  Conical,
  Cylindrical,
  Spherical,
  Toroidal,
  Bezier,
  BSpline,
  Trimmed
};

// Interface class for a surface
class ISurface {
public:

  // Factory methods to create different types of surfaces
  static ISurface MakeCylindrical(const IFrame& frame, const double radius);

  // Constructor from Handle(Geom_Surface)
  explicit ISurface(const Handle(Geom_Surface)& s);

  // Get the kind of the curve
  ISurfaceKind Kind() const {
    return kind_;
  }

  // Downcast methods to specific curve types
  Handle(Geom_CylindricalSurface) AsCylindrical() const {
    return Handle(Geom_CylindricalSurface)::DownCast(surface_);
  }

  // Conversion operator to Handle(Geom_Curve)
  operator Handle(Geom_Surface)() const {
    return surface_;
  }

private:
  Handle(Geom_Surface) surface_;
  ISurfaceKind         kind_;
};

// Python bindings
void bind_ISurface(py::module& m);
