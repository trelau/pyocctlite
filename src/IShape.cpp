#include "IShape.hpp"

#include <BRepAdaptor_Curve.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepGProp.hxx>
#include <BRepLib.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <GCPnts_TangentialDeflection.hxx>
#include <GC_MakeArcOfCircle.hxx>
#include <GProp_GProps.hxx>
#include <Geom_TrimmedCurve.hxx>
#include <Message.hxx>
#include <Message_Messenger.hxx>
#include <Message_Printer.hxx>
#include <NCollection_IndexedMap.hxx>
#include <STEPControl_Writer.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopTools_ShapeMapHasher.hxx>
#include <TopoDS_Shape.hxx>

#include "IErrors.hpp"

// Silence OCCT's default messenger below failures for the guard's lifetime
class QuietMessenger {
public:
  QuietMessenger() {
    for (const auto& printer : Message::DefaultMessenger()->Printers()) {
      levels_.push_back(printer->GetTraceLevel());
      printer->SetTraceLevel(Message_Fail);
    }
  }

  ~QuietMessenger() {
    std::size_t i = 0;
    for (const auto& printer : Message::DefaultMessenger()->Printers()) {
      if (i < levels_.size()) {
        printer->SetTraceLevel(levels_[i++]);
      }
    }
  }

private:
  std::vector<Message_Gravity> levels_;
};

static std::string kindToString(IShapeKind kind) {
  switch (kind) {
  case IShapeKind::Shape:
    return "Shape";
  case IShapeKind::Vertex:
    return "Vertex";
  case IShapeKind::Edge:
    return "Edge";
  case IShapeKind::Wire:
    return "Wire";
  case IShapeKind::Face:
    return "Face";
  case IShapeKind::Shell:
    return "Shell";
  case IShapeKind::Solid:
    return "Solid";
  case IShapeKind::CompSolid:
    return "CompSolid";
  case IShapeKind::Compound:
    return "Compound";
  default:
    return "Invalid";
  }
}

std::vector<IShape> IShape::MakeByList(const NCollection_List<TopoDS_Shape>& shapes) {
  std::vector<IShape> ishapes;
  for (NCollection_List<TopoDS_Shape>::Iterator it(shapes); it.More(); it.Next()) {
    ishapes.emplace_back(IShape(it.Value()));
  }

  return ishapes;
}

IShape IShape::MakeVertex(const IPoint& p) {

  TopoDS_Vertex v = BRepBuilderAPI_MakeVertex(p);

  return IShape(v);
}

IShape IShape::MakeEdge(const IPoint& p1, const IPoint& p2) {
  TopoDS_Edge e = BRepBuilderAPI_MakeEdge(p1, p2);

  return IShape(e);
}

IShape IShape::MakeEdge(const IShape& v1, const IShape& v2) {

  TopoDS_Edge e = BRepBuilderAPI_MakeEdge(v1.AsVertex(), v2.AsVertex());

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

  NCollection_List<TopoDS_Shape> oEdges;
  for (const IShape& e : edges) {
    oEdges.Append(e.AsEdge());
  }

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

IShape IShape::MakeSphere(const IFrame& frame, double radius) {

  TopoDS_Solid s = BRepPrimAPI_MakeSphere(frame, radius);

  return IShape(s);
}

IShape IShape::MakeCompound(const std::vector<IShape>& shapes) {

  BRep_Builder builder;
  TopoDS_Compound compound;
  builder.MakeCompound(compound);

  for (const IShape& shape : shapes) {
    builder.Add(compound, shape);
  }

  return IShape(compound);
}

void IShape::ValidateKind(const IShapeKind expected) const {
  if (kind_ != expected) {
    throw IKindMismatch("Expected " + kindToString(expected) + " but got " + kindToString(kind_) +
                        " instead.");
  }
}

bool IShape::ExportSTEP(const std::string& fname) const {

  QuietMessenger quiet;

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

double IShape::Length() const {

  GProp_GProps props;
  BRepGProp::LinearProperties(shape_, props, true, false);

  return props.Mass();
}

double IShape::Area() const {

  GProp_GProps props;
  BRepGProp::SurfaceProperties(shape_, props, true, false);

  return props.Mass();
}

double IShape::Volume() const {

  GProp_GProps props;
  BRepGProp::VolumeProperties(shape_, props, true, true, false);

  return props.Mass();
}

IBoundingBox IShape::BoundingBox() const {

  // Use the exact geometry only, ignoring any stored mesh and shape tolerances
  Bnd_Box box;
  BRepBndLib::AddOptimal(shape_, box, false, false);

  return IBoundingBox(box);
}

IPoint IShape::Centroid() const {

  GProp_GProps props;
  if (TopExp_Explorer(shape_, TopAbs_SOLID).More()) {
    BRepGProp::VolumeProperties(shape_, props, true, true, false);
    return IPoint(props.CentreOfMass());
  }
  if (TopExp_Explorer(shape_, TopAbs_FACE).More()) {
    BRepGProp::SurfaceProperties(shape_, props, true, false);
    return IPoint(props.CentreOfMass());
  }
  if (TopExp_Explorer(shape_, TopAbs_EDGE).More()) {
    BRepGProp::LinearProperties(shape_, props, true, false);
    return IPoint(props.CentreOfMass());
  }

  NCollection_IndexedMap<TopoDS_Shape, TopTools_ShapeMapHasher> vertices;
  TopExp::MapShapes(shape_, TopAbs_VERTEX, vertices);
  if (vertices.IsEmpty()) {
    throw std::runtime_error("Shape is empty.");
  }

  gp_XYZ sum(0.0, 0.0, 0.0);
  for (int i = 1; i <= vertices.Extent(); ++i) {
    sum += BRep_Tool::Pnt(TopoDS::Vertex(vertices.FindKey(i))).XYZ();
  }
  return IPoint(gp_Pnt(sum / vertices.Extent()));
}

bool IShape::IsValid() const { return BRepCheck_Analyzer(shape_).IsValid(); }

std::vector<IPoint> IShape::SamplePoints(const double deflection,
                                         const double angularDeflection) const {

  const BRepAdaptor_Curve curve(AsEdge());
  const GCPnts_TangentialDeflection sampled(curve, angularDeflection, deflection);
  std::vector<IPoint> points;
  for (int i = 1; i <= sampled.NbPoints(); ++i) {
    points.emplace_back(sampled.Value(i));
  }
  return points;
}

std::optional<ICurve> IShape::Curve() const {

  double first, last;
  Handle(Geom_Curve) c = BRep_Tool::Curve(AsEdge(), first, last);
  if (c.IsNull()) {
    return std::nullopt;
  }

  return ICurve(c);
}

IPoint IShape::Point() const { return IPoint(BRep_Tool::Pnt(AsVertex())); }

// Python bindings
void bind_IShape(nb::module_& m) {

  nb::enum_<IShapeKind>(m, "IShapeKind", "Enumeration for shape kinds.")
      .value("Shape", IShapeKind::Shape)
      .value("Vertex", IShapeKind::Vertex)
      .value("Edge", IShapeKind::Edge)
      .value("Wire", IShapeKind::Wire)
      .value("Face", IShapeKind::Face)
      .value("Shell", IShapeKind::Shell)
      .value("Solid", IShapeKind::Solid)
      .value("CompSolid", IShapeKind::CompSolid)
      .value("Compound", IShapeKind::Compound);

  nb::class_<IShape>(m, "IShape", "A shape.")
      .def_static("MakeVertex", &IShape::MakeVertex, nb::arg("p"), "Make a vertex at a point.")
      .def_static("MakeEdge", nb::overload_cast<const IPoint&, const IPoint&>(&IShape::MakeEdge),
                  nb::arg("p1"), nb::arg("p2"), "Make an edge by two points.")
      .def_static("MakeEdge", nb::overload_cast<const IShape&, const IShape&>(&IShape::MakeEdge),
                  nb::arg("v1"), nb::arg("v2"), "Make an edge by two vertices, which it shares.")
      .def_static("MakeEdge", nb::overload_cast<const ICurve&>(&IShape::MakeEdge), nb::arg("curve"),
                  "Make an edge by a curve.")
      .def_static("MakeEdge",
                  nb::overload_cast<const ICurve2D&, const ISurface&>(&IShape::MakeEdge),
                  nb::arg("c"), nb::arg("s"), "Make an edge by a 2D curve on a surface.")
      .def_static("MakeWire", nb::overload_cast<const IShape&>(&IShape::MakeWire), nb::arg("edge"),
                  "Make a wire by a single edge.")
      .def_static("MakeWire", nb::overload_cast<const std::vector<IShape>&>(&IShape::MakeWire),
                  nb::arg("edges"),
                  "Make a wire by topologically or geometrically connected edges.")
      .def_static("MakeWire", nb::overload_cast<const IShape&, const IShape&>(&IShape::MakeWire),
                  nb::arg("w1"), nb::arg("w2"), "Make a new wire by combining two wires.")
      .def_static("MakeFace", &IShape::MakeFace, nb::arg("w"), "Make a face by a planar wire.")
      .def_static("MakeSphere", &IShape::MakeSphere, nb::arg("frame"), nb::arg("radius"),
                  "Make a solid sphere given a frame at its center and a radius.")
      .def_static("MakeCompound", &IShape::MakeCompound, nb::arg("shapes"),
                  "Make a compound from a list of shapes.")

      .def("Kind", &IShape::Kind, "The kind of this shape.")
      .def("IsEqual", &IShape::IsEqual, nb::arg("other"),
           "Check if this shape is equal to the other.")
      .def("IsSame", &IShape::IsSame, nb::arg("other"),
           "Check if this shape is the same as the other (orientation may differ).")
      .def("HashCode", &IShape::HashCode, "Hash code consistent with IsSame.")
      .def("ExportSTEP", &IShape::ExportSTEP, nb::arg("fname"), "Export this shape to a STEP file.")
      .def("Length", &IShape::Length, "Calculate the length of all edges of this shape.")
      .def("Area", &IShape::Area, "Calculate the area of all faces of this shape.")
      .def("Volume", &IShape::Volume, "Calculate the volume of all solids of this shape.")
      .def("BoundingBox", &IShape::BoundingBox,
           "Calculate the axis-aligned bounding box of this shape.")
      .def("Centroid", &IShape::Centroid,
           "Calculate the centroid of the highest dimension present in this shape.")
      .def("IsValid", &IShape::IsValid, "Check if this shape and its sub-shapes are valid.")
      .def("Curve", &IShape::Curve, "Get the curve of this edge, if it has one.")
      .def("SamplePoints", &IShape::SamplePoints, nb::arg("deflection"),
           nb::arg("angularDeflection") = 0.2,
           "Get points along this edge within a deflection and an angle in radians.")
      .def("Point", &IShape::Point, "Get the point of this vertex.");
}