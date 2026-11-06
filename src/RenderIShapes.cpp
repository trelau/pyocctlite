#include "RenderIShapes.hpp"

#include <algorithm>
#include <cmath>

#include <BRepAdaptor_Curve.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_Copy.hxx>
#include <BRepLib_ToolTriangulatedShape.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRep_Tool.hxx>
#include <Bnd_Box.hxx>
#include <GCPnts_TangentialDeflection.hxx>
#include <NCollection_IndexedMap.hxx>
#include <Poly_Triangulation.hxx>
#include <Precision.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopLoc_Location.hxx>
#include <TopTools_ShapeMapHasher.hxx>

#include "IErrors.hpp"

namespace {

using ShapeMap = NCollection_IndexedMap<TopoDS_Shape, TopTools_ShapeMapHasher>;

// Mesh accuracy, with the linear deflection relative to the scene diagonal
constexpr double kRelativeDeflection = 0.0005;
constexpr double kAngularDeflection = 0.2;

// Fraction of the smaller image side that the scene's bounding sphere spans
constexpr double kFitFraction = 0.92;

// Depth offsets relative to the bounding sphere radius. Edges sit in front of faces they lie on,
// and each added shape sits in front of earlier ones it coincides with.
constexpr double kEdgeDepthBias = 0.004;
constexpr double kItemDepthBias = 0.005;

// Shading is an ambient part plus a two-sided diffuse part
constexpr double kAmbient = 0.4;
constexpr double kDiffuse = 0.6;

// Line widths in pixels
constexpr double kFaceEdgeWidth = 1.5;
constexpr double kFreeEdgeWidth = 3.5;
constexpr double kVertexWidth = 9.0;

constexpr RasterColor kFaceEdgeColor{0.1, 0.1, 0.12};

// Axis marker and label layout in pixels
constexpr double kAxisLength = 32.0;
constexpr double kAxisMargin = 48.0;
constexpr double kAxisLetterHeight = 11.0;
constexpr double kMinAxisLabelLength = 8.0;
constexpr double kLabelMargin = 12.0;
constexpr double kLabelHeight = 14.0;

constexpr RasterColor kLabelColor{0.2, 0.2, 0.2};

RasterColor Mix(const RasterColor& color, const RasterColor& other, const double amount) {
  return {color.r + (other.r - color.r) * amount, color.g + (other.g - color.g) * amount,
          color.b + (other.b - color.b) * amount};
}

// Projection from model space to image pixels for one view
struct Camera {
  gp_Pnt center;
  gp_Vec right;
  gp_Vec up;
  gp_Vec toViewer;
  gp_Vec toLight;
  double scale;
  double radius;
  double centerX;
  double centerY;

  RasterVertex Project(const gp_Pnt& point, const double depthBias, const double shade) const {
    const gp_Vec offset(center, point);
    return {centerX + offset.Dot(right) * scale, centerY - offset.Dot(up) * scale,
            offset.Dot(toViewer) / radius + depthBias, shade};
  }

  double Shade(const gp_Vec& normal) const {
    return kAmbient + kDiffuse * std::abs(normal.Dot(toLight));
  }
};

// Draw the X, Y and Z axes as they appear in this view, in a corner of the image
void DrawAxes(RasterImage& image, const Camera& camera, const int height) {

  struct Axis {
    gp_Vec direction;
    RasterColor color;
    const char* name;
  };
  const Axis axes[] = {{gp_Vec(1.0, 0.0, 0.0), {0.8, 0.1, 0.1}, "X"},
                       {gp_Vec(0.0, 1.0, 0.0), {0.1, 0.6, 0.1}, "Y"},
                       {gp_Vec(0.0, 0.0, 1.0), {0.1, 0.2, 0.8}, "Z"}};

  const double x0 = kAxisMargin;
  const double y0 = height - kAxisMargin;
  for (const Axis& axis : axes) {
    const double dx = axis.direction.Dot(camera.right) * kAxisLength;
    const double dy = -axis.direction.Dot(camera.up) * kAxisLength;
    image.DrawOverlayLine(x0, y0, x0 + dx, y0 + dy, axis.color, 2.0);

    // An axis along the view direction has no length, so it gets no letter
    const double length = std::hypot(dx, dy);
    if (length >= kMinAxisLabelLength) {
      const double reach = (length + kAxisLetterHeight) / length;
      image.DrawOverlayText(axis.name, x0 + dx * reach - kAxisLetterHeight / 3.0,
                            y0 + dy * reach - kAxisLetterHeight / 2.0, kAxisLetterHeight,
                            axis.color, 1.5);
    }
  }
}

} // namespace

void RenderIShapes::AddShape(const IShape& shape, const double r, const double g, const double b,
                             const double transparency) {
  items_.push_back({shape.AsShape(), {r, g, b}, transparency, {}, {}, {}});
  isPrepared_ = false;
}

void RenderIShapes::Prepare() {

  // Use the exact geometry only, so the size does not depend on any stored mesh
  Bnd_Box box;
  for (const Item& item : items_) {
    BRepBndLib::AddOptimal(item.shape, box, false, false);
  }
  if (box.IsVoid()) {
    throw IBuildFailed("There is nothing to render.");
  }
  const gp_Pnt lower = box.CornerMin();
  const gp_Pnt upper = box.CornerMax();
  const double diagonal = lower.Distance(upper);
  if (Precision::IsInfinite(diagonal)) {
    throw IBuildFailed("An unbounded shape cannot be rendered.");
  }
  center_ = gp_Pnt((lower.XYZ() + upper.XYZ()) * 0.5);

  // One point has no size, so give it an arbitrary one
  radius_ = diagonal > 0.0 ? diagonal * 0.5 : 1.0;

  for (Item& item : items_) {
    MeshItem(item, radius_ * 2.0 * kRelativeDeflection);
  }
  isPrepared_ = true;
}

void RenderIShapes::MeshItem(Item& item, const double deflection) {

  item.triangles.clear();
  item.edges.clear();
  item.vertices.clear();

  const TopoDS_Shape copy = BRepBuilderAPI_Copy(item.shape, true, false).Shape();
  BRepMesh_IncrementalMesh mesher(copy, deflection, false, kAngularDeflection);

  ShapeMap faces;
  TopExp::MapShapes(copy, TopAbs_FACE, faces);
  for (int i = 1; i <= faces.Extent(); ++i) {
    const TopoDS_Face& face = TopoDS::Face(faces.FindKey(i));

    TopLoc_Location location;
    const occ::handle<Poly_Triangulation>& mesh = BRep_Tool::Triangulation(face, location);
    if (mesh.IsNull() || mesh->NbTriangles() == 0) {
      throw IBuildFailed("Failed to mesh a face for rendering.");
    }
    BRepLib_ToolTriangulatedShape::ComputeNormals(face, mesh);

    const gp_Trsf& trsf = location.Transformation();
    const auto node = [&](const int index) {
      return MeshNode{mesh->Node(index).Transformed(trsf),
                      gp_Vec(mesh->Normal(index).Transformed(trsf))};
    };
    for (int t = 1; t <= mesh->NbTriangles(); ++t) {
      int n1 = 0;
      int n2 = 0;
      int n3 = 0;
      mesh->Triangle(t).Get(n1, n2, n3);
      item.triangles.push_back({node(n1), node(n2), node(n3)});
    }
  }

  ShapeMap edges;
  TopExp::MapShapes(copy, TopAbs_EDGE, edges);
  for (int i = 1; i <= edges.Extent(); ++i) {
    const TopoDS_Edge& edge = TopoDS::Edge(edges.FindKey(i));
    if (BRep_Tool::Degenerated(edge)) {
      continue;
    }

    const BRepAdaptor_Curve curve(edge);
    const GCPnts_TangentialDeflection points(curve, kAngularDeflection, deflection);
    std::vector<gp_Pnt> line;
    for (int p = 1; p <= points.NbPoints(); ++p) {
      line.push_back(points.Value(p));
    }
    item.edges.push_back(std::move(line));
  }

  // Only vertices that are not part of an edge
  for (TopExp_Explorer explorer(copy, TopAbs_VERTEX, TopAbs_EDGE); explorer.More();
       explorer.Next()) {
    item.vertices.push_back(BRep_Tool::Pnt(TopoDS::Vertex(explorer.Current())));
  }
}

nb::bytes RenderIShapes::Render(const IVector& direction, const IVector& up,
                                const std::string& label) {

  if (!isPrepared_) {
    Prepare();
  }

  // Build the view from the direction, making the up vector perpendicular to it
  const gp_Vec toViewer = static_cast<gp_Vec>(direction).Normalized();
  const gp_Vec right = static_cast<gp_Vec>(up).Crossed(toViewer).Normalized();
  const gp_Vec viewUp = toViewer.Crossed(right);

  // Light from above and to the left of the viewer, so that faces at different angles differ
  const gp_Vec toLight = (toViewer * 0.75 - right * 0.35 + viewUp * 0.55).Normalized();

  const double fit = std::min(width_, height_) * 0.5 * kFitFraction;
  const Camera camera{center_,       right,   viewUp,       toViewer,     toLight,
                      fit / radius_, radius_, width_ * 0.5, height_ * 0.5};

  RasterImage image(width_, height_);

  // A translucent triangle is drawn only after everything opaque, from the back to the front
  struct TranslucentTriangle {
    double depth;
    std::array<RasterVertex, 3> vertices;
    const Item* item;
  };
  std::vector<TranslucentTriangle> translucent;

  const auto faceEdgeColor = [](const Item& item) {
    return Mix(kFaceEdgeColor, {1.0, 1.0, 1.0}, item.transparency * 0.7);
  };

  // Draw the edges and vertices of one item
  const auto drawLines = [&](const Item& item, const double itemBias) {
    const bool isFree = item.triangles.empty();
    const RasterColor color = isFree ? item.color : faceEdgeColor(item);
    const double lineWidth = isFree ? kFreeEdgeWidth : kFaceEdgeWidth;
    const double bias = itemBias + kEdgeDepthBias;

    for (const std::vector<gp_Pnt>& line : item.edges) {
      for (std::size_t i = 0; i + 1 < line.size(); ++i) {
        image.DrawLine(camera.Project(line[i], bias, 1.0), camera.Project(line[i + 1], bias, 1.0),
                       color, lineWidth);
      }
    }
    for (const gp_Pnt& vertex : item.vertices) {
      const RasterVertex v = camera.Project(vertex, bias, 1.0);
      image.DrawLine(v, v, item.color, kVertexWidth);
    }
  };

  // Faces first, so that the edges of an earlier item are hidden by the faces of a later one
  for (std::size_t i = 0; i < items_.size(); ++i) {
    const Item& item = items_[i];
    const double itemBias = kItemDepthBias * static_cast<double>(i);
    const bool isOpaque = item.transparency <= 0.0;

    for (const std::array<MeshNode, 3>& triangle : item.triangles) {
      const std::array<RasterVertex, 3> vertices = {
          camera.Project(triangle[0].point, itemBias, camera.Shade(triangle[0].normal)),
          camera.Project(triangle[1].point, itemBias, camera.Shade(triangle[1].normal)),
          camera.Project(triangle[2].point, itemBias, camera.Shade(triangle[2].normal))};
      if (isOpaque) {
        image.FillTriangle(vertices[0], vertices[1], vertices[2], item.color, 1.0);
      } else {
        const double depth = (vertices[0].depth + vertices[1].depth + vertices[2].depth) / 3.0;
        translucent.push_back({depth, vertices, &item});
      }
    }
  }
  for (std::size_t i = 0; i < items_.size(); ++i) {
    if (items_[i].transparency <= 0.0) {
      drawLines(items_[i], kItemDepthBias * static_cast<double>(i));
    }
  }

  std::stable_sort(
      translucent.begin(), translucent.end(),
      [](const TranslucentTriangle& a, const TranslucentTriangle& b) { return a.depth < b.depth; });
  for (const TranslucentTriangle& triangle : translucent) {
    image.FillTriangle(triangle.vertices[0], triangle.vertices[1], triangle.vertices[2],
                       triangle.item->color, 1.0 - triangle.item->transparency);
  }
  for (std::size_t i = 0; i < items_.size(); ++i) {
    if (items_[i].transparency > 0.0) {
      drawLines(items_[i], kItemDepthBias * static_cast<double>(i));
    }
  }

  DrawAxes(image, camera, height_);
  image.DrawOverlayText(label, kLabelMargin, kLabelMargin, kLabelHeight, kLabelColor, 1.5);

  const std::string rgb = image.ToRGB();
  return nb::bytes(rgb.data(), rgb.size());
}

// Python bindings
void bind_RenderIShapes(nb::module_& m) {

  nb::class_<RenderIShapes>(m, "RenderIShapes", "Render shapes to an image.")
      .def(nb::init<int, int>(), nb::arg("width"), nb::arg("height"),
           "Construct the tool with the image size in pixels.")

      .def("AddShape", &RenderIShapes::AddShape, nb::arg("shape"), nb::arg("r"), nb::arg("g"),
           nb::arg("b"), nb::arg("transparency"),
           "Add a shape with its color components and transparency, each from 0 to 1.")

      .def("Render", &RenderIShapes::Render, nb::arg("direction"), nb::arg("up"), nb::arg("label"),
           "Render an orthographic view looking back along the direction as RGB bytes.");
}
