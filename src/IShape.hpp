#pragma once

#include "occtlite.hpp"

#include "TopAbs_ShapeEnum.hxx"
#include <TopoDS.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shell.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_CompSolid.hxx>
#include <TopoDS_Compound.hxx>
#include <TopTools_ListOfShape.hxx>

#include "IPoint.hpp"
#include "IVector.hpp"
#include "ICurve.hpp"
#include "ICurve2D.hpp"
#include "ISurface.hpp"

// Enumeration for shape kinds
enum class IShapeKind {
  Shape = TopAbs_SHAPE,
  Vertex = TopAbs_VERTEX,
  Edge = TopAbs_EDGE,
  Wire = TopAbs_WIRE,
  Face = TopAbs_FACE,
  Shell = TopAbs_SHELL,
  Solid = TopAbs_SOLID,
  CompSolid = TopAbs_COMPSOLID,
  Compound = TopAbs_COMPOUND
};

// Interface class for a shape
class IShape {
public:

  // Factory methods to create shapes
  static std::vector<IShape> MakeByList(const TopTools_ListOfShape& shapes);

  static IShape MakeEdge(const IPoint& p1, const IPoint& p2);

  static IShape MakeEdge(const ICurve& curve);

  static IShape MakeEdge(const ICurve2D& c, const ISurface& s);

  static IShape MakeWire(const IShape& edge);

  static IShape MakeWire(const std::vector<IShape>& edges);

  static IShape MakeWire(const IShape& w1, const IShape& w2);

  static IShape MakeFace(const IShape& w);

  // Constructor from TopoDS_Shape
  explicit IShape(const TopoDS_Shape& s)
    : shape_(s),
    kind_(static_cast<IShapeKind>(s.ShapeType())) {}

  // Get the kind of the shape
  IShapeKind Kind() const { return kind_; }

  // Check if the shape is null
  bool IsNull() const {
    return shape_.IsNull();
  }

  // Check if this shape is equal to another shape
  bool IsEqual(const IShape& other) const {
    return shape_.IsEqual(other);
  }

  // Check if this shape is the same as another shape (orientation may differ)
  bool IsSame(const IShape& other) const {
    return shape_.IsSame(other);
  }

  // Downcast methods to specific shape types
  TopoDS_Shape  AsShape() const {
    return shape_;
  }

  TopoDS_Vertex AsVertex() const {
    ValidateKind(IShapeKind::Vertex);
    return TopoDS::Vertex(shape_);
  }

  TopoDS_Edge AsEdge() const {
    ValidateKind(IShapeKind::Edge);
    return TopoDS::Edge(shape_);
  }

  TopoDS_Wire AsWire() const {
    ValidateKind(IShapeKind::Wire);
    return TopoDS::Wire(shape_);
  }

  TopoDS_Face AsFace() const {
    ValidateKind(IShapeKind::Face);
    return TopoDS::Face(shape_);
  }

  TopoDS_Shell AsShell() const {
    ValidateKind(IShapeKind::Shell);
    return TopoDS::Shell(shape_);
  }

  TopoDS_Solid AsSolid() const {
    ValidateKind(IShapeKind::Solid);
    return TopoDS::Solid(shape_);
  }

  TopoDS_CompSolid AsCompSolid() const {
    ValidateKind(IShapeKind::CompSolid);
    return TopoDS::CompSolid(shape_);
  }

  TopoDS_Compound AsCompound() const {
    ValidateKind(IShapeKind::Compound);
    return TopoDS::Compound(shape_);
  }

  // Export this shape to a STEP file
  bool ExportSTEP(const std::string& fname) const;

  // Validate that the shape is of the expected kind
  void ValidateKind(const IShapeKind expected) const;

  // Conversion operator to TopoDS_Shape
  operator const TopoDS_Shape& () const {
    return shape_;
  }

private:
  TopoDS_Shape shape_;
  IShapeKind   kind_;
};

// Python bindings
void bind_IShape(py::module& m);