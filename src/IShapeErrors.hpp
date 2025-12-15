#pragma once

#include "occtlite.hpp"

#include <stdexcept>
#include <string>

// Exception for shape type mismatches
class IShapeTypeMismatch : public std::runtime_error {
public:
  explicit IShapeTypeMismatch(const std::string& msg)
    : std::runtime_error(msg) {}
};

// Python bindings
inline void bind_IShapeErrors(py::module& m) {

  py::register_exception<IShapeTypeMismatch>(m, "IShapeTypeMismatch");

}