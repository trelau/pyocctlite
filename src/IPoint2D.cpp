#include "IPoint2D.hpp"

IPoint2D IPoint2D::MakeByXY(double x, double y) {
  return IPoint2D(x, y);
}

// Python bindings
void bind_IPoint2D(py::module& m) {

  py::class_<IPoint2D>(m, "IPoint2D", "A 2D point.")
    .def_static("MakeByXY", &IPoint2D::MakeByXY, py::arg("x"), py::arg("y"), "Make a 2D point by its X, Y coordinates.")

    .def(py::init<double, double>(), py::arg("x"), py::arg("y"), "Construct a point by its X, Y coordinates.")

    .def("X", &IPoint2D::X, "Point X-location.")
    .def("Y", &IPoint2D::Y, "Point Y-location.")
    .def("Distance", &IPoint2D::Distance, py::arg("other"), "Compute the distance to another point.")
    .def("IsEqual", &IPoint2D::IsEqual, py::arg("other"), py::arg("tol") = 1.0e-7, "Check if this point is equal to the other.");

}