#include "occtlite.hpp"

#include "ICurve2D.hpp"
#include "IFrame2D.hpp"
#include "IPoint2D.hpp"
#include "IVector2D.hpp"

#include "IAxis.hpp"
#include "IBoundingBox.hpp"
#include "ICurve.hpp"
#include "ICurveData.hpp"
#include "IFrame.hpp"
#include "IPoint.hpp"
#include "ISurface.hpp"
#include "ITransform.hpp"
#include "IVector.hpp"
#include "ProjectIPointToICurve.hpp"

#include "BooleanIShapes.hpp"
#include "ChamferIShape.hpp"
#include "CopyIShape.hpp"
#include "ExploreIShape.hpp"
#include "ExtrudeIShape.hpp"
#include "FilletIShape.hpp"
#include "IErrors.hpp"
#include "IShape.hpp"
#include "LoftIShape.hpp"
#include "MapIShape.hpp"
#include "RevolveIShape.hpp"
#include "ThickenIShape.hpp"
#include "TransformIShape.hpp"

NB_MODULE(_occtlite, m) {

  bind_IPoint2D(m);
  bind_IVector2D(m);
  bind_IFrame2D(m);
  bind_ICurve2D(m);

  bind_IPoint(m);
  bind_IVector(m);
  bind_IAxis(m);
  bind_IBoundingBox(m);
  bind_IFrame(m);
  bind_ITransform(m);
  bind_ICurve(m);
  bind_ICurveData(m);
  bind_ISurface(m);
  bind_ProjectIPointToICurve(m);

  bind_IShape(m);
  bind_CopyIShape(m);
  bind_ExploreIShape(m);
  bind_MapIShape(m);
  bind_ExtrudeIShape(m);
  bind_RevolveIShape(m);
  bind_TransformIShape(m);
  bind_FilletIShape(m);
  bind_ChamferIShape(m);
  bind_BooleanIShapes(m);
  bind_ThickenIShape(m);
  bind_LoftIShape(m);
  bind_IErrors(m);
}