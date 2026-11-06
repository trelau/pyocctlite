#include "RevolveIShape.hpp"

// Python bindings
void bind_RevolveIShape(nb::module_& m) {

  auto cls = nb::class_<RevolveIShape>(m, "RevolveIShape", "Revolve a shape.")
                 .def(nb::init<const IShape&, const IAxis&>(), nb::arg("shape"), nb::arg("axis"),
                      "Revolve the shape a full turn about the given axis.");

  // MakeShape methods
  bind_MakeShape<RevolveIShape>(cls);
}
