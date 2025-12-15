#include "IVector.hpp"

IVector IVector::MakeByXYZ(double x, double y, double z) {
  return IVector(x, y, z);
}

// Python bindings
void bind_IVector(py::module& m) {

  py::class_<IVector>(m, "IVector", "A vector.")
    .def_static("MakeByXYZ", &IVector::MakeByXYZ, py::arg("x"), py::arg("y"), py::arg("z"), "Make a vector by its X, Y, Z components.")

    .def(py::init<double, double, double>(), py::arg("x"), py::arg("y"), py::arg("z"), "Construct a vector by its X, Y, Z components.")

    .def("X", &IVector::X, "Vector X-component.")
    .def("Y", &IVector::Y, "Vector Y-component.")
    .def("Z", &IVector::Z, "Vector Z-component.")
    .def("Scaled", &IVector::Scaled, py::arg("scale"), "Return a scaled copy of this vector.");

}