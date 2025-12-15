#include "IVector2D.hpp"

IVector2D IVector2D::makeByXY(double x, double y) {
  return IVector2D(x, y);
}

// Python bindings
void bind_IVector2D(py::module& m) {

  py::class_<IVector2D>(m, "IVector2D", "A 2D vector.")
    .def_static("NakeByXY", &IVector2D::makeByXY, py::arg("x"), py::arg("y"), "Make a vector by its X, Y components.")

    .def(py::init<double, double>(), py::arg("x"), py::arg("y"), "Construct a vector by its X, Y components.")

    .def("X", &IVector2D::X, "Vector X-component.")
    .def("Y", &IVector2D::Y, "Vector Y-component.")
    .def("Scaled", &IVector2D::Scaled, py::arg("scale"), "Return a scaled copy of this vector.");

}