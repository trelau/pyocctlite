#include "ProjectIPointToICurve.hpp"

// Python bindings
void bind_ProjectIPointToICurve(py::module& m) {

  py::class_<ProjectIPointToICurve>(m, "ProjectIPointToICurve", "Project a point to a curve.")
    .def(py::init<const IPoint&, const ICurve&>(), py::arg("p"), py::arg("c"), "Project the point to the curve.")
    .def(py::init<const IPoint&, const ICurve&, double, double>(), py::arg("pnt"), py::arg("c"), py::arg("umin"), py::arg("umax"), "Project the point to the curve between parameters.")

    .def("IsDone", &ProjectIPointToICurve::IsDone, "Check if projection has results.")
    .def("NumPoints", &ProjectIPointToICurve::NumPoints, "Number of projection results.")
    .def("NearestPoint", &ProjectIPointToICurve::NearestPoint)
    .def("NearestDistance", &ProjectIPointToICurve::NearestDistance)
    .def("NearestParameter", &ProjectIPointToICurve::NearestParameter)

    .def("Perform", &ProjectIPointToICurve::Perform, py::arg("p"), "Perform the projection of a point to the curve.")
    .def("Point", &ProjectIPointToICurve::Point, py::arg("idx"), "Get the projected point at this index.")
    .def("Parameter", &ProjectIPointToICurve::Parameter, py::arg("idx"), "Get the parameter on the curve at this index.")
    .def("Distance", &ProjectIPointToICurve::Distance, py::arg("idx"), "Get the distance at this index.");

}
