#include "ICurveData.hpp"

void bind_ICurveData(nb::module_& m) {

  nb::class_<ILineData>(m, "ILineData", "Line data.")
      .def_ro("Origin", &ILineData::Origin)
      .def_ro("Direction", &ILineData::Direction);

  nb::class_<ICircleData>(m, "ICircleData", "Circle data.")
      .def_ro("Frame", &ICircleData::Frame)
      .def_ro("Radius", &ICircleData::Radius);

  nb::class_<IEllipseData>(m, "IEllipseData", "Ellipse data.")
      .def_ro("Frame", &IEllipseData::Frame)
      .def_ro("MajorRadius", &IEllipseData::MajorRadius)
      .def_ro("MinorRadius", &IEllipseData::MinorRadius);

  nb::class_<ILine2DData>(m, "ILine2DData", "2D line data.")
      .def_ro("Origin", &ILine2DData::Origin)
      .def_ro("Direction", &ILine2DData::Direction);

  nb::class_<ICircle2DData>(m, "ICircle2DData", "2D circle data.")
      .def_ro("Frame", &ICircle2DData::Frame)
      .def_ro("Radius", &ICircle2DData::Radius);

  nb::class_<IEllipse2DData>(m, "IEllipse2DData", "2D ellipse data.")
      .def_ro("Frame", &IEllipse2DData::Frame)
      .def_ro("MajorRadius", &IEllipse2DData::MajorRadius)
      .def_ro("MinorRadius", &IEllipse2DData::MinorRadius);
}
