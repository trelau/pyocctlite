#include "ISurface.hpp"

#include <GC_MakeCylindricalSurface.hxx>

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

// Python bindings
void bind_ISurface(nb::module_& m) {

  nb::enum_<ISurfaceKind>(m, "ISurfaceKind", "Enumeration for surface kinds.")
    .value("Unknown", ISurfaceKind::Unknown)
    .value("Plane", ISurfaceKind::Plane)
    .value("Cylindrical", ISurfaceKind::Cylindrical)
    .value("Bezier", ISurfaceKind::Bezier)
    .value("BSpline", ISurfaceKind::BSpline)
    .value("Trimmed", ISurfaceKind::Trimmed);

  nb::class_<ISurface>(m, "ISurface", "A surface.")

    .def_static("MakeCylindrical", &ISurface::MakeCylindrical, nb::arg("frame"), nb::arg("radius"), "Make an infinite cylindrical surface given a frame and a radius.")

    .def("Kind", &ISurface::Kind, "The kind of this surface.");

}
