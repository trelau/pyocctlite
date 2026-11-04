#include "CopyIShape.hpp"

IShape CopyIShape::ModifiedShape(const IShape& shape) const {
  TopoDS_Shape modified = tool_.ModifiedShape(shape);
  return IShape(modified);
}

// Python bindings
void bind_CopyIShape(nb::module_& m) {

  auto cls =
      nb::class_<CopyIShape>(m, "CopyIShape", "Copy a shape.")
          .def(nb::init<const IShape&, const bool, const bool>(), nb::arg("shape"),
               nb::arg("copyGeom") = true, nb::arg("copyMesh") = false, "Make a copy of the shape.")

          .def("ModifiedShape", &CopyIShape::ModifiedShape, nb::arg("shape"),
               "Get the modified shape from the input shape.");

  // MakeShape methods
  bind_MakeShape<CopyIShape>(cls);
}