#include "ExtrudeIShape.hpp"

// Python bindings
void bind_ExtrudeIShape(py::module& m) {

  auto cls = py::class_<ExtrudeIShape>(m, "ExtrudeIShape", "Extrude a shape.")
    .def(py::init<const IShape&, const IVector&>(), py::arg("shape"), py::arg("vector"), "Extrude the shape along the given vector.")

    .def("FirstShape", py::overload_cast<>(&ExtrudeIShape::FirstShape), "Get the first shape of the extrusion.")
    .def("FirstShape", py::overload_cast<const IShape&>(&ExtrudeIShape::FirstShape), py::arg("shape"), "Get the first shape of the extrusion for the given input shape.")
    .def("LastShape", py::overload_cast<>(&ExtrudeIShape::LastShape), "Get the last shape of the extrusion.")
    .def("LastShape", py::overload_cast<const IShape&>(&ExtrudeIShape::LastShape), py::arg("shape"), "Get the last shape of the extrusion for the given input shape.");

  // MakeShape methods
  bind_MakeShape<ExtrudeIShape>(cls);
}