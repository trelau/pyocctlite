#include "ProjectIPointToICurve.hpp"

// Python bindings
void bind_ProjectIPointToICurve(nb::module_& m) {

  nb::class_<ProjectIPointToICurve>(m, "ProjectIPointToICurve", "Project a point to a curve.")
      .def(nb::init<const IPoint&, const ICurve&>(), nb::arg("p"), nb::arg("c"),
           "Project the point to the curve.")
      .def(nb::init<const IPoint&, const ICurve&, double, double>(), nb::arg("pnt"), nb::arg("c"),
           nb::arg("umin"), nb::arg("umax"), "Project the point to the curve between parameters.")

      .def("IsDone", &ProjectIPointToICurve::IsDone, "Check if projection has results.")
      .def("NumPoints", &ProjectIPointToICurve::NumPoints, "Number of projection results.")
      .def("NearestPoint", &ProjectIPointToICurve::NearestPoint)
      .def("NearestDistance", &ProjectIPointToICurve::NearestDistance)
      .def("NearestParameter", &ProjectIPointToICurve::NearestParameter)

      .def("Perform", &ProjectIPointToICurve::Perform, nb::arg("p"),
           "Perform the projection of a point to the curve.")
      .def("Point", &ProjectIPointToICurve::Point, nb::arg("idx"),
           "Get the projected point at this index.")
      .def("Parameter", &ProjectIPointToICurve::Parameter, nb::arg("idx"),
           "Get the parameter on the curve at this index.")
      .def("Distance", &ProjectIPointToICurve::Distance, nb::arg("idx"),
           "Get the distance at this index.");
}
