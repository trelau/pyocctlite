#include "ICurveData.hpp"

void bind_ICurveData(nb::module_& m) {

  nb::class_<ILineData>(m, "ILineData", "Line data.")
    .def_ro("Origin", &ILineData::Origin)
    .def_ro("Direction", &ILineData::Direction);

  nb::class_<ICircleData>(m, "ICircleData", "Circle data.")
    .def_ro("Frame", &ICircleData::Frame)
    .def_ro("Radius", &ICircleData::Radius);
}
