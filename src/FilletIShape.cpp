#include "FilletIShape.hpp"

// Python bindings
void bind_FilletIShape(py::module& m) {

  auto cls = py::class_<FilletIShape>(m, "FilletIShape", "Fillet a shape.")
    .def(py::init<const IShape&>(), py::arg("shape"), "Construct fillet tool with the shape.")

    .def("AddEdge", &FilletIShape::AddEdge, py::arg("edge"), py::arg("radius"), "Add an edge to be filleted with the given radius.");

  // MakeShape methods
  bind_MakeShape<FilletIShape>(cls);
}