#include "RenderICanvas.hpp"

void RenderICanvas::AddPolyline(const std::vector<double>& points, const double r, const double g,
                                const double b, const double lineWidth) {

  const RasterColor color{r, g, b};
  for (std::size_t i = 0; i + 3 < points.size(); i += 2) {
    image_.DrawLine({points[i], points[i + 1], 0.0, 1.0}, {points[i + 2], points[i + 3], 0.0, 1.0},
                    color, lineWidth);
  }
}

void RenderICanvas::FillPolygon(const std::vector<double>& points, const double r, const double g,
                                const double b) {

  const RasterColor color{r, g, b};
  const RasterVertex first{points[0], points[1], 0.0, 1.0};
  for (std::size_t i = 2; i + 3 < points.size(); i += 2) {
    image_.FillTriangle(first, {points[i], points[i + 1], 0.0, 1.0},
                        {points[i + 2], points[i + 3], 0.0, 1.0}, color, 1.0);
  }
}

nb::bytes RenderICanvas::Render() const {

  const std::string rgb = image_.ToRGB();
  return nb::bytes(rgb.data(), rgb.size());
}

// Python bindings
void bind_RenderICanvas(nb::module_& m) {

  nb::class_<RenderICanvas>(m, "RenderICanvas", "Rasterize flat lines and polygons.")
      .def(nb::init<int, int>(), nb::arg("width"), nb::arg("height"),
           "Construct the tool with the image size in pixels.")

      .def("AddPolyline", &RenderICanvas::AddPolyline, nb::arg("points"), nb::arg("r"),
           nb::arg("g"), nb::arg("b"), nb::arg("lineWidth"),
           "Draw a line through points given as x, y values, with a width in pixels.")

      .def("FillPolygon", &RenderICanvas::FillPolygon, nb::arg("points"), nb::arg("r"),
           nb::arg("g"), nb::arg("b"), "Fill a convex polygon through points given as x, y values.")

      .def("Render", &RenderICanvas::Render, "Get the image as rows of RGB bytes.")

      .def_static("TextStrokes", &RasterImage::TextStrokes, nb::arg("text"),
                  nb::arg("letterHeight"),
                  "Get the polylines of one line of text as x, y values, with y pointing down from "
                  "the top of its letters.")

      .def_static("TextWidth", &RasterImage::TextWidth, nb::arg("text"), nb::arg("letterHeight"),
                  "Get the width of the longest line of text.");
}
