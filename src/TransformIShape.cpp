#include "TransformIShape.hpp"

IShape TransformIShape::ModifiedShape(const IShape& shape) const {
  TopoDS_Shape modified = tool_.ModifiedShape(shape);
  return IShape(modified);
}

// Python bindings
void bind_TransformIShape(py::module& m) {

  auto cls = py::class_<TransformIShape>(m, "TransformIShape", "Transform a shape.")
    .def(py::init<const IShape&, const ITransform&, const bool, const bool>(), py::arg("shape"), py::arg("trsf"), py::arg("copyGeom") = false, py::arg("copyMesh") = false, "Transform the shape.")
    .def("ModifiedShape", &TransformIShape::ModifiedShape, py::arg("shape"), "Get the modified shape from the input shape.");

  // MakeShape methods
  bind_MakeShape<TransformIShape>(cls);
}