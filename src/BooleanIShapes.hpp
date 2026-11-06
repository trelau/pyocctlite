#pragma once

#include "occtlite.hpp"

#include <BRepAlgoAPI_Common.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <NCollection_List.hxx>
#include <TopoDS_Shape.hxx>

#include "IShape.hpp"
#include "MakeIShape.hpp"

// Tool for a boolean operation, instantiated once per OCCT operation
template <typename Tool> class BooleanIShapes {
public:
  // Apply the operation between the targets and the tools
  BooleanIShapes(const std::vector<IShape>& targets, const std::vector<IShape>& tools,
                 double tol = 0.0) {
    tool_.SetArguments(ToList(targets));
    tool_.SetTools(ToList(tools));
    tool_.SetFuzzyValue(tol);
    tool_.Build();
  }

  MAKE_SHAPE_METHODS(tool_);

  // Get the edges where the surfaces of the targets and tools intersect
  std::vector<IShape> IntersectionEdges() { return IShape::MakeByList(tool_.SectionEdges()); }

private:
  static NCollection_List<TopoDS_Shape> ToList(const std::vector<IShape>& shapes) {
    NCollection_List<TopoDS_Shape> list;
    for (const IShape& s : shapes) {
      list.Append(s);
    }
    return list;
  }

  Tool tool_;
};

using UniteIShapes = BooleanIShapes<BRepAlgoAPI_Fuse>;
using CutIShapes = BooleanIShapes<BRepAlgoAPI_Cut>;
using IntersectIShapes = BooleanIShapes<BRepAlgoAPI_Common>;

// Python bindings
void bind_BooleanIShapes(nb::module_& m);
