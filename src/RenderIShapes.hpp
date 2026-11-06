#pragma once

#include "occtlite.hpp"

#include <array>
#include <string>
#include <vector>

#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

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

  // Render an orthographic view looking back along the direction, labeled with the text
  nb::bytes Render(const IVector& direction, const IVector& up, const std::string& label);

private:
  // Point on a face with its normal
  struct MeshNode {
    gp_Pnt point;
    gp_Vec normal;
  };

  // Everything drawn for one added shape
  struct Item {
    TopoDS_Shape shape;
    RasterColor color;
    double transparency;
    std::vector<std::array<MeshNode, 3>> triangles;
    std::vector<std::vector<gp_Pnt>> edges;
    std::vector<gp_Pnt> vertices;
  };

  // Find the scene bounds, then mesh every shape with one deflection based on them
  void Prepare();

  // Mesh a copy of one shape, so that the shape itself does not store a mesh
  static void MeshItem(Item& item, double deflection);

  int width_;
  int height_;
  bool isPrepared_ = false;
  std::vector<Item> items_;
  gp_Pnt center_;
  double radius_ = 0.0;
};

// Python bindings
void bind_RenderIShapes(nb::module_& m);
