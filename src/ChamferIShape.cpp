#include "ChamferIShape.hpp"

// Python bindings
void bind_ChamferIShape(nb::module_& m) {

  nb::class_<ChamferIShape, MakeIShape>(m, "ChamferIShape", "Chamfer a shape.")
      .def(nb::init<const IShape&>(), nb::arg("shape"), "Construct chamfer tool with the shape.")

      .def("AddEdge", &ChamferIShape::AddEdge, nb::arg("edge"), nb::arg("distance"),
           "Add an edge to be chamfered with the given distance on both adjacent faces.");
}
