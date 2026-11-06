#include "IVector.hpp"

#include "IPoint.hpp"

IVector IVector::MakeByXYZ(double x, double y, double z) { return IVector(gp_Vec(x, y, z)); }

IVector IVector::MakeByPoints(const IPoint& p1, const IPoint& p2) {
  return IVector(gp_Vec(p1, p2));
}

// Python bindings
void bind_IVector(nb::module_& m) {

  nb::class_<IVector>(m, "IVector", "A vector.")
      .def_static("MakeByXYZ", &IVector::MakeByXYZ, nb::arg("x"), nb::arg("y"), nb::arg("z"),
                  "Make a vector by its X, Y, Z components.")

      .def_static("MakeByPoints", &IVector::MakeByPoints, nb::arg("p1"), nb::arg("p2"),
                  "Make a vector from one point to another.")

      .def("X", &IVector::X, "Vector X-component.")
      .def("Y", &IVector::Y, "Vector Y-component.")
      .def("Z", &IVector::Z, "Vector Z-component.")
      .def("Magnitude", &IVector::Magnitude, "Get the magnitude of the vector.")
      .def("Scaled", &IVector::Scaled, nb::arg("scale"), "Return a scaled copy of this vector.")
      .def("Added", &IVector::Added, nb::arg("other"), "Return the sum with another vector.")
      .def("Subtracted", &IVector::Subtracted, nb::arg("other"),
           "Return the difference with another vector.")
      .def("Reversed", &IVector::Reversed, "Return a copy pointing the opposite way.")
      .def("Normalized", &IVector::Normalized, "Return a unit-length copy of this vector.")
      .def("Dot", &IVector::Dot, nb::arg("other"), "Compute the dot product with another vector.")
      .def("Cross", &IVector::Cross, nb::arg("other"),
           "Return the cross product with another vector.")
      .def("IsEqual", &IVector::IsEqual, nb::arg("other"), nb::arg("tol") = 1.0e-7,
           nb::arg("angular_tol") = 1.0e-12,
           "Check if the magnitudes and directions match within tolerances.");
}