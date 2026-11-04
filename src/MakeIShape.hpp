#pragma once

#include "occtlite.hpp"

#include <TopTools_ListOfShape.hxx>

#include "IErrors.hpp"
#include "IShape.hpp"

// Common methods for derived tools of OCCT BRepBuilderAPI_MakeShape
#define MAKE_SHAPE_METHODS(tool_)                                              \
  void Build() {                                                               \
    (tool_).Build();                                                           \
  }                                                                            \
                                                                               \
  bool IsDone() const {                                                        \
    return (tool_).IsDone();                                                   \
  }                                                                            \
                                                                               \
  void CheckBuilt() {                                                          \
    if (!(tool_).IsDone()) { (tool_).Build(); }                                \
    if (!(tool_).IsDone()) { throw IBuildFailed("Operation failed to build."); } \
  }                                                                            \
                                                                               \
  IShape Shape() {                                                             \
    CheckBuilt();                                                              \
    TopoDS_Shape result = (tool_).Shape();                                     \
    return IShape(result);                                                     \
  }                                                                            \
                                                                               \
  bool IsDeleted(const IShape& shape) {                                        \
    CheckBuilt();                                                              \
    return (tool_).IsDeleted(shape);                                           \
  }                                                                            \
                                                                               \
  std::vector<IShape> GeneratedShapes(const IShape& shape) {                   \
    CheckBuilt();                                                              \
    TopTools_ListOfShape generated = (tool_).Generated(shape);                 \
    return IShape::MakeByList(generated);                                      \
  }                                                                            \
                                                                               \
  std::vector<IShape> ModifiedShapes(const IShape& shape) {                    \
    CheckBuilt();                                                              \
    TopTools_ListOfShape modified = (tool_).Modified(shape);                   \
    return IShape::MakeByList(modified);                                       \
  }

// Common bindings for derived tools of OCCT BRepBuilderAPI_MakeShape
template <typename T>
void bind_MakeShape(nb::class_<T>& cls)
{
  cls.def("Build", &T::Build, "Execute the operation.");
  cls.def("IsDone", &T::IsDone, "Check if the operation completed successfully.");
  cls.def("Shape", &T::Shape, "Get the resulting shape, building if needed.");
  cls.def("IsDeleted", &T::IsDeleted, nb::arg("shape"), "Check if the given input shape was deleted by this operation.");
  cls.def("GeneratedShapes", &T::GeneratedShapes, nb::arg("shape"), "Get shapes generated from the given input shape.");
  cls.def("ModifiedShapes", &T::ModifiedShapes, nb::arg("shape"), "Get shapes modified from the given input shape.");
}
