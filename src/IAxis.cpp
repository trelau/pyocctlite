#include "IAxis.hpp"

// Python bindings
void bind_IAxis(py::module& m) {

  py::class_<IAxis>(m, "IAxis", "An axis.")
    .def("Origin", &IAxis::Origin, "Get the origin point of the axis.")
    .def("Direction", &IAxis::Direction, "Get the direction vector of the axis.");

}