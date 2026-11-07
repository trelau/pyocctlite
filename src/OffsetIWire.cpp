#include "OffsetIWire.hpp"

OffsetIWire::OffsetIWire(const IShape& wire, double distance) : tool_(wire.AsWire()) {

  tool_.Perform(distance);
}

OffsetIWire::OffsetIWire(const IShape& wire, const IShape& spine, double distance) {

  tool_.Init(spine.AsFace());
  tool_.AddWire(wire.AsWire());
  tool_.Perform(distance);
}

// Python bindings
void bind_OffsetIWire(nb::module_& m) {

  nb::class_<OffsetIWire, MakeIShape>(m, "OffsetIWire", "Offset a planar wire within its plane.")
      .def(nb::init<const IShape&, double>(), nb::arg("wire"), nb::arg("distance"),
           "Offset a wire, finding its plane from its own geometry.")
      .def(nb::init<const IShape&, const IShape&, double>(), nb::arg("wire"), nb::arg("spine"),
           nb::arg("distance"), "Offset a wire on a spine face.");
}
