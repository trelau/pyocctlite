#pragma once

#include <cstdint>
#include <string>
#include <vector>

// RGB color with components from 0 to 1
struct RasterColor {
  double r;
  double g;
  double b;
};

// Vertex in pixel coordinates, where a larger depth is closer to the viewer
struct RasterVertex {
  double x;
  double y;
  double depth;
  double shade;
};

// CPU image with a depth buffer and supersampling for antialiasing.
//
// This is the one part of the C++ layer that makes no OCCT calls. It is here because per-pixel
// loops are too slow in pure Python, and it needs no GPU, window or display on any platform.
class RasterImage {
public:
  // Construct a white image of the given final size in pixels
  RasterImage(int width, int height);

  // Fill a triangle, multiplying its color by the shade interpolated between vertices.
  // Only an opaque triangle writes depth. A translucent one must be drawn back to front.
  void FillTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                    const RasterColor& color, double opacity);

  // Draw a depth-tested line of the given width in final pixels
  void DrawLine(const RasterVertex& a, const RasterVertex& b, const RasterColor& color,
                double lineWidth);

  // Draw a line on top of everything, for overlays
  void DrawOverlayLine(double x1, double y1, double x2, double y2, const RasterColor& color,
                       double lineWidth);

  // Draw text on top of everything, with its top-left corner at the given position. Only the
  // letters needed for view and axis names are available, and others are left blank.
  void DrawOverlayText(const std::string& text, double x, double y, double letterHeight,
                       const RasterColor& color, double lineWidth);

  // Get the final image as rows of RGB bytes, from the top row down
  std::string ToRGB() const;

private:
  int width_;
  int height_;
  int sampledWidth_;
  int sampledHeight_;
  std::vector<std::uint8_t> pixels_;
  std::vector<float> depths_;
};
