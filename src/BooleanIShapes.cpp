#include "BooleanIShapes.hpp"

template <typename T> static void bind_Boolean(nb::module_& m, const char* name, const char* doc) {

  nb::class_<T, MakeIShape>(m, name, doc)
      .def(nb::init<const std::vector<IShape>&, const std::vector<IShape>&, double>(),
           nb::arg("targets"), nb::arg("tools"), nb::arg("tol") = 0.0,
           "Apply the operation between the targets and the tools.")

      .def("IntersectionEdges", &T::IntersectionEdges,
           "Get the edges where the surfaces of the targets and tools intersect.");
}

// Python bindings
void bind_BooleanIShapes(nb::module_& m) {

  bind_Boolean<UniteIShapes>(m, "UniteIShapes", "Unite shapes.");
  bind_Boolean<CutIShapes>(m, "CutIShapes", "Cut shapes (boolean subtraction).");
  bind_Boolean<IntersectIShapes>(m, "IntersectIShapes", "Intersect shapes (boolean common).");
}
