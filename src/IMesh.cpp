#include "IMesh.hpp"

#include <type_traits>

#include <TopoDS_Shape.hxx>

#include <NETGENPlugin_SimpleHypothesis_3D.hxx>
#include <NETGENPlugin_NETGEN_2D3D.hxx>
#include <NETGENPlugin_SimpleHypothesis_2D.hxx>
#include <NETGENPlugin_NETGEN_2D.hxx>
#include <StdMeshers_LocalLength.hxx>
#include <StdMeshers_Regular_1D.hxx>

IMesh IMesh::MakeMesh(const IShape& shape, const IMeshControl& globalControl, const std::vector<IMeshControl>& localControls)
{
  auto state = std::make_shared<State>();

  // Set shape to mesh
  state->shape_ = static_cast<const TopoDS_Shape&>(shape);
  state->mesh_->ShapeToMesh(state->shape_);

  // Global unique hypothesis/algorithm IDs
  int nextId = 0;

  // Own helper to keep created hypotheses/algorithms alive
  auto own = [&](auto* p)
  {
    using T = std::remove_pointer_t<decltype(p)>;
    T* raw = p;
    state->owned_.emplace_back(std::unique_ptr<T>(p));
    return raw;
  };

  // Helper to apply 1D controls
  auto apply1D = [&](const TopoDS_Shape& target, const IMeshControl& c)
  {
    // 1D  size hypothesis
    auto hyp = own(new StdMeshers_LocalLength(nextId++, state->gen_.get()));
    if (c.EdgeSize()) {
      hyp->SetLength(*c.EdgeSize());
    }
    // TODO 1D deflection hypothesis

    // 1D meshing algorithm
    auto algo = own(new StdMeshers_Regular_1D(nextId++, state->gen_.get()));

    state->mesh_->AddHypothesis(target, hyp->GetID());
    state->mesh_->AddHypothesis(target, algo->GetID());
  };

  // Helper to apply 2D controls
  auto apply2D = [&](const TopoDS_Shape& target, const IMeshControl& c)
  {
    // 2D size hypothesis
    auto hyp = own(new NETGENPlugin_SimpleHypothesis_2D(nextId++, state->gen_.get()));
    if (c.EdgeSize()) {
      hyp->SetLocalLength(*c.EdgeSize());
    }

    // 2D allow quads
    hyp->SetAllowQuadrangles(c.AllowQuads());

    // TODO 2D deflection hypothesis

    // 2D meshing algorithm
    auto algo = own(new NETGENPlugin_NETGEN_2D(nextId++, state->gen_.get()));

    state->mesh_->AddHypothesis(target, hyp->GetID());
    state->mesh_->AddHypothesis(target, algo->GetID());
  };

  // Helper to apply 3D controls
  auto apply3D = [&](const TopoDS_Shape& target, const IMeshControl& c)
  {
    // 3D size hypothesis
    auto hyp = own(new NETGENPlugin_SimpleHypothesis_3D(nextId++, state->gen_.get()));
    if (c.EdgeSize()) {
      hyp->SetLocalLength(*c.EdgeSize());
    }

    // TODO 3D deflection hypothesis

    // 3D meshing algorithm
    auto algo = own(new NETGENPlugin_NETGEN_2D3D(nextId++, state->gen_.get()));

    state->mesh_->AddHypothesis(target, hyp->GetID());
    state->mesh_->AddHypothesis(target, algo->GetID());
  };


  // Helper to apply a control based on its dimension
  auto applyControl = [&](const IMeshControl& c)
  {
    const TopoDS_Shape& target = static_cast<const TopoDS_Shape&>(c.Shape());

    switch (c.Dimension()) {
    case 1: apply1D(target, c); break;
    case 2: apply2D(target, c); break;
    case 3: apply3D(target, c); break;
    default:
      throw IMeshControlError("Unsupported mesh control dimension: " + std::to_string(c.Dimension()));
    }
  };

  // Apply controls
  applyControl(globalControl);
  for (const auto& c : localControls) {
    applyControl(c);
  }

  // Compute mesh
  const bool ok = state->gen_->Compute(*state->mesh_, state->shape_);
  if (!ok) {
    throw IMeshComputeError("Mesh computation failed.");
  }

  return IMesh(state);
}

int IMesh::NumNodes() const { return state_->mesh_->NbNodes(); }
int IMesh::NumEdges() const { return state_->mesh_->NbEdges(); }
int IMesh::NumFaces() const { return state_->mesh_->NbFaces(); }
int IMesh::NumTriangles() const { return state_->mesh_->NbTriangles(); }
int IMesh::NumQuadrangles() const { return state_->mesh_->NbQuadrangles(); }
int IMesh::NumTetras() const { return state_->mesh_->NbTetras(); }

void IMesh::ExportUNV(const std::string& path) const
{
  state_->mesh_->ExportUNV(path.c_str());
}

// Python bindings
void bind_IMesh(pybind11::module& m)
{
  using namespace pybind11;
  class_<IMesh>(m, "IMesh", "A Mesh.")
    .def_static("MakeMesh", &IMesh::MakeMesh, arg("shape"), arg("global"), arg("locals") = std::vector<IMeshControl>(), "Make a mesh from a shape and mesh controls.")

    .def("NumNodes", &IMesh::NumNodes, "Get the number of nodes in the mesh.")
    .def("NumEdges", &IMesh::NumEdges, "Get the number of edges in the mesh.")
    .def("NumFaces", &IMesh::NumFaces, "Get the number of faces in the mesh.")
    .def("NumTriangles", &IMesh::NumTriangles, "Get the number of triangles in the mesh.")
    .def("NumQuadrangles", &IMesh::NumQuadrangles, "Get the number of quadrangles in the mesh.")
    .def("NumTetras", &IMesh::NumTetras, "Get the number of tetrahedra in the mesh.")
    .def("ExportUNV", &IMesh::ExportUNV, arg("path"), "Export the mesh to a UNV file.");

}