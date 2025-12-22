#include "ICurveData.hpp"

void bind_ICurveData(py::module& m) {
  py::class_<ICircleData>(m, "ICircleData", "Circle data.")
    .def_readonly("frame", &ICircleData::frame)
    .def_readonly("radius", &ICircleData::radius);
}
