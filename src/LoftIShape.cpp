#include "LoftIShape.hpp"

// Python bindings
void bind_LoftIShape(nb::module_& m) {

  auto cls = nb::class_<LoftIShape>(m, "LoftIShape", "Tool to make lofted shapes.")
    .def(nb::init<const bool, const bool, double>(), nb::arg("is_solid") = false, nb::arg("is_ruled") = false, nb::arg("tol") = 1.0e-6, "Initialize the tool.")

    .def("AddWire", &LoftIShape::AddWire, nb::arg("wire"), "Add a wire to the loft.");

  // MakeShape methods
  bind_MakeShape<LoftIShape>(cls);
}