#include "IFrame.hpp"

IFrame IFrame::MakeByOrigin(const IPoint& origin) {

  gp_Dir n = gp_Dir(0., 0., 1.);
  gp_Dir x = gp_Dir(1., 0., 0.);
  gp_Ax2 f = gp_Ax2(origin, n, x);

  return IFrame(f);
}

// Python bindings
void bind_IFrame(py::module& m) {

  py::class_<IFrame>(m, "IFrame", "A 3D right-handed coordinate frame.")
    .def_static("MakeByOrigin", &IFrame::MakeByOrigin, py::arg("origin"), "Make a frame at the given origin with standard orientation.")

    .def("Origin", &IFrame::Origin, "Get the origin point of the frame.")
    .def("Axis", &IFrame::Axis, "Get the axis of the frame.")
    .def("XDirection", &IFrame::XDirection, "Get the X-direction of the frame.")
    .def("YDirection", &IFrame::YDirection, "Get the Y-direction of the frame.")
    .def("ZDirection", &IFrame::ZDirection, "Get the Z-direction of the frame.");

}