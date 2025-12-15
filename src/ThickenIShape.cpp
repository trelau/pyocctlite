#include "ThickenIShape.hpp"

ThickenIShape::ThickenIShape(const IShape& shape, double thickness) {

  tool_.MakeThickSolidBySimple(shape, thickness);
}

ThickenIShape::ThickenIShape(const IShape& shape, const std::vector<IShape>& faces, double thickness, double tol) {

  TopTools_ListOfShape removeShapes;
  for (const IShape& f : faces) { removeShapes.Append(f); }

  tool_.MakeThickSolidByJoin(shape, removeShapes, thickness, tol);
}

// Python bindings
void bind_ThickenIShape(py::module& m) {

  auto cls = py::class_<ThickenIShape>(m, "ThickenIShape", "Make a hollow solid with a uniform thickness.")
    .def(py::init<const IShape&, double>(), py::arg("shape"), py::arg("thickness"), "Make a hollow solid from an open shell using a uniform thickness.")
    .def(py::init<const IShape&, const std::vector<IShape>&, double, double>(), py::arg("shape"), py::arg("faces"), py::arg("thickness"), py::arg("tol") = 1.0e-3, "Make a hollow solid by removing faces and using a uniform thickness.");

  // MakeShape methods
  bind_MakeShape<ThickenIShape>(cls);
}