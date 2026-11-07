#include "RenderIShapes.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <utility>

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

// A closer view meshes more finely, down to this fraction of the scene diagonal
constexpr double kMinMeshedSpan = 0.05;

// Fraction of the smaller image side that the view's span covers
constexpr double kFitFraction = 0.92;

// Depth offsets relative to the bounding sphere radius. Edges sit in front of faces they lie on.
// Every shape after the first sits by one amount in front of the first, which covers a difference
// in their meshes without letting shapes show through each other, and a tiny further amount for
// each shape decides between shapes that coincide.
constexpr double kEdgeDepthBias = 0.002;
constexpr double kItemDepthBias = 0.003;
constexpr double kItemOrderBias = 2.0e-6;

// A shape in front of a target by less than this, relative to the bounding sphere radius, still
// leaves the target visible. It exceeds the edge bias, so that a target's own edges do not hide it.
constexpr double kTargetDepthBias = 0.006;

// Shading is an ambient part plus a two-sided diffuse part
constexpr double kAmbient = 0.4;
constexpr double kDiffuse = 0.6;

// How much depth shading darkens the farthest face compared to the nearest
constexpr double kDepthFade = 0.65;

// Line widths in pixels
constexpr double kFaceEdgeWidth = 1.5;
constexpr double kFreeEdgeWidth = 3.5;
constexpr double kVertexWidth = 9.0;
constexpr double kNumberedEdgeWidth = 2.5;
constexpr double kCutOutlineWidth = 2.5;

constexpr RasterColor kFaceEdgeColor{0.1, 0.1, 0.12};

// Axis marker and label layout in pixels
constexpr double kAxisLength = 32.0;
constexpr double kAxisMargin = 48.0;
constexpr double kAxisLetterHeight = 11.0;
constexpr double kMinAxisLabelLength = 8.0;
constexpr double kLabelMargin = 12.0;
constexpr double kLabelHeight = 14.0;

constexpr RasterColor kLabelColor{0.2, 0.2, 0.2};

// Text box layout in pixels
constexpr double kNoteLetterHeight = 12.0;
constexpr double kNotePadding = 5.0;
constexpr double kNoteLineAdvance = 18.0;
constexpr double kNoteMargin = 10.0;
constexpr double kNoteGap = 6.0;
constexpr double kLeftColumnTop = 36.0;
constexpr double kLeftColumnBottomMargin = 110.0;
constexpr double kDashLength = 7.0;
constexpr double kDashGap = 5.0;

constexpr RasterColor kNoteBackground{1.0, 1.0, 1.0};

// Thickness of a line or point in pixels when finding where to point at it
constexpr double kTargetLineWidth = 1.5;
constexpr double kTargetVertexWidth = 1.5;

// How steep a surface next to a line can be, in depth per pixel, before it counts as hiding the
// line
constexpr double kNearbySlope = 8.0;

// Shortest visible run of an edge in pixels to number it, so an edge seen end-on gets no number
constexpr std::size_t kMinNumberedRun = 3;

// Pixels a target's face must reach into its visible region to count as visible
constexpr int kMinVisibleFaceDistance = 2;

// Most steps along one segment of a line when looking for its visible part
constexpr double kMaxWalkedPixels = 20000.0;

// Below this cosine between a section's normal and the view, the viewer is not on the removed side
constexpr double kMinCutFacing = 1.0e-6;

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
  bool isDepthShaded;
  double nearest;
  double farthest;

  RasterVertex Project(const gp_Pnt& point, const double depthBias, const double shade) const {
    const gp_Vec offset(center, point);
    return {centerX + offset.Dot(right) * scale, centerY - offset.Dot(up) * scale,
            offset.Dot(toViewer) / radius + depthBias, shade};
  }

  double Shade(const gp_Pnt& point, const gp_Vec& normal) const {
    const double light = kAmbient + kDiffuse * std::abs(normal.Dot(toLight));
    if (!isDepthShaded || farthest >= nearest) {
      return light;
    }
    const double distance = (nearest - gp_Vec(center, point).Dot(toViewer)) / (nearest - farthest);
    return light * (1.0 - kDepthFade * distance);
  }
};

// Where a set of lines has been marked in a grid
struct LineRun {
  std::vector<std::pair<double, double>> longest;
  int visibleLength = 0;
};

// Walk along lines through a grid they were marked in, finding the longest run of visible pixels,
// or of any pixels if not only visible ones are wanted, and the total visible length
LineRun FindLineRun(const std::vector<std::vector<gp_Pnt>>& lines, const Camera& camera,
                    const std::vector<int>& grid, const int width, const int height,
                    const bool isVisibleOnly) {

  LineRun result;
  for (const std::vector<gp_Pnt>& line : lines) {
    std::vector<std::pair<double, double>> run;
    const auto finish = [&]() {
      if (run.size() > result.longest.size()) {
        result.longest = run;
      }
      run.clear();
    };
    for (std::size_t i = 0; i + 1 < line.size(); ++i) {
      const RasterVertex a = camera.Project(line[i], 0.0, 1.0);
      const RasterVertex b = camera.Project(line[i + 1], 0.0, 1.0);
      const double length = std::hypot(b.x - a.x, b.y - a.y);

      // Only walk what is in the image, since a closer view can make a line very long
      if (std::max(a.x, b.x) < 0.0 || std::min(a.x, b.x) >= width || std::max(a.y, b.y) < 0.0 ||
          std::min(a.y, b.y) >= height) {
        finish();
        continue;
      }
      const int steps = static_cast<int>(std::min(std::ceil(length), kMaxWalkedPixels));
      for (int step = 0; step <= steps; ++step) {
        const double t = steps > 0 ? static_cast<double>(step) / steps : 0.0;
        const double x = a.x + (b.x - a.x) * t;
        const double y = a.y + (b.y - a.y) * t;
        const bool isInside = x >= 0.0 && y >= 0.0 && x < width && y < height;
        const int value = isInside ? grid[static_cast<std::size_t>(y) * width + static_cast<int>(x)]
                                   : kRasterNone;
        if (value == kRasterVisible) {
          ++result.visibleLength;
        }
        if (value == kRasterVisible || (!isVisibleOnly && value == kRasterHidden)) {
          run.push_back({x, y});
        } else {
          finish();
        }
      }
    }
    finish();
  }
  return result;
}

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

// A text box and where it points, with no anchor if the target is outside the image
struct Note {
  std::string text;
  bool hasAnchor;
  bool isHidden;
  double anchorX;
  double anchorY;
  double width;
  double height;
  double boxX;
  double boxY;
  bool isLeft;
};

Note MakeNote(const std::string& text, const bool hasAnchor, const bool isHidden,
              const double anchorX, const double anchorY) {

  const double extraLines = static_cast<double>(std::count(text.begin(), text.end(), '\n'));
  const double width = RasterImage::TextWidth(text, kNoteLetterHeight) + kNotePadding * 2.0;
  const double height = extraLines * kNoteLineAdvance + kNoteLetterHeight + kNotePadding * 2.0;
  return {text, hasAnchor, isHidden, anchorX, anchorY, width, height, 0.0, 0.0, false};
}

void DrawBox(RasterImage& image, const std::string& text, const double x, const double y,
             const double width, const double height) {

  image.FillOverlayRect(x, y, width, height, kNoteBackground);
  image.DrawOverlayLine(x, y, x + width, y, kLabelColor, 1.0);
  image.DrawOverlayLine(x + width, y, x + width, y + height, kLabelColor, 1.0);
  image.DrawOverlayLine(x + width, y + height, x, y + height, kLabelColor, 1.0);
  image.DrawOverlayLine(x, y + height, x, y, kLabelColor, 1.0);
  image.DrawOverlayText(text, x + kNotePadding, y + kNotePadding, kNoteLetterHeight, kLabelColor,
                        1.25);
}

// Place the boxes of one column near the height of what they point at, without overlaps if they fit
void PlaceColumn(std::vector<Note*>& column, const double top, const double bottom) {

  std::stable_sort(column.begin(), column.end(),
                   [](const Note* a, const Note* b) { return a->anchorY < b->anchorY; });

  double next = top;
  for (Note* note : column) {
    note->boxY = std::max(note->anchorY - note->height * 0.5, next);
    next = note->boxY + note->height + kNoteGap;
  }

  double limit = bottom;
  for (auto note = column.rbegin(); note != column.rend(); ++note) {
    (*note)->boxY = std::min((*note)->boxY, limit - (*note)->height);
    limit = (*note)->boxY - kNoteGap;
  }

  // Too many boxes to fit share the column evenly, overlapping
  if (!column.empty() && column.front()->boxY < top) {
    const double step = (bottom - top - column.back()->height) /
                        std::max(static_cast<double>(column.size()) - 1.0, 1.0);
    for (std::size_t i = 0; i < column.size(); ++i) {
      column[i]->boxY = top + step * static_cast<double>(i);
    }
  }
}

// Place text boxes in columns on both sides of the image, then draw them and their lines
void DrawNotes(RasterImage& image, std::vector<Note>& notes, const int width, const int height) {

  std::vector<Note*> left;
  std::vector<Note*> right;
  for (Note& note : notes) {
    (note.anchorX < width * 0.5 ? left : right).push_back(&note);
  }

  const auto used = [](const std::vector<Note*>& column) {
    double total = 0.0;
    for (const Note* note : column) {
      total += note->height + kNoteGap;
    }
    return total;
  };
  const auto move = [](std::vector<Note*>& from, std::vector<Note*>& to, const bool takeRightmost) {
    const auto compare = [&](const Note* a, const Note* b) {
      return takeRightmost ? a->anchorX < b->anchorX : a->anchorX > b->anchorX;
    };
    const auto chosen = std::max_element(from.begin(), from.end(), compare);
    to.push_back(*chosen);
    from.erase(chosen);
  };

  // Move boxes from a full column to the other while there is room
  const double leftRoom = height - kLeftColumnBottomMargin - kLeftColumnTop;
  const double rightRoom = height - kNoteMargin * 2.0;
  while (!left.empty() && used(left) > leftRoom && used(right) < rightRoom) {
    move(left, right, true);
  }
  while (!right.empty() && used(right) > rightRoom && used(left) < leftRoom) {
    move(right, left, false);
  }

  for (Note* note : left) {
    note->isLeft = true;
    note->boxX = kNoteMargin;
  }
  for (Note* note : right) {
    note->boxX = std::max(0.0, width - kNoteMargin - note->width);
  }
  PlaceColumn(left, kLeftColumnTop, height - kLeftColumnBottomMargin);
  PlaceColumn(right, kNoteMargin, height - kNoteMargin);

  // Lines go first so that boxes stay readable. A white line under each keeps it visible on any
  // color, and a dashed line points at something hidden.
  for (const Note& note : notes) {
    if (!note.hasAnchor) {
      continue;
    }

    const double startX = note.isLeft ? note.boxX + note.width : note.boxX;
    const double startY = note.boxY + note.height * 0.5;
    const double length = std::hypot(note.anchorX - startX, note.anchorY - startY);
    const double dx = length > 0.0 ? (note.anchorX - startX) / length : 0.0;
    const double dy = length > 0.0 ? (note.anchorY - startY) / length : 0.0;
    const double step = note.isHidden ? kDashLength + kDashGap : std::max(length, 1.0);
    const double drawn = note.isHidden ? kDashLength : step;

    for (const double lineWidth : {3.5, 1.5}) {
      const RasterColor color = lineWidth > 2.0 ? kNoteBackground : kLabelColor;
      for (double position = 0.0; position < length; position += step) {
        const double end = std::min(position + drawn, length);
        image.DrawOverlayLine(startX + dx * position, startY + dy * position, startX + dx * end,
                              startY + dy * end, color, lineWidth);
      }
      image.DrawOverlayLine(note.anchorX, note.anchorY, note.anchorX, note.anchorY, color,
                            lineWidth + 4.5);
    }
  }
  for (const Note& note : notes) {
    DrawBox(image, note.text, note.boxX, note.boxY, note.width, note.height);
  }
}

} // namespace

void RenderIShapes::AddShape(const IShape& shape, const double r, const double g, const double b,
                             const double transparency) {
  Item item;
  item.shape = shape.AsShape();
  item.color = {r, g, b};
  item.transparency = transparency;
  items_.push_back(std::move(item));
  hasBounds_ = false;
  meshDeflection_ = 0.0;
}

void RenderIShapes::AddNumberedFaces(const IShape& shape, const double r, const double g,
                                     const double b, const std::vector<double>& colors,
                                     const std::vector<int>& indices) {

  std::vector<RasterColor> faceColors;
  for (std::size_t i = 0; i + 2 < colors.size(); i += 3) {
    faceColors.push_back({colors[i], colors[i + 1], colors[i + 2]});
  }
  Item item;
  item.shape = shape.AsShape();
  item.color = {r, g, b};
  item.hasNumberedFaces = true;
  item.numbered = {indices.begin(), indices.end()};
  item.faceColors = std::move(faceColors);
  items_.push_back(std::move(item));
  hasBounds_ = false;
  meshDeflection_ = 0.0;
}

void RenderIShapes::AddNumberedEdges(const IShape& shape, const double r, const double g,
                                     const double b, const std::vector<double>& colors,
                                     const std::vector<int>& indices) {

  Item item;
  item.shape = shape.AsShape();
  item.color = {r, g, b};
  item.hasNumberedEdges = true;
  item.numbered = {indices.begin(), indices.end()};
  for (std::size_t i = 0; i + 2 < colors.size(); i += 3) {
    item.edgeColors.push_back({colors[i], colors[i + 1], colors[i + 2]});
  }
  items_.push_back(std::move(item));
  hasBounds_ = false;
  meshDeflection_ = 0.0;
}

void RenderIShapes::AddCallout(const IShape& shape, const std::string& text) {
  Item target;
  target.shape = shape.AsShape();
  callouts_.push_back({std::move(target), text});
  meshDeflection_ = 0.0;
}

void RenderIShapes::SetSection(const IPoint& origin, const IVector& normal,
                               const std::vector<double>& colors) {

  std::vector<RasterColor> cutColors;
  for (std::size_t i = 0; i + 2 < colors.size(); i += 3) {
    cutColors.push_back({colors[i], colors[i + 1], colors[i + 2]});
  }
  section_ = Section{static_cast<gp_Pnt>(origin), static_cast<gp_Vec>(normal).Normalized(),
                     std::move(cutColors)};
  meshDeflection_ = 0.0;
}

void RenderIShapes::FindBounds() {

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
  hasBounds_ = true;
}

void RenderIShapes::MeshItems(const double deflection) {

  if (deflection == meshDeflection_) {
    return;
  }

  for (Item& item : items_) {
    MeshItem(item, deflection);
  }
  for (Callout& callout : callouts_) {
    MeshItem(callout.target, deflection);
  }
  meshDeflection_ = deflection;
}

void RenderIShapes::MeshItem(Item& item, const double deflection) const {

  item.triangles.clear();
  item.edges.clear();
  item.edgeIndices.clear();
  item.vertices.clear();
  item.outline.clear();

  const TopoDS_Shape copy = BRepBuilderAPI_Copy(item.shape, true, false).Shape();
  BRepMesh_IncrementalMesh mesher(copy, deflection, false, kAngularDeflection);

  ShapeMap solidFaces;
  for (TopExp_Explorer solids(copy, TopAbs_SOLID); solids.More(); solids.Next()) {
    TopExp::MapShapes(solids.Current(), TopAbs_FACE, solidFaces);
  }

  ShapeMap faces;
  TopExp::MapShapes(copy, TopAbs_FACE, faces);
  item.faceCount = faces.Extent();
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

    // Triangles wind by the surface's own direction, which a reversed face or a mirroring undoes
    const bool isOnSolid = solidFaces.Contains(face);
    const bool isFlipped = (face.Orientation() == TopAbs_REVERSED) != trsf.IsNegative();
    for (int t = 1; t <= mesh->NbTriangles(); ++t) {
      int n1 = 0;
      int n2 = 0;
      int n3 = 0;
      mesh->Triangle(t).Get(n1, n2, n3);
      const std::array<MeshNode, 3> nodes = {node(n1), node(n2), node(n3)};
      gp_Vec outward(0.0, 0.0, 0.0);
      if (isOnSolid) {
        outward =
            gp_Vec(nodes[0].point, nodes[1].point).Crossed(gp_Vec(nodes[0].point, nodes[2].point));
        if (isFlipped) {
          outward.Reverse();
        }
      }
      item.triangles.push_back({nodes, i - 1, outward});
    }
  }

  ShapeMap edges;
  TopExp::MapShapes(copy, TopAbs_EDGE, edges);
  item.edgeCount = edges.Extent();
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
    item.edgeIndices.push_back(i - 1);
  }

  // Only vertices that are not part of an edge
  for (TopExp_Explorer explorer(copy, TopAbs_VERTEX, TopAbs_EDGE); explorer.More();
       explorer.Next()) {
    item.vertices.push_back(BRep_Tool::Pnt(TopoDS::Vertex(explorer.Current())));
  }

  if (section_) {
    ClipItem(item);
  }
}

void RenderIShapes::ClipItem(Item& item) const {

  const auto distance = [&](const gp_Pnt& point) {
    return gp_Vec(section_->origin, point).Dot(section_->normal);
  };
  const auto between = [](const gp_Pnt& a, const gp_Pnt& b, const double t) {
    return gp_Pnt(a.XYZ() + (b.XYZ() - a.XYZ()) * t);
  };

  std::vector<MeshTriangle> triangles;
  for (const MeshTriangle& triangle : item.triangles) {
    const std::array<MeshNode, 3>& nodes = triangle.nodes;
    const std::array<double, 3> distances = {distance(nodes[0].point), distance(nodes[1].point),
                                             distance(nodes[2].point)};
    const auto isRemoved = [](const double value) { return value > 0.0; };
    const auto removed = std::count_if(distances.begin(), distances.end(), isRemoved);
    if (removed == 3) {
      continue;
    }
    if (removed == 0) {
      triangles.push_back(triangle);
      continue;
    }

    // Walk around the triangle, keeping its part on this side and noting where the plane crosses it
    std::vector<MeshNode> polygon;
    std::vector<gp_Pnt> crossings;
    for (std::size_t i = 0; i < 3; ++i) {
      const std::size_t next = (i + 1) % 3;
      if (!isRemoved(distances[i])) {
        polygon.push_back(nodes[i]);
      }
      if (isRemoved(distances[i]) != isRemoved(distances[next])) {
        // Normals stay unscaled, so that the shading is the same as on the whole triangle
        const double t = distances[i] / (distances[i] - distances[next]);
        const gp_Pnt point = between(nodes[i].point, nodes[next].point, t);
        const gp_Vec normal = nodes[i].normal + (nodes[next].normal - nodes[i].normal) * t;
        polygon.push_back({point, normal});
        crossings.push_back(point);
      }
    }
    for (std::size_t i = 1; i + 1 < polygon.size(); ++i) {
      triangles.push_back(
          {{polygon[0], polygon[i], polygon[i + 1]}, triangle.face, triangle.outward});
    }
    item.outline.push_back({crossings[0], crossings[1]});
  }
  item.triangles = std::move(triangles);

  // An edge can leave a kept part on each side of a removed one, so it can become several lines
  std::vector<std::vector<gp_Pnt>> edges;
  std::vector<int> edgeIndices;
  for (std::size_t e = 0; e < item.edges.size(); ++e) {
    const std::vector<gp_Pnt>& line = item.edges[e];
    std::vector<gp_Pnt> part;
    const auto finish = [&]() {
      if (part.size() > 1) {
        edges.push_back(part);
        edgeIndices.push_back(item.edgeIndices[e]);
      }
      part.clear();
    };
    for (std::size_t i = 0; i < line.size(); ++i) {
      const double current = distance(line[i]);
      if (i > 0) {
        const double previous = distance(line[i - 1]);
        if ((previous > 0.0) != (current > 0.0)) {
          part.push_back(between(line[i - 1], line[i], previous / (previous - current)));
          if (current > 0.0) {
            finish();
          }
        }
      }
      if (current <= 0.0) {
        part.push_back(line[i]);
      }
    }
    finish();
  }
  item.edges = std::move(edges);
  item.edgeIndices = std::move(edgeIndices);

  const auto isVertexRemoved = [&](const gp_Pnt& point) { return distance(point) > 0.0; };
  item.vertices.erase(std::remove_if(item.vertices.begin(), item.vertices.end(), isVertexRemoved),
                      item.vertices.end());
}

nb::bytes RenderIShapes::Render(const IVector& direction, const IVector& up,
                                const std::string& label, const std::optional<IPoint>& center,
                                const std::optional<double>& span, const bool isDepthShaded,
                                const bool hasLabels) {

  if (!hasBounds_) {
    FindBounds();
  }

  // Keep the mesh accurate for the view, since a closer view shows its facets
  const double diagonal = radius_ * 2.0;
  const double spanned = span ? *span : diagonal;
  const double meshedSpan = std::clamp(spanned, diagonal * kMinMeshedSpan, diagonal);
  MeshItems(meshedSpan * kRelativeDeflection);

  // Build the view from the direction, making the up vector perpendicular to it
  const gp_Vec toViewer = static_cast<gp_Vec>(direction).Normalized();
  const gp_Vec right = static_cast<gp_Vec>(up).Crossed(toViewer).Normalized();
  const gp_Vec viewUp = toViewer.Crossed(right);

  // Light from above and to the left of the viewer, so that faces at different angles differ
  const gp_Vec toLight = (toViewer * 0.75 - right * 0.35 + viewUp * 0.55).Normalized();

  const double scale = std::min(width_, height_) * kFitFraction / spanned;
  const gp_Pnt viewCenter = center ? static_cast<gp_Pnt>(*center) : center_;

  // Depth shading spans the faces in the view direction, so it uses the full range on any part
  double nearest = -std::numeric_limits<double>::infinity();
  double farthest = std::numeric_limits<double>::infinity();
  for (const Item& item : items_) {
    for (const MeshTriangle& triangle : item.triangles) {
      for (const MeshNode& node : triangle.nodes) {
        const double depth = gp_Vec(viewCenter, node.point).Dot(toViewer);
        nearest = std::max(nearest, depth);
        farthest = std::min(farthest, depth);
      }
    }
  }

  const Camera camera{viewCenter, right,        viewUp,        toViewer,      toLight, scale,
                      radius_,    width_ * 0.5, height_ * 0.5, isDepthShaded, nearest, farthest};

  // The bias that puts each shape in front of the earlier ones it coincides with
  const auto itemBias = [](const std::size_t index) {
    return index == 0 ? 0.0 : kItemDepthBias + kItemOrderBias * static_cast<double>(index);
  };

  RasterImage image(width_, height_);

  // A translucent triangle is drawn only after everything opaque, from the back to the front
  struct TranslucentTriangle {
    double depth;
    std::array<RasterVertex, 3> vertices;
    RasterColor color;
    double opacity;
  };
  std::vector<TranslucentTriangle> translucent;

  const auto faceEdgeColor = [](const Item& item) {
    return Mix(kFaceEdgeColor, {1.0, 1.0, 1.0}, item.transparency * 0.7);
  };

  // Only from the removed side can a section show the inside of a solid
  const double cutFacing = section_ ? toViewer.Dot(section_->normal) : 0.0;
  const bool isCutVisible = cutFacing > kMinCutFacing && !section_->colors.empty();

  // Draw the edges and vertices of one item
  const auto drawLines = [&](const Item& item, const double shapeBias) {
    const bool isFree = item.faceCount == 0;

    // The color of a numbered shape is for its faces, which free edges of it do not have
    const RasterColor plainColor =
        isFree && !item.hasNumberedEdges ? item.color : faceEdgeColor(item);
    const double plainWidth = isFree ? kFreeEdgeWidth : kFaceEdgeWidth;
    const double bias = shapeBias + kEdgeDepthBias;

    for (std::size_t e = 0; e < item.edges.size(); ++e) {
      const std::vector<gp_Pnt>& line = item.edges[e];
      const int index = item.edgeIndices[e];
      const bool isNumbered = item.IsEdgeNumbered(index);
      const RasterColor color =
          isNumbered ? item.edgeColors[static_cast<std::size_t>(index) % item.edgeColors.size()]
                     : plainColor;
      const double lineWidth = isNumbered ? kNumberedEdgeWidth : plainWidth;
      for (std::size_t i = 0; i + 1 < line.size(); ++i) {
        image.DrawLine(camera.Project(line[i], bias, 1.0), camera.Project(line[i + 1], bias, 1.0),
                       color, lineWidth);
      }
    }
    for (const gp_Pnt& vertex : item.vertices) {
      const RasterVertex v = camera.Project(vertex, bias, 1.0);
      image.DrawLine(v, v, item.color, kVertexWidth);
    }
    for (const std::array<gp_Pnt, 2>& segment : item.outline) {
      image.DrawLine(camera.Project(segment[0], bias, 1.0), camera.Project(segment[1], bias, 1.0),
                     plainColor, isCutVisible ? kCutOutlineWidth : kFaceEdgeWidth);
    }
  };

  // Faces first, so that the edges of an earlier item are hidden by the faces of a later one
  for (std::size_t i = 0; i < items_.size(); ++i) {
    const Item& item = items_[i];
    const double bias = itemBias(i);
    const bool isOpaque = item.transparency <= 0.0;

    for (const MeshTriangle& triangle : item.triangles) {
      const std::array<MeshNode, 3>& nodes = triangle.nodes;
      const std::array<RasterVertex, 3> vertices = {
          camera.Project(nodes[0].point, bias, camera.Shade(nodes[0].point, nodes[0].normal)),
          camera.Project(nodes[1].point, bias, camera.Shade(nodes[1].point, nodes[1].normal)),
          camera.Project(nodes[2].point, bias, camera.Shade(nodes[2].point, nodes[2].normal))};
      const RasterColor& color = item.FaceColor(triangle.face);
      if (isOpaque) {
        // Seeing the far side of a solid's surface first means looking through the cut into
        // material
        const bool isCut = isCutVisible && triangle.outward.Dot(toViewer) < 0.0;
        const int faceId = item.IsFaceNumbered(triangle.face) ? triangle.face : kRasterNone;
        image.FillTriangle(vertices[0], vertices[1], vertices[2], color, 1.0,
                           isCut ? kRasterCut - static_cast<int>(i) : faceId);
      } else {
        const double depth = (vertices[0].depth + vertices[1].depth + vertices[2].depth) / 3.0;
        translucent.push_back({depth, vertices, color, 1.0 - item.transparency});
      }
    }
  }

  // The cut lies on the plane, in front of whatever edges and translucent faces are behind it
  if (isCutVisible) {
    const gp_Vec& normal = section_->normal;
    const double perDistance = 1.0 / (cutFacing * radius_);
    const double depthPerX = -right.Dot(normal) * perDistance / scale;
    const double depthPerY = viewUp.Dot(normal) * perDistance / scale;
    const double depthAtCenter = gp_Vec(viewCenter, section_->origin).Dot(normal) * perDistance;
    image.FillCut(section_->colors, kFaceEdgeColor,
                  depthAtCenter - camera.centerX * depthPerX - camera.centerY * depthPerY,
                  depthPerX, depthPerY);
  }

  for (std::size_t i = 0; i < items_.size(); ++i) {
    if (items_[i].transparency <= 0.0) {
      drawLines(items_[i], itemBias(i));
    }
  }

  std::stable_sort(
      translucent.begin(), translucent.end(),
      [](const TranslucentTriangle& a, const TranslucentTriangle& b) { return a.depth < b.depth; });
  for (const TranslucentTriangle& triangle : translucent) {
    image.FillTriangle(triangle.vertices[0], triangle.vertices[1], triangle.vertices[2],
                       triangle.color, triangle.opacity);
  }
  for (std::size_t i = 0; i < items_.size(); ++i) {
    if (items_[i].transparency > 0.0) {
      drawLines(items_[i], itemBias(i));
    }
  }

  std::vector<Note> notes;
  struct NumberBox {
    std::string text;
    double x;
    double y;
    double width;
    double height;
  };
  std::vector<NumberBox> numberBoxes;

  // Number each visible face, on the face if there is room for the number
  visiblePixels_.clear();
  for (const Item& item : items_) {
    if (!item.hasNumberedFaces) {
      continue;
    }

    visiblePixels_.assign(item.faceCount, 0);
    const std::vector<int> ids = image.IdGrid();
    for (const int id : ids) {
      if (id != kRasterNone) {
        ++visiblePixels_[id];
      }
    }
    const std::map<int, RasterPole> facePoles =
        hasLabels ? FindRasterPoles(ids, width_, height_) : std::map<int, RasterPole>{};
    for (const auto& [face, pole] : facePoles) {
      const std::string text = std::to_string(face);
      Note note = MakeNote(text, true, false, pole.x + 0.5, pole.y + 0.5);
      if (pole.distance >= std::max(note.width, note.height) * 0.5) {
        numberBoxes.push_back({text, note.anchorX - note.width * 0.5,
                               note.anchorY - note.height * 0.5, note.width, note.height});
      } else {
        notes.push_back(std::move(note));
      }
    }
  }

  // Find where to point at each callout's target, using the scene's depths before any overlays
  const double targetBias = itemBias(items_.size() - 1) + kTargetDepthBias;
  const double nearbyTolerance = kNearbySlope / (scale * radius_);

  // Number each visible edge at the middle of its longest visible run
  for (const Item& item : items_) {
    if (!item.hasNumberedEdges) {
      continue;
    }

    visiblePixels_.assign(item.edgeCount, 0);
    std::vector<int> grid(static_cast<std::size_t>(width_) * height_);
    for (std::size_t e = 0; e < item.edges.size(); ++e) {
      const int index = item.edgeIndices[e];
      if (!item.IsEdgeNumbered(index)) {
        continue;
      }

      const std::vector<gp_Pnt>& line = item.edges[e];
      std::fill(grid.begin(), grid.end(), kRasterNone);
      for (std::size_t i = 0; i + 1 < line.size(); ++i) {
        image.MarkLine(camera.Project(line[i], targetBias, 1.0),
                       camera.Project(line[i + 1], targetBias, 1.0), kTargetLineWidth,
                       nearbyTolerance, grid);
      }

      const LineRun run = FindLineRun({line}, camera, grid, width_, height_, true);
      if (run.longest.size() >= kMinNumberedRun) {
        const std::pair<double, double>& middle = run.longest[run.longest.size() / 2];
        visiblePixels_[index] = run.visibleLength;
        if (hasLabels) {
          notes.push_back(
              MakeNote(std::to_string(index), true, false, middle.first, middle.second));
        }
      }
    }
  }

  for (const Callout& callout : callouts_) {
    const Item& target = callout.target;
    std::vector<int> grid(static_cast<std::size_t>(width_) * height_, kRasterNone);

    const bool hasFaces = !target.triangles.empty();
    for (const MeshTriangle& triangle : target.triangles) {
      image.MarkTriangle(camera.Project(triangle.nodes[0].point, targetBias, 1.0),
                         camera.Project(triangle.nodes[1].point, targetBias, 1.0),
                         camera.Project(triangle.nodes[2].point, targetBias, 1.0), grid);
    }
    if (!hasFaces) {
      for (const std::vector<gp_Pnt>& line : target.edges) {
        for (std::size_t i = 0; i + 1 < line.size(); ++i) {
          image.MarkLine(camera.Project(line[i], targetBias, 1.0),
                         camera.Project(line[i + 1], targetBias, 1.0), kTargetLineWidth,
                         nearbyTolerance, grid);
        }
      }
      for (const gp_Pnt& vertex : target.vertices) {
        const RasterVertex v = camera.Project(vertex, targetBias, 1.0);
        image.MarkLine(v, v, kTargetVertexWidth, nearbyTolerance, grid);
      }
    }

    const std::map<int, RasterPole> poles = FindRasterPoles(grid, width_, height_);
    const auto visible = poles.find(kRasterVisible);
    const auto hidden = poles.find(kRasterHidden);
    const bool isVisible =
        visible != poles.end() &&
        (!hasFaces || visible->second.distance >= kMinVisibleFaceDistance || hidden == poles.end());

    // Thin targets have no deep pixels, so point at the middle of their longest run along a line
    const bool isThin = !hasFaces && !target.edges.empty();
    const std::vector<std::pair<double, double>> run =
        isThin ? FindLineRun(target.edges, camera, grid, width_, height_, isVisible).longest
               : std::vector<std::pair<double, double>>{};
    if (!run.empty()) {
      const std::pair<double, double>& middle = run[run.size() / 2];
      const std::string text = isVisible ? callout.text : callout.text + " (hidden)";
      notes.push_back(MakeNote(text, true, !isVisible, middle.first, middle.second));
    } else if (isVisible) {
      const RasterPole& pole = visible->second;
      notes.push_back(MakeNote(callout.text, true, false, pole.x + 0.5, pole.y + 0.5));
    } else if (hidden != poles.end()) {
      const RasterPole& pole = hidden->second;
      notes.push_back(MakeNote(callout.text + " (hidden)", true, true, pole.x + 0.5, pole.y + 0.5));
    } else {
      notes.push_back(MakeNote(callout.text + " (out of view)", false, false, width_, height_));
    }
  }

  if (hasLabels) {
    DrawAxes(image, camera, height_);
  }
  DrawNotes(image, notes, width_, height_);
  for (const NumberBox& box : numberBoxes) {
    DrawBox(image, box.text, box.x, box.y, box.width, box.height);
  }
  if (hasLabels) {
    image.DrawOverlayText(label, kLabelMargin, kLabelMargin, kLabelHeight, kLabelColor, 1.5);
  }

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

      .def("AddNumberedFaces", &RenderIShapes::AddNumberedFaces, nb::arg("shape"), nb::arg("r"),
           nb::arg("g"), nb::arg("b"), nb::arg("colors"), nb::arg("indices"),
           "Add a shape with a color for its faces, and a number on each visible face at the "
           "indices and a color for each of those from r, g, b values.")

      .def("AddNumberedEdges", &RenderIShapes::AddNumberedEdges, nb::arg("shape"), nb::arg("r"),
           nb::arg("g"), nb::arg("b"), nb::arg("colors"), nb::arg("indices"),
           "Add a shape with a color for its faces, and a number on each visible edge at the "
           "indices and a color for each of those from r, g, b values.")

      .def("AddCallout", &RenderIShapes::AddCallout, nb::arg("shape"), nb::arg("text"),
           "Add a text box with a line pointing to the visible part of the shape.")

      .def("SetSection", &RenderIShapes::SetSection, nb::arg("origin"), nb::arg("normal"),
           nb::arg("colors"),
           "Remove everything on the side of a plane that its normal points to, showing hatching "
           "over a color where a solid's material is cut, with a color for each added shape from "
           "r, g, b values.")

      .def("Render", &RenderIShapes::Render, nb::arg("direction"), nb::arg("up"), nb::arg("label"),
           nb::arg("center").none(), nb::arg("span").none(), nb::arg("isDepthShaded"),
           nb::arg("hasLabels"),
           "Render an orthographic view looking back along the direction as RGB bytes.")

      .def("VisiblePixels", &RenderIShapes::VisiblePixels,
           "Get the visible pixels of each numbered face, or the visible length in pixels of each "
           "numbered edge, in the latest view.");
}
