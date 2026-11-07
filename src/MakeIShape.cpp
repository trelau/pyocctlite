#include "MakeIShape.hpp"

#include "IErrors.hpp"

void MakeIShape::CheckBuilt() {
  if (!Tool().IsDone()) {
    Tool().Build();
  }
  if (!Tool().IsDone()) {
    throw IBuildFailed("Operation failed to build.");
  }
}

IShape MakeIShape::Shape() {
  CheckBuilt();
  return IShape(Tool().Shape());
}

bool MakeIShape::IsDeleted(const IShape& shape) {
  CheckBuilt();
  return Tool().IsDeleted(shape);
}

std::vector<IShape> MakeIShape::GeneratedShapes(const IShape& shape) {
  CheckBuilt();
  return IShape::MakeByList(Tool().Generated(shape));
}

std::vector<IShape> MakeIShape::ModifiedShapes(const IShape& shape) {
  CheckBuilt();
  return IShape::MakeByList(Tool().Modified(shape));
}

// Python bindings
void bind_MakeIShape(nb::module_& m) {

  nb::class_<MakeIShape>(m, "MakeIShape", "Base class for tools that make a shape.")
      .def("Build", &MakeIShape::Build, "Execute the operation.")
      .def("IsDone", &MakeIShape::IsDone, "Check if the operation completed successfully.")
      .def("Shape", &MakeIShape::Shape, "Get the resulting shape, building if needed.")
      .def("IsDeleted", &MakeIShape::IsDeleted, nb::arg("shape"),
           "Check if the given input shape was deleted by this operation.")
      .def("GeneratedShapes", &MakeIShape::GeneratedShapes, nb::arg("shape"),
           "Get shapes generated from the given input shape.")
      .def("ModifiedShapes", &MakeIShape::ModifiedShapes, nb::arg("shape"),
           "Get shapes modified from the given input shape.");
}
