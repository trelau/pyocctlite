#include "IMeshControl.hpp"

IMeshControl::IMeshControl(int dim, const IShape& shape, std::optional<double> edge_size, std::optional<double> deflection, bool quads)
  : dim_(dim), shape_(shape), edge_size_(edge_size), deflection_(deflection), quads_(quads) {
}

IMeshControl IMeshControl::MakeControl1D(const IShape& shape, std::optional<double> edge_size, std::optional<double> deflection)
{
  return IMeshControl(1, shape, edge_size, deflection, false);
}

IMeshControl IMeshControl::MakeControl2D(const IShape& shape, std::optional<double> edge_size, std::optional<double> deflection, bool quads)
{
  return IMeshControl(2, shape, edge_size, deflection, quads);
}

IMeshControl IMeshControl::MakeControl3D(const IShape& shape, std::optional<double> edge_size, std::optional<double> deflection)
{
  return IMeshControl(3, shape, edge_size, deflection, false);
}

// Python bindings
void bind_IMeshControl(py::module& m) {

  py::class_<IMeshControl>(m, "IMeshControl", "A mesh control.")
    .def_static("MakeControl1D", &IMeshControl::MakeControl1D, py::arg("shape"), py::arg("edge_size") = std::nullopt, py::arg("deflection") = std::nullopt, "Create a 1D mesh control.")
    .def_static("MakeControl2D", &IMeshControl::MakeControl2D, py::arg("shape"), py::arg("edge_size") = std::nullopt, py::arg("deflection") = std::nullopt, py::arg("quads") = false, "Create a 2D mesh control.")
    .def_static("MakeControl3D", &IMeshControl::MakeControl3D, py::arg("shape"), py::arg("edge_size") = std::nullopt, py::arg("deflection") = std::nullopt, "Create a 3D mesh control.")

    .def("Dimension", &IMeshControl::Dimension, "Get the dimension of the mesh control.")
    .def("EdgeSize", &IMeshControl::EdgeSize, "Get the edge size of the mesh control.")
    .def("Deflection", &IMeshControl::Deflection, "Get the deflection of the mesh control.")
    .def("AllowQuads", &IMeshControl::AllowQuads, "Check if quads are allowed in the mesh control.");

}