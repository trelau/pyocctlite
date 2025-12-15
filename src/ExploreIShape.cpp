#include "ExploreIShape.hpp"

// Python bindings
void bind_ExploreIShape(py::module& m) {

  auto cls = py::class_<ExploreIShape>(m, "ExploreIShape", "Explore a shape.")
    .def(py::init<const IShape&, const IShapeKind, const IShapeKind>(), py::arg("shape"), py::arg("find"), py::arg("ignore") = IShapeKind::Shape, "Constructor to explore a shape.")

    .def("More", &ExploreIShape::More, "Check if there are more shapes to explore.")
    .def("Next", &ExploreIShape::Next, "Move to the next shape.")
    .def("Current", &ExploreIShape::Current, "Get the current shape.");

}