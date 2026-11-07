#include "FilletIShape.hpp"

// Python bindings
void bind_FilletIShape(nb::module_& m) {

  nb::class_<FilletIShape, MakeIShape>(m, "FilletIShape", "Fillet a shape.")
      .def(nb::init<const IShape&>(), nb::arg("shape"), "Construct fillet tool with the shape.")

      .def("AddEdge", &FilletIShape::AddEdge, nb::arg("edge"), nb::arg("radius"),
           "Add an edge to be filleted with the given radius.");
}