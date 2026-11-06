#pragma once

#include "occtlite.hpp"

#include <stdexcept>
#include <string>

// Exception for an object of the wrong kind (bound as a TypeError subclass)
class IKindMismatch : public std::runtime_error {
public:
  explicit IKindMismatch(const std::string& msg) : std::runtime_error(msg) {}
};

// Exception for a tool that failed to build (bound as a RuntimeError subclass)
class IBuildFailed : public std::runtime_error {
public:
  explicit IBuildFailed(const std::string& msg) : std::runtime_error(msg) {}
};

// Python bindings
inline void bind_IErrors(nb::module_& m) {

  nb::exception<IKindMismatch>(m, "KindMismatch", PyExc_TypeError);
  nb::exception<IBuildFailed>(m, "BuildFailed", PyExc_RuntimeError);
}
