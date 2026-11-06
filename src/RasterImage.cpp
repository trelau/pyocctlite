#include "RasterImage.hpp"

#include <algorithm>
#include <cmath>
#include <limits>

namespace {

// Samples per pixel along each axis
constexpr int kSamples = 2;

// Samples around a line that can hide it, which reaches past the edge of a line of target width
constexpr int kLineSightSamples = 2;

// Square pixels allowed beyond a line's radius
constexpr double kLineRadiusTolerance = 1.0e-6;

// Hatching of a cut area, as the horizontal distance between lines and their horizontal width in
// final pixels. It stays the same at any zoom, so that thin walls and small parts still show it.
constexpr double kHatchSpacing = 8.0;
constexpr double kHatchWidth = 1.5;

// Size in letter grid units, where a capital letter is 4 wide and 6 high
constexpr double kLetterGridWidth = 4.0;
constexpr double kLetterGridHeight = 6.0;
constexpr double kLetterGridAdvance = 5.5;

// Distance between lines of text, relative to the letter height
constexpr double kLineAdvance = 1.5;

// Strokes for the printable ASCII characters, starting from the space. Each polyline is a run of
// x and y digits on the letter grid, with y pointing down and polylines separated by a space.
constexpr const char* kLetters[] = {
    "",                                    // space
    "2024 2526",                           // !
    "1012 3032",                           // "
    "1016 3036 0242 0444",                 // #
    "413010010213334445361605 2006",       // $
    "0010110100 3545463635 4006",          // %
    "4612112031320405162644",              // &
    "2022",                                // '
    "30212536",                            // (
    "10212516",                            // )
    "2125 0244 4204",                      // *
    "2125 0343",                           // +
    "252617",                              // ,
    "0343",                                // -
    "2526",                                // .
    "4006",                                // /
    "103041453616050110 0541",             // 0
    "112026 1636",                         // 1
    "01103041420646",                      // 2
    "0110304142334445361605 1333",         // 3
    "36300444",                            // 4
    "400003334445361605",                  // 5
    "30100105163645443303",                // 6
    "004016",                              // 7
    "103041423313020110 1304051636454433", // 8
    "43130201103041453616",                // 9
    "2122 2526",                           // :
    "2122 252617",                         // ;
    "400346",                              // <
    "0242 0444",                           // =
    "004306",                              // >
    "01103041422324 2526",                 // ?
    "453616050110304144242242",            // @
    "062046 1434",                         // A
    "06003041423303 3344453606",           // B
    "4130100105163645",                    // C
    "00304145360600",                      // D
    "40000646 0333",                       // E
    "400006 0333",                         // F
    "41301001051636454323",                // G
    "0006 4046 0343",                      // H
    "2026 1030 1636",                      // I
    "4045361605",                          // J
    "0006 400346",                         // K
    "000646",                              // L
    "0600234046",                          // M
    "06004640",                            // N
    "103041453616050110",                  // O
    "06003041423303",                      // P
    "103041453616050110 2446",             // Q
    "06003041423303 2346",                 // R
    "413010010213334445361605",            // S
    "0040 2026",                           // T
    "000516364540",                        // U
    "002640",                              // V
    "0016233640",                          // W
    "0046 4006",                           // X
    "002340 2326",                         // Y
    "00400646",                            // Z
    "30202636",                            // [
    "0046",                                // backslash
    "10202616",                            // ]
    "022042",                              // ^
    "0747",                                // _
    "1021",                                // `
    "12324346 441405163645",               // a
    "0006 0312324345361605",               // b
    "4332120305163645",                    // c
    "4046 4332120305163645",               // d
    "04444332120305163645",                // e
    "4130201116 0333",                     // f
    "4332120305163645 4247381807",         // g
    "0006 0312324346",                     // h
    "2226 2021",                           // i
    "3237281807 3031",                     // j
    "0006 420446",                         // k
    "10202536",                            // l
    "0206 03122326 23324346",              // m
    "0206 0312324346",                     // n
    "123243453616050312",                  // o
    "0208 0312324345361605",               // p
    "4248 4332120305163645",               // q
    "0206 03123243",                       // r
    "43321203143445361605",                // s
    "1015263645 0232",                     // t
    "0205163645 4246",                     // u
    "022642",                              // v
    "0216243642",                          // w
    "0246 4206",                           // x
    "0205163645 4247381807",               // y
    "02420646",                            // z
    "30212213242536",                      // {
    "2028",                                // |
    "10212233242516",                      // }
    "03123443",                            // ~
};

std::uint8_t ToByte(const double value) {
  return static_cast<std::uint8_t>(std::lround(std::clamp(value, 0.0, 1.0) * 255.0));
}

double EdgeFunction(const RasterVertex& a, const RasterVertex& b, const double x, const double y) {
  return (b.x - a.x) * (y - a.y) - (b.y - a.y) * (x - a.x);
}

// Limit a pixel position before converting it, since it can be far outside a zoomed image
int ToPixel(const double value, const int last) {
  return static_cast<int>(std::clamp(value, 0.0, static_cast<double>(last)));
}

// Call a function with the position and interpolation weights of each pixel inside a triangle
template <typename Function>
void ForEachTrianglePixel(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                          const int width, const int height, const Function& function) {

  const double area = EdgeFunction(a, b, c.x, c.y);
  if (area == 0.0) {
    return;
  }

  const int xMin = ToPixel(std::floor(std::min({a.x, b.x, c.x})), width - 1);
  const int xMax = ToPixel(std::ceil(std::max({a.x, b.x, c.x})), width - 1);
  const int yMin = ToPixel(std::floor(std::min({a.y, b.y, c.y})), height - 1);
  const int yMax = ToPixel(std::ceil(std::max({a.y, b.y, c.y})), height - 1);

  for (int y = yMin; y <= yMax; ++y) {
    for (int x = xMin; x <= xMax; ++x) {
      const double px = x + 0.5;
      const double py = y + 0.5;
      const double wa = EdgeFunction(b, c, px, py) / area;
      const double wb = EdgeFunction(c, a, px, py) / area;
      const double wc = EdgeFunction(a, b, px, py) / area;
      if (wa >= 0.0 && wb >= 0.0 && wc >= 0.0) {
        function(x, y, wa, wb, wc);
      }
    }
  }
}

// Call a function with the position and fraction along the line of each pixel inside a line
template <typename Function>
void ForEachLinePixel(const RasterVertex& a, const RasterVertex& b, const double radius,
                      const int width, const int height, const Function& function) {

  const double dx = b.x - a.x;
  const double dy = b.y - a.y;
  const double lengthSquared = dx * dx + dy * dy;

  // Allow for rounding, so that pixels exactly at the radius are consistently inside the line
  const double limit = radius * radius + kLineRadiusTolerance;

  const int yMin = ToPixel(std::floor(std::min(a.y, b.y) - radius), height - 1);
  const int yMax = ToPixel(std::ceil(std::max(a.y, b.y) + radius), height - 1);
  const int xFirst = ToPixel(std::floor(std::min(a.x, b.x) - radius), width - 1);
  const int xLast = ToPixel(std::ceil(std::max(a.x, b.x) + radius), width - 1);

  for (int y = yMin; y <= yMax; ++y) {
    const double py = y + 0.5;

    // On each row, a line that is not horizontal only reaches a limited span of columns
    int xMin = xFirst;
    int xMax = xLast;
    if (dy != 0.0) {
      const double x = a.x + dx * std::clamp((py - a.y) / dy, 0.0, 1.0);
      const double span = radius * std::sqrt(lengthSquared) / std::abs(dy) + 1.0;
      xMin = std::max(xFirst, ToPixel(std::floor(x - span), width - 1));
      xMax = std::min(xLast, ToPixel(std::ceil(x + span), width - 1));
    }

    for (int x = xMin; x <= xMax; ++x) {
      const double px = x + 0.5;

      // Find the closest point on the line
      double t = 0.0;
      if (lengthSquared > 0.0) {
        t = std::clamp(((px - a.x) * dx + (py - a.y) * dy) / lengthSquared, 0.0, 1.0);
      }
      const double offsetX = px - (a.x + dx * t);
      const double offsetY = py - (a.y + dy * t);
      if (offsetX * offsetX + offsetY * offsetY <= limit) {
        function(x, y, t);
      }
    }
  }
}

} // namespace

std::map<int, RasterPole> FindRasterPoles(const std::vector<int>& grid, const int width,
                                          const int height) {

  // Distance to the nearest pixel of another region, counting diagonal steps as one pixel
  std::vector<int> distances(grid.size(), 0);

  const auto update = [&](const int x, const int y, const int (&steps)[4][2]) {
    const std::size_t index = static_cast<std::size_t>(y) * width + x;
    if (grid[index] == kRasterNone) {
      return;
    }

    int nearest = distances[index] > 0 ? distances[index] - 1 : width + height;
    for (int i = 0; i < 4; ++i) {
      const int nx = x + steps[i][0];
      const int ny = y + steps[i][1];
      if (nx < 0 || ny < 0 || nx >= width || ny >= height) {
        nearest = 0;
        break;
      }
      const std::size_t neighbor = static_cast<std::size_t>(ny) * width + nx;
      nearest = grid[neighbor] == grid[index] ? std::min(nearest, distances[neighbor]) : 0;
      if (nearest == 0) {
        break;
      }
    }
    distances[index] = nearest + 1;
  };

  const int forward[4][2] = {{-1, 0}, {0, -1}, {-1, -1}, {1, -1}};
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      update(x, y, forward);
    }
  }
  const int backward[4][2] = {{1, 0}, {0, 1}, {1, 1}, {-1, 1}};
  for (int y = height - 1; y >= 0; --y) {
    for (int x = width - 1; x >= 0; --x) {
      update(x, y, backward);
    }
  }

  std::map<int, RasterPole> poles;
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const std::size_t index = static_cast<std::size_t>(y) * width + x;
      if (grid[index] == kRasterNone) {
        continue;
      }
      const auto found = poles.find(grid[index]);
      if (found == poles.end() || distances[index] > found->second.distance) {
        poles[grid[index]] = {x, y, distances[index]};
      }
    }
  }
  return poles;
}

RasterImage::RasterImage(const int width, const int height)
    : width_(width), height_(height), sampledWidth_(width * kSamples),
      sampledHeight_(height * kSamples) {

  const std::size_t count =
      static_cast<std::size_t>(sampledWidth_) * static_cast<std::size_t>(sampledHeight_);
  pixels_.assign(count * 3, 255);
  depths_.assign(count, -std::numeric_limits<float>::infinity());
  ids_.assign(count, kRasterNone);
}

void RasterImage::FillTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                               const RasterColor& color, const double opacity, const int id) {

  // Work in sample coordinates
  const RasterVertex sa{a.x * kSamples, a.y * kSamples, a.depth, a.shade};
  const RasterVertex sb{b.x * kSamples, b.y * kSamples, b.depth, b.shade};
  const RasterVertex sc{c.x * kSamples, c.y * kSamples, c.depth, c.shade};

  const bool isOpaque = opacity >= 1.0;
  const auto fill = [&](const int x, const int y, const double wa, const double wb,
                        const double wc) {
    const std::size_t index = static_cast<std::size_t>(y) * sampledWidth_ + x;
    const float depth = static_cast<float>(wa * sa.depth + wb * sb.depth + wc * sc.depth);
    if (depth < depths_[index]) {
      return;
    }

    const double shade = wa * sa.shade + wb * sb.shade + wc * sc.shade;
    std::uint8_t* pixel = &pixels_[index * 3];
    if (isOpaque) {
      depths_[index] = depth;
      ids_[index] = id;
      pixel[0] = ToByte(color.r * shade);
      pixel[1] = ToByte(color.g * shade);
      pixel[2] = ToByte(color.b * shade);
    } else {
      const double rest = (1.0 - opacity) / 255.0;
      pixel[0] = ToByte(color.r * shade * opacity + pixel[0] * rest);
      pixel[1] = ToByte(color.g * shade * opacity + pixel[1] * rest);
      pixel[2] = ToByte(color.b * shade * opacity + pixel[2] * rest);
    }
  };
  ForEachTrianglePixel(sa, sb, sc, sampledWidth_, sampledHeight_, fill);
}

void RasterImage::FillCut(const std::vector<RasterColor>& colors, const RasterColor& hatchColor,
                          const double depth0, const double depthPerX, const double depthPerY) {

  for (int y = 0; y < sampledHeight_; ++y) {
    for (int x = 0; x < sampledWidth_; ++x) {
      const std::size_t index = static_cast<std::size_t>(y) * sampledWidth_ + x;
      if (ids_[index] > kRasterCut) {
        continue;
      }

      const double px = (x + 0.5) / kSamples;
      const double py = (y + 0.5) / kSamples;
      const bool isHatch = std::fmod(px + py, kHatchSpacing) < kHatchWidth;
      const std::size_t item = static_cast<std::size_t>(kRasterCut - ids_[index]);
      const RasterColor& color = isHatch ? hatchColor : colors[item % colors.size()];
      depths_[index] = static_cast<float>(depth0 + px * depthPerX + py * depthPerY);
      ids_[index] = kRasterNone;
      std::uint8_t* pixel = &pixels_[index * 3];
      pixel[0] = ToByte(color.r);
      pixel[1] = ToByte(color.g);
      pixel[2] = ToByte(color.b);
    }
  }
}

void RasterImage::DrawLine(const RasterVertex& a, const RasterVertex& b, const RasterColor& color,
                           const double lineWidth) {

  // Work in sample coordinates
  const RasterVertex sa{a.x * kSamples, a.y * kSamples, a.depth, a.shade};
  const RasterVertex sb{b.x * kSamples, b.y * kSamples, b.depth, b.shade};

  const auto draw = [&](const int x, const int y, const double t) {
    const std::size_t index = static_cast<std::size_t>(y) * sampledWidth_ + x;
    const float depth = static_cast<float>(a.depth + (b.depth - a.depth) * t);
    if (depth < depths_[index]) {
      return;
    }

    depths_[index] = depth;
    std::uint8_t* pixel = &pixels_[index * 3];
    pixel[0] = ToByte(color.r);
    pixel[1] = ToByte(color.g);
    pixel[2] = ToByte(color.b);
  };
  ForEachLinePixel(sa, sb, lineWidth * kSamples * 0.5, sampledWidth_, sampledHeight_, draw);
}

void RasterImage::MarkTriangle(const RasterVertex& a, const RasterVertex& b, const RasterVertex& c,
                               std::vector<int>& grid) const {

  const auto mark = [&](const int x, const int y, const double wa, const double wb,
                        const double wc) {
    const std::size_t sample =
        static_cast<std::size_t>(y * kSamples) * sampledWidth_ + x * kSamples;
    const std::size_t index = static_cast<std::size_t>(y) * width_ + x;
    const float depth = static_cast<float>(wa * a.depth + wb * b.depth + wc * c.depth);
    if (depth >= depths_[sample]) {
      grid[index] = kRasterVisible;
    } else if (grid[index] == kRasterNone) {
      grid[index] = kRasterHidden;
    }
  };
  ForEachTrianglePixel(a, b, c, width_, height_, mark);
}

void RasterImage::MarkLine(const RasterVertex& a, const RasterVertex& b, const double lineWidth,
                           const double nearbyTolerance, std::vector<int>& grid) const {

  const auto mark = [&](const int x, const int y, const double t) {
    const std::size_t sample =
        static_cast<std::size_t>(y * kSamples) * sampledWidth_ + x * kSamples;
    const std::size_t index = static_cast<std::size_t>(y) * width_ + x;
    const float depth = static_cast<float>(a.depth + (b.depth - a.depth) * t);

    float nearest = depths_[sample];
    for (int sy = -kLineSightSamples; sy <= kLineSightSamples; ++sy) {
      for (int sx = -kLineSightSamples; sx <= kLineSightSamples; ++sx) {
        const int px = x * kSamples + sx;
        const int py = y * kSamples + sy;
        if (px >= 0 && py >= 0 && px < sampledWidth_ && py < sampledHeight_) {
          nearest = std::max(nearest, depths_[static_cast<std::size_t>(py) * sampledWidth_ + px]);
        }
      }
    }

    if (depth >= depths_[sample] && depth + nearbyTolerance >= nearest) {
      grid[index] = kRasterVisible;
    } else if (grid[index] == kRasterNone) {
      grid[index] = kRasterHidden;
    }
  };
  ForEachLinePixel(a, b, lineWidth * 0.5, width_, height_, mark);
}

std::vector<int> RasterImage::IdGrid() const {

  std::vector<int> grid(static_cast<std::size_t>(width_) * height_);
  for (int y = 0; y < height_; ++y) {
    for (int x = 0; x < width_; ++x) {
      grid[static_cast<std::size_t>(y) * width_ + x] =
          ids_[static_cast<std::size_t>(y * kSamples) * sampledWidth_ + x * kSamples];
    }
  }
  return grid;
}

void RasterImage::DrawOverlayLine(const double x1, const double y1, const double x2,
                                  const double y2, const RasterColor& color,
                                  const double lineWidth) {

  const double top = std::numeric_limits<float>::max();
  DrawLine({x1, y1, top, 1.0}, {x2, y2, top, 1.0}, color, lineWidth);
}

void RasterImage::FillOverlayRect(const double x, const double y, const double width,
                                  const double height, const RasterColor& color) {

  const int xMin = ToPixel(std::floor(x * kSamples), sampledWidth_ - 1);
  const int xMax = ToPixel(std::ceil((x + width) * kSamples), sampledWidth_ - 1);
  const int yMin = ToPixel(std::floor(y * kSamples), sampledHeight_ - 1);
  const int yMax = ToPixel(std::ceil((y + height) * kSamples), sampledHeight_ - 1);

  for (int py = yMin; py <= yMax; ++py) {
    for (int px = xMin; px <= xMax; ++px) {
      const std::size_t index = static_cast<std::size_t>(py) * sampledWidth_ + px;
      depths_[index] = std::numeric_limits<float>::max();
      std::uint8_t* pixel = &pixels_[index * 3];
      pixel[0] = ToByte(color.r);
      pixel[1] = ToByte(color.g);
      pixel[2] = ToByte(color.b);
    }
  }
}

void RasterImage::DrawOverlayText(const std::string& text, const double x, const double y,
                                  const double letterHeight, const RasterColor& color,
                                  const double lineWidth) {

  const double unit = letterHeight / kLetterGridHeight;
  double left = x;
  double top = y;
  for (const char letter : text) {
    if (letter == '\n') {
      left = x;
      top += letterHeight * kLineAdvance;
      continue;
    }

    const bool isPrintable = letter >= ' ' && letter <= '~';
    const char* stroke = kLetters[(isPrintable ? letter : '?') - ' '];
    double lastX = 0.0;
    double lastY = 0.0;
    bool hasLast = false;
    for (; *stroke != '\0'; ++stroke) {
      if (*stroke == ' ') {
        hasLast = false;
        continue;
      }

      const double px = left + (stroke[0] - '0') * unit;
      const double py = top + (stroke[1] - '0') * unit;
      ++stroke;
      if (hasLast) {
        DrawOverlayLine(lastX, lastY, px, py, color, lineWidth);
      }
      lastX = px;
      lastY = py;
      hasLast = true;
    }
    left += kLetterGridAdvance * unit;
  }
}

double RasterImage::TextWidth(const std::string& text, const double letterHeight) {

  const double unit = letterHeight / kLetterGridHeight;
  std::size_t longest = 0;
  std::size_t current = 0;
  for (const char letter : text) {
    current = letter == '\n' ? 0 : current + 1;
    longest = std::max(longest, current);
  }
  if (longest == 0) {
    return 0.0;
  }
  return (static_cast<double>(longest - 1) * kLetterGridAdvance + kLetterGridWidth) * unit;
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
