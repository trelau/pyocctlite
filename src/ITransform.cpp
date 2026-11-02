#include "ITransform.hpp"

#include <gp_Dir.hxx>
#include <gp_Ax2.hxx>

ITransform ITransform::MakeMirror(const IPoint& origin, const IVector& normal) {

  gp_Dir d(normal);
  gp_Ax2 axis(origin, d);
  gp_Trsf trsf;
  trsf.SetMirror(axis);

  return ITransform(trsf);
}

// Python bindings
void bind_ITransform(nb::module_& m) {

  nb::class_<ITransform>(m, "ITransform", "A transformation.")
    .def_static("MakeMirror", &ITransform::MakeMirror, nb::arg("origin"), nb::arg("normal"), "Make a mirror transformation defined by a point and a normal vector.");
}