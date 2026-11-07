#include "CopyIShape.hpp"

IShape CopyIShape::ModifiedShape(const IShape& shape) const {
  TopoDS_Shape modified = tool_.ModifiedShape(shape);
  return IShape(modified);
}

// Python bindings
void bind_CopyIShape(nb::module_& m) {

  nb::class_<CopyIShape, MakeIShape>(m, "CopyIShape", "Copy a shape.")
      .def(nb::init<const IShape&, const bool>(), nb::arg("shape"), nb::arg("copyGeom") = true,
           "Make a copy of the shape.")

      .def("ModifiedShape", &CopyIShape::ModifiedShape, nb::arg("shape"),
           "Get the modified shape from the input shape.");
}