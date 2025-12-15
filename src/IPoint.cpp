#include "IPoint.hpp"

IPoint IPoint::MakeByXYZ(double x, double y, double z) {
  return IPoint(x, y, z);
}

// Python bindings
void bind_IPoint(py::module& m) {

  py::class_<IPoint>(m, "IPoint", "A point.")
    .def_static("MakeByXYZ", &IPoint::MakeByXYZ, py::arg("x"), py::arg("y"), py::arg("z"), "Make a point by its X, Y, Z coordinates.")

    .def(py::init<double, double, double>(), py::arg("x"), py::arg("y"), py::arg("z"), "Construct a point by its X, Y, Z coordinates.")

    .def("X", &IPoint::X, "Point X-location.")
    .def("Y", &IPoint::Y, "Point Y-location.")
    .def("Z", &IPoint::Z, "Point Z-location.")
    .def("Distance", &IPoint::Distance, py::arg("other"), "Compute the distance to another point.")
    .def("IsEqual", &IPoint::IsEqual, py::arg("other"), py::arg("tol") = 1.0e-7, "Check if this point is equal to the other.");

}