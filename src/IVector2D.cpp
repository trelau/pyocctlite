#include "IVector2D.hpp"

#include "IPoint2D.hpp"

IVector2D IVector2D::MakeByXY(double x, double y) { return IVector2D(gp_Vec2d(x, y)); }

IVector2D IVector2D::MakeByPoints(const IPoint2D& p1, const IPoint2D& p2) {
  return IVector2D(gp_Vec2d(p1, p2));
}

// Python bindings
void bind_IVector2D(nb::module_& m) {

  nb::class_<IVector2D>(m, "IVector2D", "A 2D vector.")
      .def_static("MakeByXY", &IVector2D::MakeByXY, nb::arg("x"), nb::arg("y"),
                  "Make a vector by its X, Y components.")

      .def_static("MakeByPoints", &IVector2D::MakeByPoints, nb::arg("p1"), nb::arg("p2"),
                  "Make a vector from one point to another.")

      .def("X", &IVector2D::X, "Vector X-component.")
      .def("Y", &IVector2D::Y, "Vector Y-component.")
      .def("Magnitude", &IVector2D::Magnitude, "Get the magnitude of the vector.")
      .def("Scaled", &IVector2D::Scaled, nb::arg("scale"), "Return a scaled copy of this vector.")
      .def("Added", &IVector2D::Added, nb::arg("other"), "Return the sum with another vector.")
      .def("Subtracted", &IVector2D::Subtracted, nb::arg("other"),
           "Return the difference with another vector.")
      .def("Reversed", &IVector2D::Reversed, "Return a copy pointing the opposite way.")
      .def("Normalized", &IVector2D::Normalized, "Return a unit-length copy of this vector.")
      .def("Dot", &IVector2D::Dot, nb::arg("other"), "Compute the dot product with another vector.")
      .def("Cross", &IVector2D::Cross, nb::arg("other"),
           "Compute the scalar cross product with another vector.")
      .def("IsEqual", &IVector2D::IsEqual, nb::arg("other"), nb::arg("tol") = 1.0e-7,
           nb::arg("angular_tol") = 1.0e-12,
           "Check if the magnitudes and directions match within tolerances.");
}