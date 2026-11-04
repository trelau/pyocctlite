#include "ExploreIShape.hpp"

// Python bindings
void bind_ExploreIShape(nb::module_& m) {

  auto cls = nb::class_<ExploreIShape>(m, "ExploreIShape", "Explore a shape.")
                 .def(nb::init<const IShape&, const IShapeKind, const IShapeKind>(),
                      nb::arg("shape"), nb::arg("find"), nb::arg("ignore") = IShapeKind::Shape,
                      "Constructor to explore a shape.")

                 .def("More", &ExploreIShape::More, "Check if there are more shapes to explore.")
                 .def("Next", &ExploreIShape::Next, "Move to the next shape.")
                 .def("Current", &ExploreIShape::Current, "Get the current shape.");
}