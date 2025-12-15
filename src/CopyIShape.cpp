#include "CopyIShape.hpp"

IShape CopyIShape::ModifiedShape(const IShape& shape) const {
  TopoDS_Shape modified = tool_.ModifiedShape(shape);
  return IShape(modified);
}

// Python bindings
void bind_CopyIShape(py::module& m) {

  auto cls = py::class_<CopyIShape>(m, "CopyIShape", "Copy a shape.")
    .def(py::init<const IShape&, const bool, const bool>(), py::arg("shape"), py::arg("copyGeom") = true, py::arg("copyMesh") = false, "Make a copy of the shape.")

    .def("ModifiedShape", &CopyIShape::ModifiedShape, py::arg("shape"), "Get the modified shape from the input shape.");

  // MakeShape methods
  bind_MakeShape<CopyIShape>(cls);
}