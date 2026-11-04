#include "ISurface.hpp"

#include <string>

#include <GC_MakeCylindricalSurface.hxx>

#include "IErrors.hpp"

static std::string kindToString(ISurfaceKind kind) {
  switch (kind) {
  case ISurfaceKind::Unknown:     return "Unknown";
  case ISurfaceKind::Plane:       return "Plane";
  case ISurfaceKind::Conical:     return "Conical";
  case ISurfaceKind::Cylindrical: return "Cylindrical";
  case ISurfaceKind::Spherical:   return "Spherical";
  case ISurfaceKind::Toroidal:    return "Toroidal";
  case ISurfaceKind::Bezier:      return "Bezier";
  case ISurfaceKind::BSpline:     return "BSpline";
  case ISurfaceKind::Trimmed:     return "Trimmed";
  default:                        return "Invalid";
  }
}

ISurface ISurface::MakeCylindrical(const IFrame& frame, const double radius) {

  Handle(Geom_CylindricalSurface) s = GC_MakeCylindricalSurface(frame, radius);

  return ISurface(s);
}

ISurface::ISurface(const Handle(Geom_Surface)& s)
  : surface_(s), kind_(ISurfaceKind::Unknown)  {

  if (s->IsKind(STANDARD_TYPE(Geom_CylindricalSurface))) {
    kind_ = ISurfaceKind::Cylindrical;
  }
}

void ISurface::ValidateKind(const ISurfaceKind expected) const {
  if (kind_ != expected) {
    throw IKindMismatch(
      "Expected " + kindToString(expected) + " but got " + kindToString(kind_) + " instead.");
  }
}

// Python bindings
void bind_ISurface(nb::module_& m) {

  nb::enum_<ISurfaceKind>(m, "ISurfaceKind", "Enumeration for surface kinds.")
    .value("Unknown", ISurfaceKind::Unknown)
    .value("Plane", ISurfaceKind::Plane)
    .value("Conical", ISurfaceKind::Conical)
    .value("Cylindrical", ISurfaceKind::Cylindrical)
    .value("Spherical", ISurfaceKind::Spherical)
    .value("Toroidal", ISurfaceKind::Toroidal)
    .value("Bezier", ISurfaceKind::Bezier)
    .value("BSpline", ISurfaceKind::BSpline)
    .value("Trimmed", ISurfaceKind::Trimmed);

  nb::class_<ISurface>(m, "ISurface", "A surface.")

    .def_static("MakeCylindrical", &ISurface::MakeCylindrical, nb::arg("frame"), nb::arg("radius"), "Make an infinite cylindrical surface given a frame and a radius.")

    .def("Kind", &ISurface::Kind, "The kind of this surface.");

}
