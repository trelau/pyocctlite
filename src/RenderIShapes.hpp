#pragma once

#include "occtlite.hpp"

#include <array>
#include <optional>
#include <string>
#include <vector>

#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

#include "IPoint.hpp"
#include "IShape.hpp"
#include "IVector.hpp"
#include "RasterImage.hpp"

// Tool to render shapes to an image without a GPU or display
class RenderIShapes {
public:
  // Construct the tool with the image size in pixels
  RenderIShapes(int width, int height) : width_(width), height_(height) {}

  // Add a shape with its color components from 0 to 1 and its transparency from 0 to 1
  void AddShape(const IShape& shape, double r, double g, double b, double transparency);

  // Add a shape with a color for each face, cycling through the colors given as r, g, b values.
  // Faces are numbered on the image in the order of a map of faces, starting from 0.
  void AddNumberedFaces(const IShape& shape, const std::vector<double>& colors);

  // Add a shape with the color components for its faces and a color for each edge, cycling through
  // the colors given as r, g, b values. Edges are numbered on the image in the order of a map of
  // edges, starting from 0.
  void AddNumberedEdges(const IShape& shape, double r, double g, double b,
                        const std::vector<double>& colors);

  // Add a text box with a line pointing to the visible part of the shape
  void AddCallout(const IShape& shape, const std::string& text);

  // Remove everything on the side of a plane that its normal points to, including callout targets.
  // From that side, where a solid's material is cut, the image shows hatching over a color. The
  // colors are for each added shape in order, cycling, as r, g, b values from 0 to 1. The normal
  // must not be zero.
  void SetSection(const IPoint& origin, const IVector& normal, const std::vector<double>& colors);

  // Render an orthographic view looking back along the direction, labeled with the text. The view
  // is centered on the point and spans the length across the image's smaller side, each defaulting
  // to fit all shapes. Depth shading also darkens faces that are farther from the viewer. Without
  // labels, the view name, axes and numbers are left out, but callouts are still drawn.
  nb::bytes Render(const IVector& direction, const IVector& up, const std::string& label,
                   const std::optional<IPoint>& center, const std::optional<double>& span,
                   bool isDepthShaded, bool hasLabels);

  // Get the visible pixels of each numbered face, or the visible length in pixels of each numbered
  // edge, in the latest view
  std::vector<int> VisiblePixels() const { return visiblePixels_; }

private:
  // Point on a face with its normal
  struct MeshNode {
    gp_Pnt point;
    gp_Vec normal;
  };

  // Triangle with the index of its face in the shape. On a solid, outward is a normal pointing out
  // of the material, and elsewhere it is zero.
  struct MeshTriangle {
    std::array<MeshNode, 3> nodes;
    int face;
    gp_Vec outward;
  };

  // Everything drawn for one added shape
  struct Item {
    TopoDS_Shape shape;
    RasterColor color{0.0, 0.0, 0.0};
    double transparency = 0.0;
    bool hasNumberedFaces = false;
    bool hasNumberedEdges = false;
    std::vector<RasterColor> faceColors;
    std::vector<RasterColor> edgeColors;
    std::vector<MeshTriangle> triangles;
    std::vector<std::vector<gp_Pnt>> edges;
    std::vector<int> edgeIndices;
    std::vector<gp_Pnt> vertices;
    std::vector<std::array<gp_Pnt, 2>> outline;
    int faceCount = 0;
    int edgeCount = 0;

    // Get the color of a face
    const RasterColor& FaceColor(const int face) const {
      return faceColors.empty() ? color : faceColors[face % faceColors.size()];
    }
  };

  // A shape to point at, which is not drawn
  struct Callout {
    Item target;
    std::string text;
  };

  // A plane with a unit normal pointing to the removed side, and the color of each shape's cut area
  struct Section {
    gp_Pnt origin;
    gp_Vec normal;
    std::vector<RasterColor> colors;
  };

  // Find the scene bounds
  void FindBounds();

  // Mesh every shape with one deflection, unless they already are
  void MeshItems(double deflection);

  // Mesh a copy of one shape, so that the shape itself does not store a mesh, and apply any section
  void MeshItem(Item& item, double deflection) const;

  // Remove what the section removes from a meshed shape, keeping the outline of the cut
  void ClipItem(Item& item) const;

  int width_;
  int height_;
  bool hasBounds_ = false;
  double meshDeflection_ = 0.0;
  std::vector<Item> items_;
  std::vector<Callout> callouts_;
  std::optional<Section> section_;
  std::vector<int> visiblePixels_;
  gp_Pnt center_;
  double radius_ = 0.0;
};

// Python bindings
void bind_RenderIShapes(nb::module_& m);
