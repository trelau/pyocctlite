#pragma once

#include "occtlite.hpp"

#include <string>
#include <vector>

#include "RasterImage.hpp"

// Tool to rasterize flat lines, polygons and text strokes in pixel coordinates, from the top row
// down
class RenderICanvas {
public:
  // Construct a white image of the given size in pixels
  RenderICanvas(int width, int height) : image_(width, height, true) {}

  // Draw a line through points given as x, y values, with a width in pixels
  void AddPolyline(const std::vector<double>& points, double r, double g, double b,
                   double lineWidth);

  // Fill a convex polygon through points given as x, y values
  void FillPolygon(const std::vector<double>& points, double r, double g, double b);

  // Get the image as rows of RGB bytes, from the top row down
  nb::bytes Render() const;

private:
  RasterImage image_;
};

// Python bindings
void bind_RenderICanvas(nb::module_& m);
