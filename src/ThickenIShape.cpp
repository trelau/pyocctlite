#include "ThickenIShape.hpp"

ThickenIShape::ThickenIShape(const IShape& shape, double thickness) {

  tool_.MakeThickSolidBySimple(shape, thickness);
}

ThickenIShape::ThickenIShape(const IShape& shape, const std::vector<IShape>& faces, double thickness, double tol) {

  NCollection_List<TopoDS_Shape> removeShapes;
  for (const IShape& f : faces) { removeShapes.Append(f); }

  tool_.MakeThickSolidByJoin(shape, removeShapes, thickness, tol);
}

// Python bindings
void bind_ThickenIShape(nb::module_& m) {

  auto cls = nb::class_<ThickenIShape>(m, "ThickenIShape", "Make a hollow solid with a uniform thickness.")
    .def(nb::init<const IShape&, double>(), nb::arg("shape"), nb::arg("thickness"), "Make a hollow solid from an open shell using a uniform thickness.")
    .def(nb::init<const IShape&, const std::vector<IShape>&, double, double>(), nb::arg("shape"), nb::arg("faces"), nb::arg("thickness"), nb::arg("tol") = 1.0e-3, "Make a hollow solid by removing faces and using a uniform thickness.");

  // MakeShape methods
  bind_MakeShape<ThickenIShape>(cls);
}