#include "RevolveIShape.hpp"

// Python bindings
void bind_RevolveIShape(nb::module_& m) {

  nb::class_<RevolveIShape, MakeIShape>(m, "RevolveIShape", "Revolve a shape.")
      .def(nb::init<const IShape&, const IAxis&>(), nb::arg("shape"), nb::arg("axis"),
           "Revolve the shape a full turn about the given axis.");
}
