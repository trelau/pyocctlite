#include "CutIShapes.hpp"

#include <NCollection_List.hxx>
#include <TopoDS_Shape.hxx>

CutIShapes::CutIShapes(const IShape& target, const std::vector<IShape>& tools) {

  NCollection_List<TopoDS_Shape> oTargets;
  oTargets.Append(target);
  tool_.SetArguments(oTargets);

  NCollection_List<TopoDS_Shape> oTools;
  for (const IShape& s : tools) {
    oTools.Append(s);
  }
  tool_.SetTools(oTools);
  tool_.Build();
}

CutIShapes::CutIShapes(const std::vector<IShape>& targets, const IShape& tool) {

  NCollection_List<TopoDS_Shape> oTargets;
  for (const IShape& s : targets) {
    oTargets.Append(s);
  }
  tool_.SetArguments(oTargets);

  NCollection_List<TopoDS_Shape> oTools;
  oTools.Append(tool);
  tool_.SetTools(oTools);
  tool_.Build();
}

CutIShapes::CutIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools) {

  NCollection_List<TopoDS_Shape> oTargets;
  for (const IShape& s : targets) {
    oTargets.Append(s);
  }
  tool_.SetArguments(oTargets);

  NCollection_List<TopoDS_Shape> oTools;
  for (const IShape& s : tools) {
    oTools.Append(s);
  }
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
void bind_CutIShapes(nb::module_& m) {

  auto cls =
      nb::class_<CutIShapes>(m, "CutIShapes", "Cut shapes (boolean subtraction).")
          .def(nb::init<const IShape&, const IShape&>(), nb::arg("target"), nb::arg("tool"),
               "Cut the tool from the target.")
          .def(nb::init<const IShape&, const std::vector<IShape>&>(), nb::arg("target"),
               nb::arg("tools"), "Cut the tools from the target.")
          .def(nb::init<const std::vector<IShape>&, const IShape&>(), nb::arg("targets"),
               nb::arg("tool"), "Cut the tool from the targets.")
          .def(nb::init<const std::vector<IShape>&, const std::vector<IShape>&>(),
               nb::arg("targets"), nb::arg("tools"), "Cut the tools from the targets.")

          .def("IntersectionEdges", &CutIShapes::IntersectionEdges, "Get the intersection edges.");

  // MakeShape methods
  bind_MakeShape<CutIShapes>(cls);
}
