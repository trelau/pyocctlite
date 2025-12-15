#include "LoftIShape.hpp"

// Python bindings
void bind_LoftIShape(py::module& m) {

  auto cls = py::class_<LoftIShape>(m, "LoftIShape", "Tool to make lofted shapes.")
    .def(py::init<const bool, const bool, double>(), py::arg("is_solid") = false, py::arg("is_ruled") = false, py::arg("tol") = 1.0e-6, "Initialize the tool.")

    .def("AddWire", &LoftIShape::AddWire, py::arg("wire"), "Add a wire to the loft.");

  // MakeShape methods
  bind_MakeShape<LoftIShape>(cls);
}