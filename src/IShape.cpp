#include "IShape.hpp"

#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepLib.hxx>
#include <GC_MakeArcOfCircle.hxx>
#include <Geom_TrimmedCurve.hxx>
#include <STEPControl_Writer.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>

#include "IShapeErrors.hpp"

static std::string kindToString(IShapeKind kind) {
  switch (kind) {
  case IShapeKind::Shape:     return "Shape";
  case IShapeKind::Vertex:    return "Vertex";
  case IShapeKind::Edge:      return "Edge";
  case IShapeKind::Wire:      return "Wire";
  case IShapeKind::Face:      return "Face";
  case IShapeKind::Shell:     return "Shell";
  case IShapeKind::Solid:     return "Solid";
  case IShapeKind::CompSolid: return "CompSolid";
  case IShapeKind::Compound:  return "Compound";
  default:                    return "Invalid";
  }
}

std::vector<IShape> IShape::MakeByList(const TopTools_ListOfShape& shapes)
{
  std::vector<IShape> ishapes;
  for (TopTools_ListOfShape::Iterator it(shapes); it.More(); it.Next()) {
    ishapes.emplace_back(IShape(it.Value()));
  }

  return ishapes;
}

IShape IShape::MakeEdge(const IPoint& p1, const IPoint& p2)
{
  TopoDS_Edge e = BRepBuilderAPI_MakeEdge(p1, p2);

  return IShape(e);
}

IShape IShape::MakeEdge(const ICurve& curve) {

  TopoDS_Edge e = BRepBuilderAPI_MakeEdge(curve);

  return IShape(e);
}

IShape IShape::MakeEdge(const ICurve2D& c, const ISurface& s) {

  TopoDS_Edge e = BRepBuilderAPI_MakeEdge(c, s);
  BRepLib::BuildCurve3d(e);

  return IShape(e);
}

IShape IShape::MakeWire(const IShape& edge) {

  TopoDS_Wire w = BRepBuilderAPI_MakeWire(edge.AsEdge());

  return IShape(w);
}

IShape IShape::MakeWire(const std::vector<IShape>& edges) {

  TopTools_ListOfShape oEdges;
  for (const IShape& e : edges) { oEdges.Append(e.AsEdge()); }

  BRepBuilderAPI_MakeWire builder;
  builder.Add(oEdges);
  TopoDS_Wire w = builder.Wire();

  return IShape(w);

}

IShape IShape::MakeWire(const IShape& w1, const IShape& w2) {

  BRepBuilderAPI_MakeWire builder(w1.AsWire());
  builder.Add(w2.AsWire());
  TopoDS_Wire w = builder.Wire();

  return IShape(w);
}

IShape IShape::MakeFace(const IShape& w) {

  TopoDS_Face f = BRepBuilderAPI_MakeFace(w.AsWire(), true);

  return IShape(f);
}

void IShape::ValidateKind(const IShapeKind expected) const {
  if (kind_ != expected) {
    throw IShapeTypeMismatch(
      "Expected " + kindToString(expected) + " but got " + kindToString(kind_) + " instead.");
  }
}

bool IShape::ExportSTEP(const std::string& fname) const {

  // TODO: Suppress console output

  STEPControl_Writer writer;
  IFSelect_ReturnStatus status;

  status = writer.Transfer(shape_, STEPControl_AsIs);
  if (status != IFSelect_RetDone) {
    return false;
  }

  status = writer.Write(fname.c_str());
  if (status != IFSelect_RetDone) {
    return false;
  }

  return true;
}

// Python bindings
void bind_IShape(py::module& m) {

  py::enum_<IShapeKind>(m, "IShapeKind", "Enumeration for shape kinds.")
    .value("Shape", IShapeKind::Shape)
    .value("Vertex", IShapeKind::Vertex)
    .value("Edge", IShapeKind::Edge)
    .value("Wire", IShapeKind::Wire)
    .value("Face", IShapeKind::Face)
    .value("Shell", IShapeKind::Shell)
    .value("Solid", IShapeKind::Solid)
    .value("CompSolid", IShapeKind::CompSolid)
    .value("Compound", IShapeKind::Compound);

  py::class_<IShape>(m, "IShape", "A shape.")
    .def_static("MakeEdge", py::overload_cast<const IPoint&, const IPoint&>(&IShape::MakeEdge), py::arg("p1"), py::arg("p2"), "Make an edge by two points.")
    .def_static("MakeEdge", py::overload_cast<const ICurve&>(&IShape::MakeEdge), py::arg("curve"), "Make an edge by a curve.")
    .def_static("MakeEdge", py::overload_cast<const ICurve2D&, const ISurface&>(&IShape::MakeEdge), py::arg("c"), py::arg("s"), "Make an edge by a 2D curve on a surface.")
    .def_static("MakeWire", py::overload_cast<const IShape&>(&IShape::MakeWire), py::arg("edge"), "Make a wire by a single edge.")
    .def_static("MakeWire", py::overload_cast<const std::vector<IShape>&>(&IShape::MakeWire), py::arg("edges"), "Make a wire by topologically or geometrically connected edges.")
    .def_static("MakeWire", py::overload_cast<const IShape&, const IShape&>(&IShape::MakeWire), py::arg("w1"), py::arg("w2"), "Make a new wire by combining two wires.")
    .def_static("MakeFace", &IShape::MakeFace, py::arg("w"), "Make a face by a planar wire.")

    .def("Kind", &IShape::Kind, "The kind of this shape.")
    .def("IsNull", &IShape::IsNull, "Whether or not this shape is null.")
    .def("IsEqual", &IShape::IsEqual, py::arg("other"), "Check if this shape is equal to the other.")
    .def("IsSame", &IShape::IsSame, py::arg("other"), "Check if this shape is the same as the other (orientation may differ).")
    .def("ExportSTEP", &IShape::ExportSTEP, py::arg("fname"), "Export this shape to a STEP file.");

}