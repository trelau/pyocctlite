#include "ExtrudeIShape.hpp"

// Python bindings
void bind_ExtrudeIShape(nb::module_& m) {

  auto cls =
      nb::class_<ExtrudeIShape>(m, "ExtrudeIShape", "Extrude a shape.")
          .def(nb::init<const IShape&, const IVector&>(), nb::arg("shape"), nb::arg("vector"),
               "Extrude the shape along the given vector.")

          .def("FirstShape", nb::overload_cast<>(&ExtrudeIShape::FirstShape),
               "Get the first shape of the extrusion.")
          .def("FirstShape", nb::overload_cast<const IShape&>(&ExtrudeIShape::FirstShape),
               nb::arg("shape"), "Get the first shape of the extrusion for the given input shape.")
          .def("LastShape", nb::overload_cast<>(&ExtrudeIShape::LastShape),
               "Get the last shape of the extrusion.")
          .def("LastShape", nb::overload_cast<const IShape&>(&ExtrudeIShape::LastShape),
               nb::arg("shape"), "Get the last shape of the extrusion for the given input shape.");

  // MakeShape methods
  bind_MakeShape<ExtrudeIShape>(cls);
}