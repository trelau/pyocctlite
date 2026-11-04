#include "IVector.hpp"

IVector IVector::MakeByXYZ(double x, double y, double z) {
  return IVector(gp_Vec(x, y, z));
}

// Python bindings
void bind_IVector(nb::module_& m) {

  nb::class_<IVector>(m, "IVector", "A vector.")
    .def_static("MakeByXYZ", &IVector::MakeByXYZ, nb::arg("x"), nb::arg("y"), nb::arg("z"), "Make a vector by its X, Y, Z components.")

    .def("X", &IVector::X, "Vector X-component.")
    .def("Y", &IVector::Y, "Vector Y-component.")
    .def("Z", &IVector::Z, "Vector Z-component.")
    .def("Magnitude", &IVector::Magnitude, "Get the magnitude of the vector.")
    .def("Scaled", &IVector::Scaled, nb::arg("scale"), "Return a scaled copy of this vector.");

}