#pragma once

#include "occtlite.hpp"

#include <Geom_Curve.hxx>
#include <Geom_Line.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <Geom_Parabola.hxx>
#include <Geom_Hyperbola.hxx>
#include <Geom_BezierCurve.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_TrimmedCurve.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"
#include "IFrame.hpp"

// Enumeration for curve kinds
enum class ICurveKind {
  Unknown = 0,
  Line,
  Circle,
  Ellipse,
  Parabola,
  Hyperbola,
  Bezier,
  BSpline,
  Trimmed
};

// Interface class for a curve
class ICurve {
public:

  // Factory methods to create different types of curves
  static ICurve MakeLine(const IPoint& p1, const IPoint& p2);

  static ICurve MakeCircle(const IFrame& frame, const double radius);

  static ICurve MakeCircle(const IPoint& p1, const IPoint& p2, const IPoint& p3);

  static ICurve MakeCircularArc(const IPoint& p1, const IPoint& p2, const IPoint& p3);

  // Constructor from Handle(Geom_Curve)
  explicit ICurve(const Handle(Geom_Curve)& c);

  // Get the kind of the curve
  ICurveKind Kind() const {
    return kind_;
  }
  // Check if the curve is closed
  bool IsClosed() const {
    return curve_->IsClosed();
  }

  // Check if the curve is periodic
  bool IsPeriodic() const {
    return curve_->IsPeriodic();
  }
  // Get the first parameter of the curve
  double FirstParameter() const {
    return curve_->FirstParameter();
  }
  // Get the last parameter of the curve
  double LastParameter() const {
    return curve_->LastParameter();
  }

  // Evaluate the point on the curve at parameter u
  IPoint Evaluate(double u) const;

  // Evaluate the derivative of the curve at parameter u
  IVector Derivative(double u, int order = 1) const;


  // Downcast methods to specific curve types
  Handle(Geom_Line) AsLine() const {
    return Handle(Geom_Line)::DownCast(curve_);
  }

  Handle(Geom_Circle) AsCircle() const {
    return Handle(Geom_Circle)::DownCast(curve_);
  }

  Handle(Geom_Ellipse) AsEllipse() const {
    return Handle(Geom_Ellipse)::DownCast(curve_);
  }

  Handle(Geom_Parabola) AsParabola() const {
    return Handle(Geom_Parabola)::DownCast(curve_);
  }

  Handle(Geom_Hyperbola) AsHyperbola() const {
    return Handle(Geom_Hyperbola)::DownCast(curve_);
  }

  Handle(Geom_BezierCurve) AsBezier() const {
    return Handle(Geom_BezierCurve)::DownCast(curve_);
  }

  Handle(Geom_BSplineCurve) AsBSpline() const {
    return Handle(Geom_BSplineCurve)::DownCast(curve_);
  }

  Handle(Geom_TrimmedCurve) AsTrimmed() const {
    return Handle(Geom_TrimmedCurve)::DownCast(curve_);
  }

  // Conversion operator to Handle(Geom_Curve)
  operator Handle(Geom_Curve)() const {
    return curve_;
  }

private:
  Handle(Geom_Curve) curve_;
  ICurveKind         kind_;
};

// Python bindings
void bind_ICurve(py::module& m);
