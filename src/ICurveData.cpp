#include "ICurveData.hpp"

void bind_ICurveData(py::module& m) {

  py::class_<ILineData>(m, "ILineData", "Line data.")
    .def_readonly("Origin", &ILineData::Origin)
    .def_readonly("Direction", &ILineData::Direction);

  py::class_<ICircleData>(m, "ICircleData", "Circle data.")
    .def_readonly("Frame", &ICircleData::Frame)
    .def_readonly("Radius", &ICircleData::Radius);
}
