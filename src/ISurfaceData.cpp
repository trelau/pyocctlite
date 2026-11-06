#include "ISurfaceData.hpp"

void bind_ISurfaceData(nb::module_& m) {

  nb::class_<ICylindricalData>(m, "ICylindricalData", "Cylindrical surface data.")
      .def_ro("Frame", &ICylindricalData::Frame)
      .def_ro("Radius", &ICylindricalData::Radius);
}
