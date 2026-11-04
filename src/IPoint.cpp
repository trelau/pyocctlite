#include "IPoint.hpp"

IPoint IPoint::MakeByXYZ(double x, double y, double z) {
  return IPoint(gp_Pnt(x, y, z));
}

// Python bindings
void bind_IPoint(nb::module_& m) {

  nb::class_<IPoint>(m, "IPoint", "A point.")
      .def_static("MakeByXYZ", &IPoint::MakeByXYZ, nb::arg("x"), nb::arg("y"), nb::arg("z"),
                  "Make a point by its X, Y, Z coordinates.")

      .def("X", &IPoint::X, "Point X-location.")
      .def("Y", &IPoint::Y, "Point Y-location.")
      .def("Z", &IPoint::Z, "Point Z-location.")
      .def("Distance", &IPoint::Distance, nb::arg("other"),
           "Compute the distance to another point.")
      .def("IsEqual", &IPoint::IsEqual, nb::arg("other"), nb::arg("tol") = 1.0e-7,
           "Check if this point is equal to the other.");
}