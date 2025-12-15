#include "MapIShape.hpp"

#include <TopExp.hxx>

MapIShape::MapIShape(const IShape& shape, const IShapeKind kind)
{
  TopExp::MapShapes(shape, static_cast<TopAbs_ShapeEnum>(kind), tool_);
}

// Python bindings
void bind_MapIShape(py::module& m) {

  auto cls = py::class_<MapIShape>(m, "MapIShape", "Map a shape.")
    .def(py::init<const IShape&, const IShapeKind>(), py::arg("shape"), py::arg("kind"), "Constructor to map a shape.")

    .def("Extent", &MapIShape::Extent, "Get the extent of the map.")
    .def("Size", &MapIShape::Size, "Get the size of the map.")
    .def("FindShape", &MapIShape::FindShape, py::arg("index"), "Find the shape by index.")
    .def("FindIndex", &MapIShape::FindIndex, py::arg("shape"), "Find the index of the shape.")
    .def("Contains", &MapIShape::Contains, py::arg("shape"), "Check if the map contains the shape.");

}