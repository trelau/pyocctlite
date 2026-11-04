#include "IPoint2D.hpp"

IPoint2D IPoint2D::MakeByXY(double x, double y) { return IPoint2D(gp_Pnt2d(x, y)); }

// Python bindings
void bind_IPoint2D(nb::module_& m) {

  nb::class_<IPoint2D>(m, "IPoint2D", "A 2D point.")
      .def_static("MakeByXY", &IPoint2D::MakeByXY, nb::arg("x"), nb::arg("y"),
                  "Make a 2D point by its X, Y coordinates.")

      .def("X", &IPoint2D::X, "Point X-location.")
      .def("Y", &IPoint2D::Y, "Point Y-location.")
      .def("Distance", &IPoint2D::Distance, nb::arg("other"),
           "Compute the distance to another point.")
      .def("IsEqual", &IPoint2D::IsEqual, nb::arg("other"), nb::arg("tol") = 1.0e-7,
           "Check if this point is equal to the other.");
}