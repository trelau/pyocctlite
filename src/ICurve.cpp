#include "ICurve.hpp"

#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>
#include <GC_MakeCircle.hxx>
#include <GC_MakeArcOfCircle.hxx>
#include <GC_MakeLine.hxx>

ICurve ICurve::MakeLine(const IPoint& p1, const IPoint& p2) {

  Handle(Geom_Line) line = GC_MakeLine(p1, p2);

  return ICurve(line);
}

ICurve ICurve::MakeCircle(const IFrame& frame, const double radius) {

  Handle(Geom_Circle) c = GC_MakeCircle(frame, radius);

  return ICurve(c);
}

ICurve ICurve::MakeCircle(const IPoint& p1, const IPoint& p2, const IPoint& p3) {

  Handle(Geom_Circle) c = GC_MakeCircle(p1, p2, p3);

  return ICurve(c);
}

ICurve ICurve::MakeCircularArc(const IPoint& p1, const IPoint& p2, const IPoint& p3) {

  Handle(Geom_TrimmedCurve) arc = GC_MakeArcOfCircle(p1, p2, p3);

  return ICurve(arc);
}

ICurve::ICurve(const Handle(Geom_Curve)& c)
  : curve_(c), kind_(ICurveKind::Unknown) {

  if (c->IsKind(STANDARD_TYPE(Geom_Line))) {
    kind_ = ICurveKind::Line;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_Circle))) {
    kind_ = ICurveKind::Circle;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_Ellipse))) {
    kind_ = ICurveKind::Ellipse;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_Parabola))) {
    kind_ = ICurveKind::Parabola;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_Hyperbola))) {
    kind_ = ICurveKind::Hyperbola;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_BezierCurve))) {
    kind_ = ICurveKind::Bezier;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_BSplineCurve))) {
    kind_ = ICurveKind::BSpline;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom_TrimmedCurve))) {
    kind_ = ICurveKind::Trimmed;
  }
}

IPoint ICurve::Evaluate(double u) const {

  gp_Pnt p = curve_->Value(u);

  return IPoint(p);
}

IVector ICurve::Derivative(double u, int order) const {

  gp_Vec v = curve_->DN(u, order);

  return IVector(v);
}

std::optional<ILineData> ICurve::LineData() const {
  if (kind_ != ICurveKind::Line) {
    return std::nullopt;
  }
  Handle(Geom_Line) line = AsLine();
  IPoint origin(line->Position().Location());
  IVector direction(line->Position().Direction());
  ILineData data{origin, direction};
  return data;
}

std::optional<ICircleData> ICurve::CircleData() const {

  if (kind_ != ICurveKind::Circle) {
    return std::nullopt;
  }
  Handle(Geom_Circle) circle = AsCircle();
  IFrame frame(circle->Position());
  double radius = circle->Radius();
  ICircleData data{frame, radius};
  return data;
}

// Python bindings
void bind_ICurve(py::module& m) {

  py::enum_<ICurveKind>(m, "ICurveKind", "Enumeration for curve kinds.")
    .value("Unknown", ICurveKind::Unknown)
    .value("Line", ICurveKind::Line)
    .value("Circle", ICurveKind::Circle)
    .value("Ellipse", ICurveKind::Ellipse)
    .value("Hyperbola", ICurveKind::Hyperbola)
    .value("Parabola", ICurveKind::Parabola)
    .value("Bezier", ICurveKind::Bezier)
    .value("BSpline", ICurveKind::BSpline)
    .value("Trimmed", ICurveKind::Trimmed);

  py::class_<ICurve>(m, "ICurve", "A curve.")
    .def_static("MakeLine", &ICurve::MakeLine, py::arg("p1"), py::arg("p2"), "Make a line by two points.")
    .def_static("MakeCircle", py::overload_cast<const IFrame&, const double>(&ICurve::MakeCircle), py::arg("frame"), py::arg("radius"), "Make a circle by frame and radius.")
    .def_static("MakeCircle", py::overload_cast<const IPoint&, const IPoint&, const IPoint&>(&ICurve::MakeCircle), py::arg("p1"), py::arg("p2"), py::arg("p3"), "Make a circle by three points.")
    .def_static("MakeCircularArc", &ICurve::MakeCircularArc, py::arg("p1"), py::arg("p2"), py::arg("p3"), "Make a circular arc by three points.")

    .def("Kind", &ICurve::Kind, "The kind of this curve.")
    .def("IsClosed", &ICurve::IsClosed, "Whether or not this curve is closed.")
    .def("IsPeriodic", &ICurve::IsPeriodic, "Whether or not this curve is periodic.")
    .def("FirstParameter", &ICurve::FirstParameter, "The first parameter of this curve.")
    .def("LastParameter", &ICurve::LastParameter, "The last parameter of this curve.")
    .def("Evaluate", &ICurve::Evaluate, py::arg("u"), "Evaluate a point on this curve.")
    .def("Derivative", &ICurve::Derivative, py::arg("u"), py::arg("order") = 1, "Evaluate a derivative on this curve.")

    .def("LineData", &ICurve::LineData, "Get line data if this curve is a line.")
    .def("CircleData", &ICurve::CircleData, "Get circle data if this curve is a circle.");

}
