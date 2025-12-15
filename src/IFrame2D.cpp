#include "IFrame2D.hpp"

IFrame2D IFrame2D::MakeByOrigin(const IPoint2D& origin) {

  gp_Dir2d x = gp_Dir2d(1., 0.);
  gp_Dir2d y = gp_Dir2d(0., 1.);
  gp_Ax22d f = gp_Ax22d(origin, x, y);

  return IFrame2D(f);
}

IFrame2D IFrame2D::MakeByVector(const IPoint2D& origin, const IVector2D& xVector) {

  gp_Dir2d x = gp_Dir2d(xVector);
  gp_Ax22d f = gp_Ax22d(origin, x, true);

  return IFrame2D(f);
}

// Python bindings
void bind_IFrame2D(py::module& m) {

  py::class_<IFrame2D>(m, "IFrame2D", "A 2D right-handed coordinate frame.")
    .def_static("MakeByOrigin", &IFrame2D::MakeByOrigin, py::arg("origin"), "Make a frame at the given origin with standard orientation.")
    .def_static("MakeByVector", &IFrame2D::MakeByVector, py::arg("origin"), py::arg("xvec"), "Make a frame at the given origin with the specified X-direction.")

    .def("Origin", &IFrame2D::Origin, "Get the origin point of the frame.")
    .def("XDirection", &IFrame2D::XDirection, "Get the X-direction of the frame.")
    .def("YDirection", &IFrame2D::YDirection, "Get the Y-direction of the frame.");

}