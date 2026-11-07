#include "ICurve2D.hpp"

#include <string>

#include <GCE2d_MakeCircle.hxx>
#include <GCE2d_MakeEllipse.hxx>
#include <GCE2d_MakeLine.hxx>
#include <GCE2d_MakeSegment.hxx>
#include <GCPnts_TangentialDeflection.hxx>
#include <Geom2dAdaptor_Curve.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Vec2d.hxx>

#include "IErrors.hpp"

static std::string kindToString(ICurve2DKind kind) {
  switch (kind) {
  case ICurve2DKind::Unknown:
    return "Unknown";
  case ICurve2DKind::Line:
    return "Line";
  case ICurve2DKind::Circle:
    return "Circle";
  case ICurve2DKind::Ellipse:
    return "Ellipse";
  case ICurve2DKind::Parabola:
    return "Parabola";
  case ICurve2DKind::Hyperbola:
    return "Hyperbola";
  case ICurve2DKind::Bezier:
    return "Bezier";
  case ICurve2DKind::BSpline:
    return "BSpline";
  case ICurve2DKind::Trimmed:
    return "Trimmed";
  default:
    return "Invalid";
  }
}

ICurve2D ICurve2D::MakeLine(const IPoint2D& p1, const IPoint2D& p2) {

  Handle(Geom2d_Line) c = GCE2d_MakeLine(p1, p2);

  return ICurve2D(c);
}

std::vector<IPoint2D> ICurve2D::SamplePoints(const double deflection,
                                             const double angularDeflection) const {

  const Geom2dAdaptor_Curve curve(curve_);
  const GCPnts_TangentialDeflection sampled(curve, angularDeflection, deflection);
  std::vector<IPoint2D> points;
  for (int i = 1; i <= sampled.NbPoints(); ++i) {
    const gp_Pnt point = sampled.Value(i);
    points.emplace_back(gp_Pnt2d(point.X(), point.Y()));
  }
  return points;
}

ICurve2D ICurve2D::MakeCircle(const IFrame2D& frame, const double radius) {

  Handle(Geom2d_Circle) c = GCE2d_MakeCircle(static_cast<gp_Ax22d>(frame), radius);

  return ICurve2D(c);
}

ICurve2D ICurve2D::MakeEllipse(const IFrame2D& frame, const double majorRadius,
                               const double minorRadius) {

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

ICurve2D::ICurve2D(const Handle(Geom2d_Curve) & c) : curve_(c), kind_(ICurve2DKind::Unknown) {

  if (c->IsKind(STANDARD_TYPE(Geom2d_Line))) {
    kind_ = ICurve2DKind::Line;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_Circle))) {
    kind_ = ICurve2DKind::Circle;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_Ellipse))) {
    kind_ = ICurve2DKind::Ellipse;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_Parabola))) {
    kind_ = ICurve2DKind::Parabola;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_Hyperbola))) {
    kind_ = ICurve2DKind::Hyperbola;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_BezierCurve))) {
    kind_ = ICurve2DKind::Bezier;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_BSplineCurve))) {
    kind_ = ICurve2DKind::BSpline;
  } else if (c->IsKind(STANDARD_TYPE(Geom2d_TrimmedCurve))) {
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

ILine2DData ICurve2D::LineData() const {

  Handle(Geom2d_Line) line = AsLine();

  return {IPoint2D(line->Position().Location()), IVector2D(line->Position().Direction())};
}

ICircle2DData ICurve2D::CircleData() const {

  Handle(Geom2d_Circle) circle = AsCircle();

  return {IFrame2D(circle->Position()), circle->Radius()};
}

IEllipse2DData ICurve2D::EllipseData() const {

  Handle(Geom2d_Ellipse) ellipse = AsEllipse();

  return {IFrame2D(ellipse->Position()), ellipse->MajorRadius(), ellipse->MinorRadius()};
}

void ICurve2D::ValidateKind(const ICurve2DKind expected) const {
  if (kind_ != expected) {
    throw IKindMismatch("Expected " + kindToString(expected) + " but got " + kindToString(kind_) +
                        " instead.");
  }
}

// Python bindings
void bind_ICurve2D(nb::module_& m) {

  nb::enum_<ICurve2DKind>(m, "ICurve2DKind", "Enumeration for 2D curve kinds.")
      .value("Unknown", ICurve2DKind::Unknown)
      .value("Line", ICurve2DKind::Line)
      .value("Circle", ICurve2DKind::Circle)
      .value("Ellipse", ICurve2DKind::Ellipse)
      .value("Hyperbola", ICurve2DKind::Hyperbola)
      .value("Parabola", ICurve2DKind::Parabola)
      .value("Bezier", ICurve2DKind::Bezier)
      .value("BSpline", ICurve2DKind::BSpline)
      .value("Trimmed", ICurve2DKind::Trimmed);

  nb::class_<ICurve2D>(m, "ICurve2D", "A 2D curve.")

      .def_static("MakeLine", &ICurve2D::MakeLine, nb::arg("p1"), nb::arg("p2"), "Make a line.")
      .def("SamplePoints", &ICurve2D::SamplePoints, nb::arg("deflection"),
           nb::arg("angularDeflection") = 0.2,
           "Get points along this curve within a deflection and an angle in radians.")
      .def_static("MakeCircle", &ICurve2D::MakeCircle, nb::arg("frame"), nb::arg("radius"),
                  "Make a circle.")
      .def_static("MakeEllipse", &ICurve2D::MakeEllipse, nb::arg("frame"), nb::arg("rmajor"),
                  nb::arg("rminor"), "Make an ellipse.")
      .def_static(
          "MakeTrimmed",
          nb::overload_cast<const ICurve2D&, const double, const double>(&ICurve2D::MakeTrimmed),
          nb::arg("curve"), nb::arg("u0"), nb::arg("u1"), "Make a trimmed curve.")
      .def_static("MakeTrimmed",
                  nb::overload_cast<const IPoint2D&, const IPoint2D&>(&ICurve2D::MakeTrimmed),
                  nb::arg("p1"), nb::arg("p2"), "Make a trimmed curve from two points.")

      .def("Kind", &ICurve2D::Kind, "The kind of this curve.")
      .def("IsClosed", &ICurve2D::IsClosed, "Whether or not this curve is closed.")
      .def("IsPeriodic", &ICurve2D::IsPeriodic, "Whether or not this curve is periodic.")
      .def("FirstParameter", &ICurve2D::FirstParameter, "The first parameter of this curve.")
      .def("LastParameter", &ICurve2D::LastParameter, "The last parameter of this curve.")
      .def("Evaluate", &ICurve2D::Evaluate, nb::arg("u"), "Evaluate a point on this curve.")
      .def("Derivative", &ICurve2D::Derivative, nb::arg("u"), nb::arg("order") = 1,
           "Evaluate a derivative on this curve.")

      .def("LineData", &ICurve2D::LineData, "Get line data.")
      .def("CircleData", &ICurve2D::CircleData, "Get circle data.")
      .def("EllipseData", &ICurve2D::EllipseData, "Get ellipse data.");
}
