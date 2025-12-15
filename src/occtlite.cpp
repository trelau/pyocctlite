#include "occtlite.hpp"

#include "IPoint2D.hpp"
#include "IVector2D.hpp"
#include "IFrame2D.hpp"
#include "ICurve2D.hpp"

#include "IPoint.hpp"
#include "IVector.hpp"
#include "IFrame.hpp"
#include "ITransform.hpp"
#include "ICurve.hpp"
#include "ISurface.hpp"
#include "ProjectIPointToICurve.hpp"

#include "IShape.hpp"
#include "CopyIShape.hpp"
#include "ExploreIShape.hpp"
#include "MapIShape.hpp"
#include "ExtrudeIShape.hpp"
#include "TransformIShape.hpp"
#include "FilletIShape.hpp"
#include "UniteIShapes.hpp"
#include "ThickenIShape.hpp"
#include "LoftIShape.hpp"
#include "IShapeErrors.hpp"

#include "IMesh.hpp"
#include "IMeshControl.hpp"
#include "IMeshErrors.hpp"

PYBIND11_MODULE(_occtlite, m) {

  bind_IPoint2D(m);
  bind_IVector2D(m);
  bind_IFrame2D(m);
  bind_ICurve2D(m);

  bind_IPoint(m);
  bind_IVector(m);
  bind_IFrame(m);
  bind_ITransform(m);
  bind_ICurve(m);
  bind_ISurface(m);
  bind_ProjectIPointToICurve(m);

  bind_IShape(m);
  bind_CopyIShape(m);
  bind_ExploreIShape(m);
  bind_MapIShape(m);
  bind_ExtrudeIShape(m);
  bind_TransformIShape(m);
  bind_FilletIShape(m);
  bind_UniteIShapes(m);
  bind_ThickenIShape(m);
  bind_LoftIShape(m);
  bind_IShapeErrors(m);

  bind_IMeshControl(m);
  bind_IMesh(m);
  bind_IMeshErrors(m);

}