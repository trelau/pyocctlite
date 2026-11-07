#include "TransformIShape.hpp"

IShape TransformIShape::ModifiedShape(const IShape& shape) const {
  TopoDS_Shape modified = tool_.ModifiedShape(shape);
  return IShape(modified);
}

// Python bindings
void bind_TransformIShape(nb::module_& m) {

  nb::class_<TransformIShape, MakeIShape>(m, "TransformIShape", "Transform a shape.")
      .def(nb::init<const IShape&, const ITransform&, const bool, const bool>(), nb::arg("shape"),
           nb::arg("trsf"), nb::arg("copyGeom") = false, nb::arg("copyMesh") = false,
           "Transform the shape.")
      .def("ModifiedShape", &TransformIShape::ModifiedShape, nb::arg("shape"),
           "Get the modified shape from the input shape.");
}