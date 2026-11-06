#include "IAxis.hpp"

#include <gp_Dir.hxx>

IAxis IAxis::MakeByVector(const IPoint& origin, const IVector& direction) {

  gp_Dir d(direction);

  return IAxis(gp_Ax1(origin, d));
}

// Python bindings
void bind_IAxis(nb::module_& m) {

  nb::class_<IAxis>(m, "IAxis", "An axis.")
      .def_static("MakeByVector", &IAxis::MakeByVector, nb::arg("origin"), nb::arg("direction"),
                  "Make an axis from an origin point and a direction vector.")
      .def("Origin", &IAxis::Origin, "Get the origin point of the axis.")
      .def("Direction", &IAxis::Direction, "Get the direction vector of the axis.");
}
