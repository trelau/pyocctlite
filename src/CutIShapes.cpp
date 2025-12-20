#include "CutIShapes.hpp"

#include <TopTools_ListOfShape.hxx>

CutIShapes::CutIShapes(const IShape& target, const std::vector<IShape>& tools) {

  TopTools_ListOfShape oTargets;
  oTargets.Append(target);
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  for (const IShape& s : tools) { oTools.Append(s); }
  tool_.SetTools(oTools);
  tool_.Build();
}

CutIShapes::CutIShapes(const std::vector<IShape>& targets, const IShape& tool) {

  TopTools_ListOfShape oTargets;
  for (const IShape& s : targets) { oTargets.Append(s); }
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  oTools.Append(tool);
  tool_.SetTools(oTools);
  tool_.Build();
}

CutIShapes::CutIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools) {

  TopTools_ListOfShape oTargets;
  for (const IShape& s : targets) { oTargets.Append(s); }
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  for (const IShape& s : tools) { oTools.Append(s); }
  tool_.SetTools(oTools);
  tool_.Build();
}

std::vector<IShape> CutIShapes::IntersectionEdges() {

  std::vector<IShape> edges;
  for (const TopoDS_Shape& s : tool_.SectionEdges()) {
    edges.emplace_back(IShape(s));
  }

  return edges;
}

// Python bindings
void bind_CutIShapes(py::module& m) {

  auto cls = py::class_<CutIShapes>(m, "CutIShapes", "Cut shapes (boolean subtraction).")
    .def(py::init<const IShape&, const IShape&>(), py::arg("target"), py::arg("tool"), "Cut the tool from the target.")
    .def(py::init<const IShape&, const std::vector<IShape>&>(), py::arg("target"), py::arg("tools"), "Cut the tools from the target.")
    .def(py::init<const std::vector<IShape>&, const IShape&>(), py::arg("targets"), py::arg("tool"), "Cut the tool from the targets.")
    .def(py::init<const std::vector<IShape>&, const std::vector<IShape>&>(), py::arg("targets"), py::arg("tools"), "Cut the tools from the targets.")

    .def("IntersectionEdges", &CutIShapes::IntersectionEdges, "Get the intersection edges.");

  // MakeShape methods
  bind_MakeShape<CutIShapes>(cls);
}
