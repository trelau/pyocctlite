#include "ICurve2D.hpp"

#include <gp_Pnt2d.hxx>
#include <gp_Vec2d.hxx>
#include <GCE2d_MakeLine.hxx>
#include <GCE2d_MakeSegment.hxx>
#include <GCE2d_MakeEllipse.hxx>

ICurve2D ICurve2D::MakeLine(const IPoint2D& p1, const IPoint2D& p2) {

  Handle(Geom2d_Line) c = GCE2d_MakeLine(p1, p2);

  return ICurve2D(c);
}

ICurve2D ICurve2D::MakeEllipse(const IFrame2D& frame, const double majorRadius, const double minorRadius) {

  Handle(Geom2d_Ellipse) c = GCE2d_MakeEllipse(frame, majorRadius, minorRadius);

  return ICurve2D(c);
}

ICurve2D ICurve2D::MakeTrimmed(const ICurve2D& curve, const double u0, const double u1) {

  Handle(Geom2d_TrimmedCurve) c = new Geom2d_TrimmedCurve(curve, u0, u1);

  return ICurve2D(c);
}

ICurve2D ICurve2D::MakeTrimmed(const IPoint2D& p1, const IPoint2D& p2) {

  Handle(Geom2d_TrimmedCurve) c = GCE2d_MakeSegment(p1, p2);

  return ICurve2D(c);
}

ICurve2D::ICurve2D(const Handle(Geom2d_Curve)& c)
  : curve_(c), kind_(ICurve2DKind::Unknown) {

  if (c->IsKind(STANDARD_TYPE(Geom2d_Line))) {
    kind_ = ICurve2DKind::Line;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_Circle))) {
    kind_ = ICurve2DKind::Circle;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_Ellipse))) {
    kind_ = ICurve2DKind::Ellipse;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_Parabola))) {
    kind_ = ICurve2DKind::Parabola;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_Hyperbola))) {
    kind_ = ICurve2DKind::Hyperbola;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_BezierCurve))) {
    kind_ = ICurve2DKind::Bezier;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_BSplineCurve))) {
    kind_ = ICurve2DKind::BSpline;
  }
  else if (c->IsKind(STANDARD_TYPE(Geom2d_TrimmedCurve))) {
    kind_ = ICurve2DKind::Trimmed;
  }
}

IPoint2D ICurve2D::Evaluate(double u) const {

  gp_Pnt2d p = curve_->Value(u);

  return IPoint2D(p);
}

IVector2D ICurve2D::Derivative(double u, int order) const {

  gp_Vec2d v = curve_->DN(u, order);

  return IVector2D(v);
}

// Python bindings
void bind_ICurve2D(py::module& m) {

  py::enum_<ICurve2DKind>(m, "ICurve2DKind", "Enumeration for 2D curve kinds.")
    .value("Unknown", ICurve2DKind::Unknown)
    .value("Line", ICurve2DKind::Line)
    .value("Circle", ICurve2DKind::Circle)
    .value("Ellipse", ICurve2DKind::Ellipse)
    .value("Hyperbola", ICurve2DKind::Hyperbola)
    .value("Parabola", ICurve2DKind::Parabola)
    .value("Bezier", ICurve2DKind::Bezier)
    .value("BSpline", ICurve2DKind::BSpline)
    .value("Trimmed", ICurve2DKind::Trimmed);

  py::class_<ICurve2D>(m, "ICurve2D", "A 2D curve.")

    .def_static("MakeLine", &ICurve2D::MakeLine, py::arg("p1"), py::arg("p2"), "Make a line.")
    .def_static("MakeEllipse", &ICurve2D::MakeEllipse, py::arg("frame"), py::arg("rmajor"), py::arg("rminor"), "Make an ellipse.")
    .def_static("MakeTrimmed", py::overload_cast<const ICurve2D&, const double, const double>(&ICurve2D::MakeTrimmed), py::arg("curve"), py::arg("u0"), py::arg("u1"), "Make a trimmed curve.")
    .def_static("MakeTrimmed", py::overload_cast<const IPoint2D&, const IPoint2D&>(&ICurve2D::MakeTrimmed), py::arg("p1"), py::arg("p2"), "Make a trimmed curve from two points.")

    .def("Kind", &ICurve2D::Kind, "The kind of this curve.")
    .def("IsClosed", &ICurve2D::IsClosed, "Whether or not this curve is closed.")
    .def("IsPeriodic", &ICurve2D::IsPeriodic, "Whether or not this curve is periodic.")
    .def("FirstParameter", &ICurve2D::FirstParameter, "The first parameter of this curve.")
    .def("LastParameter", &ICurve2D::LastParameter, "The last parameter of this curve.")
    .def("Evaluate", &ICurve2D::Evaluate, py::arg("u"), "Evaluate a point on this curve.")
    .def("Derivative", &ICurve2D::Derivative, py::arg("u"), py::arg("order") = 1, "Evaluate a derivative on this curve.");

}
