#include "IBoundingBox.hpp"

// Python bindings
void bind_IBoundingBox(nb::module_& m) {

  nb::class_<IBoundingBox>(m, "IBoundingBox", "An axis-aligned bounding box.")
      .def("MinPoint", &IBoundingBox::MinPoint, "Get the corner with the smallest coordinates.")
      .def("MaxPoint", &IBoundingBox::MaxPoint, "Get the corner with the largest coordinates.");
}
