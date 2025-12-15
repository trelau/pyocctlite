#pragma once

#include <memory>
#include <string>
#include <vector>

#include "IShape.hpp"
#include "IMeshControl.hpp"
#include "IMeshErrors.hpp"

#include <TopoDS_Shape.hxx>
#include <SMESH_Gen.hxx>
#include <SMESH_Mesh.hxx>
#include <SMESH_Hypothesis.hxx>

// Interface class for a mesh
class IMesh {
public:

  // Factory method to create a mesh from a shape and mesh controls
  static IMesh MakeMesh(const IShape& shape, const IMeshControl& globalControl, const std::vector<IMeshControl>& localControls = {});

  // Basic mesh queries
  int NumNodes() const;
  int NumEdges() const;
  int NumFaces() const;
  int NumTriangles() const;
  int NumQuadrangles() const;
  int NumTetras() const;

  // Export
  void ExportUNV(const std::string& path) const;

private:
  // Internal state owning all SMESH objects for safe lifetime management
  struct State {
    std::unique_ptr<SMESH_Gen> gen_ = std::make_unique<SMESH_Gen>();
    std::unique_ptr<SMESH_Mesh> mesh_{ gen_->CreateMesh(true) };
    std::vector<std::unique_ptr<SMESH_Hypothesis>> owned_;
    TopoDS_Shape shape_;
  };

  // Constructor from state
  explicit IMesh(std::shared_ptr<State> state) : state_(std::move(state)) {}

  // Shared pointer to internal state
  std::shared_ptr<State> state_;
};

// Python bindings
void bind_IMesh(pybind11::module& m);