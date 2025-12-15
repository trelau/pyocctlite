#pragma once

#include "occtlite.hpp"

#include <stdexcept>
#include <string>

class IMeshControlError : public std::runtime_error {
public:
  explicit IMeshControlError(const std::string& msg)
    : std::runtime_error(msg) {}
};

class IMeshComputeError : public std::runtime_error {
public:
  explicit IMeshComputeError(const std::string& msg)
    : std::runtime_error(msg) {}
};

// Python bindings
inline void bind_IMeshErrors(py::module& m) {

  py::register_exception<IMeshControlError>(m, "IMeshControlError");
  py::register_exception<IMeshComputeError>(m, "IMeshComputeError");

}