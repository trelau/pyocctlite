#pragma once

#include "occtlite.hpp"

#include <Geom2d_Curve.hxx>
#include <Geom2d_Line.hxx>
#include <Geom2d_Circle.hxx>
#include <Geom2d_Ellipse.hxx>
#include <Geom2d_Parabola.hxx>
#include <Geom2d_Hyperbola.hxx>
#include <Geom2d_BezierCurve.hxx>
#include <Geom2d_BSplineCurve.hxx>
#include <Geom2d_TrimmedCurve.hxx>

#include "IPoint2D.hpp"
#include "IVector2D.hpp"
#include "IFrame2D.hpp"

// Enumeration for 2D curve kinds
enum class ICurve2DKind {
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
class ICurve2D {
public:

  // Factory methods to create different types of curves
  static ICurve2D MakeLine(const IPoint2D& p1, const IPoint2D& p2);

  static ICurve2D MakeEllipse(const IFrame2D& frame, const double majorRadius, const double minorRadius);

  static ICurve2D MakeTrimmed(const ICurve2D& curve, const double u0, const double u1);

  static ICurve2D MakeTrimmed(const IPoint2D& p1, const IPoint2D& p2);

  // Constructor from Handle(Geom2d_Curve)
  explicit ICurve2D(const Handle(Geom2d_Curve)& c);

  // Get the kind of the curve
  ICurve2DKind Kind() const {
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
  IPoint2D Evaluate(double u) const;

  // Evaluate the derivative of the curve at parameter u
  IVector2D Derivative(double u, int order = 1) const;


  // Downcast methods to specific curve types
  Handle(Geom2d_Line) AsLine() const {
    return Handle(Geom2d_Line)::DownCast(curve_);
  }

  Handle(Geom2d_Circle) AsCircle() const {
    return Handle(Geom2d_Circle)::DownCast(curve_);
  }

  Handle(Geom2d_Ellipse) AsEllipse() const {
    return Handle(Geom2d_Ellipse)::DownCast(curve_);
  }

  Handle(Geom2d_Parabola) AsParabola() const {
    return Handle(Geom2d_Parabola)::DownCast(curve_);
  }

  Handle(Geom2d_Hyperbola) AsHyperbola() const {
    return Handle(Geom2d_Hyperbola)::DownCast(curve_);
  }

  Handle(Geom2d_BezierCurve) AsBezier() const {
    return Handle(Geom2d_BezierCurve)::DownCast(curve_);
  }

  Handle(Geom2d_BSplineCurve) AsBSpline() const {
    return Handle(Geom2d_BSplineCurve)::DownCast(curve_);
  }

  Handle(Geom2d_TrimmedCurve) AsTrimmed() const {
    return Handle(Geom2d_TrimmedCurve)::DownCast(curve_);
  }

  // Conversion operator to Handle(Geom2d_Curve)
  operator Handle(Geom2d_Curve)() const {
    return curve_;
  }

private:
  Handle(Geom2d_Curve) curve_;
  ICurve2DKind         kind_;
};

// Python bindings
void bind_ICurve2D(py::module& m);
