#pragma once

#include "occtlite.hpp"

#include <Standard_Integer.hxx>
#include <GeomAPI_ProjectPointOnCurve.hxx>

#include "IPoint.hpp"
#include "ICurve.hpp"

// Tool to project a point onto a curve
class ProjectIPointToICurve {
public:

  // Constructor to project a point onto a curve
  ProjectIPointToICurve(const IPoint& p, const ICurve& c) : tool_(p, c) {};

  // Constructor to project a point onto a curve between parameters
  ProjectIPointToICurve(const IPoint& p, const ICurve& c, double u0, double u1) : tool_(p, c, u0, u1) {};

  // Perform the projection of a point onto the curve
  void Perform(const IPoint& p) {
    tool_.Perform(p);
  }

  // Check if the projection has results
  bool IsDone() const {
    return tool_.NbPoints() > 0;
  }

  // Get the number of projection results
  int NumPoints() const {
    return tool_.NbPoints();
  }

  // Get the projected point at the given index
  IPoint Point(int idx) const {
    return IPoint(tool_.Point(idx));
  }

  // Get the parameter on the curve at the given index
  double Parameter(int idx) const {
    return tool_.Parameter(idx);
  }
  // Get the distance at the given index
  double Distance(int idx) const {
    return tool_.Distance(idx);
  }
  // Get the nearest projected point
  IPoint NearestPoint() const {
    return IPoint(tool_.NearestPoint());
  }
  // Get the parameter of the nearest projected point
  double NearestParameter() const {
    return tool_.LowerDistanceParameter();
  }
  // Get the distance to the nearest projected point
  double NearestDistance() const {
    return tool_.LowerDistance();
  }

private:
  GeomAPI_ProjectPointOnCurve tool_;

};

// Python bindings
void bind_ProjectIPointToICurve(py::module& m);
