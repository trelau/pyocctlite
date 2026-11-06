#pragma once

#include <cstdint>
#include <map>
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

// Pixel deepest inside a region of a grid, with its distance in pixels to the region's boundary
struct RasterPole {
  int x;
  int y;
  int distance;
};

// Grid value for a pixel that is not part of any region
constexpr int kRasterNone = -1;

// Grid values for a shape marked against the image
constexpr int kRasterHidden = 0;
constexpr int kRasterVisible = 1;

// Id for a triangle whose samples become the cut area of a section where they end up on top, using
// the first cut color. Each lower id uses the next color.
constexpr int kRasterCut = -2;

// Find the pole of each region in a grid of pixel values, skipping pixels without a region
std::map<int, RasterPole> FindRasterPoles(const std::vector<int>& grid, int width, int height);

// CPU image with a depth buffer and supersampling for antialiasing.
//
// This is the one part of the C++ layer that makes no OCCT calls. It is here because per-pixel
// loops are too slow in pure Python, and it needs no GPU, window or display on any platform.
class RasterImage {
public:
  // Construct a white image of the given final size in pixels
  RasterImage(int width, int height);

  // Fill a triangle, multiplying its color by the shade interpolated between vertices.
  // Only an opaque triangle writes depth and the id. A translucent one must be drawn back to front.
  void FillTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                    const RasterColor& color, double opacity, int id = kRasterNone);

  // Give the samples of cut triangles that are on top their color with diagonal hatching over it,
  // and move them to the plane whose depth at a final pixel position is
  // depth0 + x * depthPerX + y * depthPerY
  void FillCut(const std::vector<RasterColor>& colors, const RasterColor& hatchColor, double depth0,
               double depthPerX, double depthPerY);

  // Draw a depth-tested line of the given width in final pixels
  void DrawLine(const RasterVertex& a, const RasterVertex& b, const RasterColor& color,
                double lineWidth);

  // Mark the pixels of a triangle in a grid as visible or hidden against the image's depths
  void MarkTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                    std::vector<int>& grid) const;

  // Mark the pixels of a line in a grid as visible or hidden against the image's depths. A line is
  // also hidden by anything nearby that is in front of it by more than the tolerance, so that a
  // hidden line on an outline does not count as visible over the background beside it.
  void MarkLine(const RasterVertex& a, const RasterVertex& b, double lineWidth,
                double nearbyTolerance, std::vector<int>& grid) const;

  // Get the id of the triangle that is on top at each final pixel, from the top row down
  std::vector<int> IdGrid() const;

  // Draw a line on top of everything, for overlays
  void DrawOverlayLine(double x1, double y1, double x2, double y2, const RasterColor& color,
                       double lineWidth);

  // Fill a rectangle on top of everything, for overlays
  void FillOverlayRect(double x, double y, double width, double height, const RasterColor& color);

  // Draw text on top of everything, with its top-left corner at the given position. Printable
  // ASCII is available, a newline starts a new line, and other characters are drawn as "?".
  void DrawOverlayText(const std::string& text, double x, double y, double letterHeight,
                       const RasterColor& color, double lineWidth);

  // Get the width of the longest line of text, in pixels
  static double TextWidth(const std::string& text, double letterHeight);

  // Get the final image as rows of RGB bytes, from the top row down
  std::string ToRGB() const;

private:
  int width_;
  int height_;
  int sampledWidth_;
  int sampledHeight_;
  std::vector<std::uint8_t> pixels_;
  std::vector<float> depths_;
  std::vector<int> ids_;
};
