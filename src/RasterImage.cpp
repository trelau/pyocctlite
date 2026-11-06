#include "RasterImage.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace {

// Samples per pixel along each axis
constexpr int kSamples = 2;

// Square samples allowed beyond a line's radius
constexpr double kLineRadiusTolerance = 1.0e-6;

// Size in letter grid units, where a letter is 4 wide and 6 high
constexpr double kLetterGridWidth = 4.0;
constexpr double kLetterGridHeight = 6.0;
constexpr double kLetterGridAdvance = 5.5;

// One stroke between grid points of a letter
struct LetterStroke {
  char letter;
  int x1;
  int y1;
  int x2;
  int y2;
};

// Strokes for the letters used in view and axis names, on a grid with y pointing down
constexpr LetterStroke kLetterStrokes[] = {
    {'A', 0, 6, 2, 0}, {'A', 2, 0, 4, 6}, {'A', 1, 4, 3, 4}, {'B', 0, 0, 0, 6}, {'B', 0, 0, 3, 0},
    {'B', 3, 0, 4, 1}, {'B', 4, 1, 4, 2}, {'B', 4, 2, 3, 3}, {'B', 0, 3, 3, 3}, {'B', 3, 3, 4, 4},
    {'B', 4, 4, 4, 5}, {'B', 4, 5, 3, 6}, {'B', 3, 6, 0, 6}, {'C', 4, 1, 3, 0}, {'C', 3, 0, 1, 0},
    {'C', 1, 0, 0, 1}, {'C', 0, 1, 0, 5}, {'C', 0, 5, 1, 6}, {'C', 1, 6, 3, 6}, {'C', 3, 6, 4, 5},
    {'E', 4, 0, 0, 0}, {'E', 0, 0, 0, 6}, {'E', 0, 6, 4, 6}, {'E', 0, 3, 3, 3}, {'F', 4, 0, 0, 0},
    {'F', 0, 0, 0, 6}, {'F', 0, 3, 3, 3}, {'G', 4, 1, 3, 0}, {'G', 3, 0, 1, 0}, {'G', 1, 0, 0, 1},
    {'G', 0, 1, 0, 5}, {'G', 0, 5, 1, 6}, {'G', 1, 6, 3, 6}, {'G', 3, 6, 4, 5}, {'G', 4, 5, 4, 3},
    {'G', 4, 3, 2, 3}, {'H', 0, 0, 0, 6}, {'H', 4, 0, 4, 6}, {'H', 0, 3, 4, 3}, {'I', 2, 0, 2, 6},
    {'I', 1, 0, 3, 0}, {'I', 1, 6, 3, 6}, {'K', 0, 0, 0, 6}, {'K', 4, 0, 0, 3}, {'K', 0, 3, 4, 6},
    {'L', 0, 0, 0, 6}, {'L', 0, 6, 4, 6}, {'M', 0, 6, 0, 0}, {'M', 0, 0, 2, 3}, {'M', 2, 3, 4, 0},
    {'M', 4, 0, 4, 6}, {'N', 0, 6, 0, 0}, {'N', 0, 0, 4, 6}, {'N', 4, 6, 4, 0}, {'O', 1, 0, 3, 0},
    {'O', 3, 0, 4, 1}, {'O', 4, 1, 4, 5}, {'O', 4, 5, 3, 6}, {'O', 3, 6, 1, 6}, {'O', 1, 6, 0, 5},
    {'O', 0, 5, 0, 1}, {'O', 0, 1, 1, 0}, {'P', 0, 6, 0, 0}, {'P', 0, 0, 3, 0}, {'P', 3, 0, 4, 1},
    {'P', 4, 1, 4, 2}, {'P', 4, 2, 3, 3}, {'P', 3, 3, 0, 3}, {'R', 0, 6, 0, 0}, {'R', 0, 0, 3, 0},
    {'R', 3, 0, 4, 1}, {'R', 4, 1, 4, 2}, {'R', 4, 2, 3, 3}, {'R', 3, 3, 0, 3}, {'R', 2, 3, 4, 6},
    {'S', 4, 1, 3, 0}, {'S', 3, 0, 1, 0}, {'S', 1, 0, 0, 1}, {'S', 0, 1, 0, 2}, {'S', 0, 2, 1, 3},
    {'S', 1, 3, 3, 3}, {'S', 3, 3, 4, 4}, {'S', 4, 4, 4, 5}, {'S', 4, 5, 3, 6}, {'S', 3, 6, 1, 6},
    {'S', 1, 6, 0, 5}, {'T', 0, 0, 4, 0}, {'T', 2, 0, 2, 6}, {'X', 0, 0, 4, 6}, {'X', 4, 0, 0, 6},
    {'Y', 0, 0, 2, 3}, {'Y', 4, 0, 2, 3}, {'Y', 2, 3, 2, 6}, {'Z', 0, 0, 4, 0}, {'Z', 4, 0, 0, 6},
    {'Z', 0, 6, 4, 6},
};

std::uint8_t ToByte(const double value) {
  return static_cast<std::uint8_t>(std::lround(std::clamp(value, 0.0, 1.0) * 255.0));
}

double EdgeFunction(const RasterVertex& a, const RasterVertex& b, const double x, const double y) {
  return (b.x - a.x) * (y - a.y) - (b.y - a.y) * (x - a.x);
}

} // namespace

RasterImage::RasterImage(const int width, const int height)
    : width_(width), height_(height), sampledWidth_(width * kSamples),
      sampledHeight_(height * kSamples) {

  const std::size_t count =
      static_cast<std::size_t>(sampledWidth_) * static_cast<std::size_t>(sampledHeight_);
  pixels_.assign(count * 3, 255);
  depths_.assign(count, -std::numeric_limits<float>::infinity());
}

void RasterImage::FillTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                               const RasterColor& color, const double opacity) {

  // Work in sample coordinates
  const RasterVertex sa{a.x * kSamples, a.y * kSamples, a.depth, a.shade};
  const RasterVertex sb{b.x * kSamples, b.y * kSamples, b.depth, b.shade};
  const RasterVertex sc{c.x * kSamples, c.y * kSamples, c.depth, c.shade};

  const double area = EdgeFunction(sa, sb, sc.x, sc.y);
  if (area == 0.0) {
    return;
  }

  const int xMin = std::max(0, static_cast<int>(std::floor(std::min({sa.x, sb.x, sc.x}))));
  const int xMax =
      std::min(sampledWidth_ - 1, static_cast<int>(std::ceil(std::max({sa.x, sb.x, sc.x}))));
  const int yMin = std::max(0, static_cast<int>(std::floor(std::min({sa.y, sb.y, sc.y}))));
  const int yMax =
      std::min(sampledHeight_ - 1, static_cast<int>(std::ceil(std::max({sa.y, sb.y, sc.y}))));

  const bool isOpaque = opacity >= 1.0;
  for (int y = yMin; y <= yMax; ++y) {
    for (int x = xMin; x <= xMax; ++x) {
      const double px = x + 0.5;
      const double py = y + 0.5;
      const double wa = EdgeFunction(sb, sc, px, py) / area;
      const double wb = EdgeFunction(sc, sa, px, py) / area;
      const double wc = EdgeFunction(sa, sb, px, py) / area;
      if (wa < 0.0 || wb < 0.0 || wc < 0.0) {
        continue;
      }

      const std::size_t index = static_cast<std::size_t>(y) * sampledWidth_ + x;
      const float depth = static_cast<float>(wa * sa.depth + wb * sb.depth + wc * sc.depth);
      if (depth < depths_[index]) {
        continue;
      }

      const double shade = wa * sa.shade + wb * sb.shade + wc * sc.shade;
      std::uint8_t* pixel = &pixels_[index * 3];
      if (isOpaque) {
        depths_[index] = depth;
        pixel[0] = ToByte(color.r * shade);
        pixel[1] = ToByte(color.g * shade);
        pixel[2] = ToByte(color.b * shade);
      } else {
        pixel[0] = ToByte(color.r * shade * opacity + pixel[0] / 255.0 * (1.0 - opacity));
        pixel[1] = ToByte(color.g * shade * opacity + pixel[1] / 255.0 * (1.0 - opacity));
        pixel[2] = ToByte(color.b * shade * opacity + pixel[2] / 255.0 * (1.0 - opacity));
      }
    }
  }
}

void RasterImage::DrawLine(const RasterVertex& a, const RasterVertex& b, const RasterColor& color,
                           const double lineWidth) {

  // Work in sample coordinates
  const double radius = lineWidth * kSamples * 0.5;
  const double x1 = a.x * kSamples;
  const double y1 = a.y * kSamples;
  const double dx = (b.x - a.x) * kSamples;
  const double dy = (b.y - a.y) * kSamples;
  const double lengthSquared = dx * dx + dy * dy;

  // Allow for rounding, so that samples exactly at the radius are consistently inside the line
  const double limit = radius * radius + kLineRadiusTolerance;

  const int yMin = std::max(0, static_cast<int>(std::floor(std::min(y1, y1 + dy) - radius)));
  const int yMax =
      std::min(sampledHeight_ - 1, static_cast<int>(std::ceil(std::max(y1, y1 + dy) + radius)));
  const int xFirst = std::max(0, static_cast<int>(std::floor(std::min(x1, x1 + dx) - radius)));
  const int xLast =
      std::min(sampledWidth_ - 1, static_cast<int>(std::ceil(std::max(x1, x1 + dx) + radius)));

  for (int y = yMin; y <= yMax; ++y) {
    const double py = y + 0.5;

    // On each row, a line that is not horizontal only reaches a limited span of columns. The span
    // can be huge for a nearly horizontal line, so it is limited before converting to int.
    int xMin = xFirst;
    int xMax = xLast;
    if (dy != 0.0) {
      const double x = x1 + dx * std::clamp((py - y1) / dy, 0.0, 1.0);
      const double span = radius * std::sqrt(lengthSquared) / std::abs(dy) + 1.0;
      xMin = static_cast<int>(std::floor(std::max<double>(xFirst, x - span)));
      xMax = static_cast<int>(std::ceil(std::min<double>(xLast, x + span)));
    }

    for (int x = xMin; x <= xMax; ++x) {
      const double px = x + 0.5;

      // Find the closest point on the line
      double t = 0.0;
      if (lengthSquared > 0.0) {
        t = std::clamp(((px - x1) * dx + (py - y1) * dy) / lengthSquared, 0.0, 1.0);
      }
      const double offsetX = px - (x1 + dx * t);
      const double offsetY = py - (y1 + dy * t);
      if (offsetX * offsetX + offsetY * offsetY > limit) {
        continue;
      }

      const std::size_t index = static_cast<std::size_t>(y) * sampledWidth_ + x;
      const float depth = static_cast<float>(a.depth + (b.depth - a.depth) * t);
      if (depth < depths_[index]) {
        continue;
      }

      depths_[index] = depth;
      std::uint8_t* pixel = &pixels_[index * 3];
      pixel[0] = ToByte(color.r);
      pixel[1] = ToByte(color.g);
      pixel[2] = ToByte(color.b);
    }
  }
}

void RasterImage::DrawOverlayLine(const double x1, const double y1, const double x2,
                                  const double y2, const RasterColor& color,
                                  const double lineWidth) {

  const double top = std::numeric_limits<float>::max();
  DrawLine({x1, y1, top, 1.0}, {x2, y2, top, 1.0}, color, lineWidth);
}

void RasterImage::DrawOverlayText(const std::string& text, const double x, const double y,
                                  const double letterHeight, const RasterColor& color,
                                  const double lineWidth) {

  const double unit = letterHeight / kLetterGridHeight;
  double left = x;
  for (const char letter : text) {
    for (const LetterStroke& stroke : kLetterStrokes) {
      if (stroke.letter == letter) {
        DrawOverlayLine(left + stroke.x1 * unit, y + stroke.y1 * unit, left + stroke.x2 * unit,
                        y + stroke.y2 * unit, color, lineWidth);
      }
    }
    left += kLetterGridAdvance * unit;
  }
}

std::string RasterImage::ToRGB() const {

  std::string rgb(static_cast<std::size_t>(width_) * height_ * 3, '\0');
  for (int y = 0; y < height_; ++y) {
    for (int x = 0; x < width_; ++x) {
      for (int channel = 0; channel < 3; ++channel) {
        int sum = 0;
        for (int sy = 0; sy < kSamples; ++sy) {
          for (int sx = 0; sx < kSamples; ++sx) {
            const std::size_t index =
                static_cast<std::size_t>(y * kSamples + sy) * sampledWidth_ + x * kSamples + sx;
            sum += pixels_[index * 3 + channel];
          }
        }
        const int value = (sum + kSamples * kSamples / 2) / (kSamples * kSamples);
        rgb[(static_cast<std::size_t>(y) * width_ + x) * 3 + channel] = static_cast<char>(value);
      }
    }
  }
  return rgb;
}
