#include "UniteIShapes.hpp"

#include <TopTools_ListOfShape.hxx>

UniteIShapes::UniteIShapes(const IShape& target, const std::vector<IShape>& tools) {

  TopTools_ListOfShape oTargets;
  oTargets.Append(target);
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  for (const IShape& s : tools) { oTools.Append(s); }
  tool_.SetTools(oTools);
  tool_.Build();
}

UniteIShapes::UniteIShapes(const std::vector<IShape>& targets, const IShape& tool) {

  TopTools_ListOfShape oTargets;
  for (const IShape& s : targets) { oTargets.Append(s); }
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  oTools.Append(tool);
  tool_.SetTools(oTools);
  tool_.Build();
}

UniteIShapes::UniteIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools) {

  TopTools_ListOfShape oTargets;
  for (const IShape& s : targets) { oTargets.Append(s); }
  tool_.SetArguments(oTargets);

  TopTools_ListOfShape oTools;
  for (const IShape& s : tools) { oTools.Append(s); }
  tool_.SetTools(oTools);
  tool_.Build();
}

std::vector<IShape> UniteIShapes::IntersectionEdges() {

  std::vector<IShape> edges;
  for (const TopoDS_Shape& s : tool_.SectionEdges()) {
    edges.emplace_back(IShape(s));
  }

  return edges;
}

// Python bindings
void bind_UniteIShapes(nb::module_& m) {

  auto cls = nb::class_<UniteIShapes>(m, "UniteIShapes", "Unite shapes.")
    .def(nb::init<const IShape&, const IShape&>(), nb::arg("target"), nb::arg("tool"), "Unite the target and tool.")
    .def(nb::init<const IShape&, const std::vector<IShape>&>(), nb::arg("target"), nb::arg("tools"), "Unite the target with the tools.")
    .def(nb::init<const std::vector<IShape>&, const IShape&>(), nb::arg("targets"), nb::arg("tool"), "Unite the targets with the tool.")
    .def(nb::init<const std::vector<IShape>&, const std::vector<IShape>&>(), nb::arg("targets"), nb::arg("tools"), "Unite the targets with the tools.")

    .def("IntersectionEdges", &UniteIShapes::IntersectionEdges, "Get the intersection edges.");

  // MakeShape methods
  bind_MakeShape<UniteIShapes>(cls);
}
