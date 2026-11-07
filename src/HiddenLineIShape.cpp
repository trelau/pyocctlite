#include "HiddenLineIShape.hpp"

#include <initializer_list>

#include <BRepLib.hxx>
#include <HLRAlgo_Projector.hxx>
#include <TopoDS_Compound.hxx>
#include <gp_Ax2.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

namespace {

// Combine resulting edges into one compound, which is empty if there are none. The edges
// only have curves in the view's plane until the 3D curves are built.
IShape Combine(std::initializer_list<TopoDS_Shape> parts) {

  BRep_Builder builder;
  TopoDS_Compound compound;
  builder.MakeCompound(compound);
  for (const TopoDS_Shape& part : parts) {
    if (!part.IsNull()) {
      BRepLib::BuildCurves3d(part);
      builder.Add(compound, part);
    }
  }
  return IShape(compound);
}

} // namespace

HiddenLineIShape::HiddenLineIShape(const IShape& shape, const IVector& direction, const IVector& up)
    : algo_(new HLRBRep_Algo()) {

  const gp_Vec toViewer = static_cast<gp_Vec>(direction).Normalized();
  const gp_Vec right = static_cast<gp_Vec>(up).Crossed(toViewer).Normalized();

  algo_->Add(shape);
  algo_->Projector(
      HLRAlgo_Projector(gp_Ax2(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(toViewer), gp_Dir(right))));
  algo_->Update();
  algo_->Hide();
}

IShape HiddenLineIShape::Visible() {
  HLRBRep_HLRToShape tool(algo_);
  return Combine({tool.VCompound(), tool.OutLineVCompound()});
}

IShape HiddenLineIShape::Hidden() {
  HLRBRep_HLRToShape tool(algo_);
  return Combine({tool.HCompound(), tool.OutLineHCompound()});
}

IShape HiddenLineIShape::VisibleSmooth() {
  HLRBRep_HLRToShape tool(algo_);
  return Combine({tool.Rg1LineVCompound()});
}

IShape HiddenLineIShape::HiddenSmooth() {
  HLRBRep_HLRToShape tool(algo_);
  return Combine({tool.Rg1LineHCompound()});
}

// Python bindings
void bind_HiddenLineIShape(nb::module_& m) {

  nb::class_<HiddenLineIShape>(
      m, "HiddenLineIShape",
      "Find the visible and hidden lines of a shape in an orthographic view.")
      .def(nb::init<const IShape&, const IVector&, const IVector&>(), nb::arg("shape"),
           nb::arg("direction"), nb::arg("up"),
           "Construct the tool from a shape, the direction toward the viewer and the up direction.")

      .def("Visible", &HiddenLineIShape::Visible, "Get the visible sharp edges and silhouettes.")

      .def("Hidden", &HiddenLineIShape::Hidden, "Get the hidden sharp edges and silhouettes.")

      .def("VisibleSmooth", &HiddenLineIShape::VisibleSmooth,
           "Get the visible edges between faces that meet smoothly.")

      .def("HiddenSmooth", &HiddenLineIShape::HiddenSmooth,
           "Get the hidden edges between faces that meet smoothly.");
}
