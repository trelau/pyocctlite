from __future__ import annotations

from pyocctlite._occtlite import (ICurve, ICurve2D, ICurve2DKind, ICurveKind, IFrame, IFrame2D,
                                  IPoint, IPoint2D, ISurface, ISurfaceKind, ITransform, IVector,
                                  IVector2D)

__all__ = ['Point2D', 'Point', 'Vector2D', 'Vector', 'Frame2D', 'Frame', 'Transform', 'Curve',
           'Curve2D', 'Line', 'Circle', 'TrimmedCurve', 'Surface', 'CylindricalSurface',
           'Ellipse2D', 'TrimmedCurve2D']


class Point2D:

    @classmethod
    def by_xy(cls, x: float, y: float) -> Point2D:
        return cls(IPoint2D(x, y))

    def __init__(self, p: IPoint2D):
        assert isinstance(p, IPoint2D)
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint2D:
        return self._ipoint


class Vector2D:

    @classmethod
    def by_xy(cls, x: float, y: float) -> Vector2D:
        return cls(IVector2D(x, y))

    def __init__(self, v: IVector2D):
        assert isinstance(v, IVector2D)
        self._ivector = v

    @property
    def ivector(self) -> IVector2D:
        return self._ivector

    def scaled(self, scale: float) -> Vector2D:
        return Vector2D(self.ivector.scaled(scale))


class Frame2D:

    @classmethod
    def by_origin(cls, origin: Point2D) -> Frame2D:
        iframe = IFrame2D.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vector(cls, origin: Point2D, xvec: Vector2D) -> Frame2D:
        iframe = IFrame2D.MakeByVector(origin.ipoint, xvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame2D):
        assert isinstance(f, IFrame2D)
        self._iframe = f

    @property
    def iframe(self) -> IFrame2D:
        return self._iframe

    @property
    def x_direction(self) -> Vector2D:
        return Vector2D(self.iframe.XDirection())

    @property
    def y_direction(self) -> Vector2D:
        return Vector2D(self.iframe.YDirection())


class Curve2D:

    def __init__(self, c: ICurve2D):
        assert isinstance(c, ICurve2D)
        self._icurve = c

    @property
    def icurve(self) -> ICurve2D:
        return self._icurve

    def evaluate(self, u) -> Point2D:
        ipoint = self.icurve.Evaluate(u)
        return Point2D(ipoint)


class Ellipse2D(Curve2D):

    @classmethod
    def by_radii(cls, frame: Frame2D, rmajor: float, rminor: float):
        icurve = ICurve2D.MakeEllipse(frame.iframe, rmajor, rminor)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        super().__init__(c)
        assert c.Kind() == ICurve2DKind.Ellipse


class TrimmedCurve2D(Curve2D):

    @classmethod
    def by_curve(cls, curve: Curve2D, u0: float, u1: float) -> TrimmedCurve2D:
        icurve = ICurve2D.MakeTrimmed(curve.icurve, u0, u1)
        return TrimmedCurve2D(icurve)

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> TrimmedCurve2D:
        icurve = ICurve2D.MakeTrimmed(p1.ipoint, p2.ipoint)
        return TrimmedCurve2D(icurve)

    def __init__(self, c: ICurve2D):
        super().__init__(c)
        assert c.Kind() == ICurve2DKind.Trimmed


class Point:

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Point:
        return cls(IPoint(x, y, z))

    def __init__(self, p: IPoint):
        assert isinstance(p, IPoint)
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint:
        return self._ipoint


class Vector:

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Vector:
        return cls(IVector(x, y, z))

    def __init__(self, v: IVector):
        assert isinstance(v, IVector)
        self._ivector = v

    @property
    def ivector(self) -> IVector:
        return self._ivector

    def scaled(self, scale: float) -> Vector:
        return Vector(self.ivector.Scaled(scale))


class Frame:

    @classmethod
    def by_origin(cls, origin: Point) -> Frame:
        iframe = IFrame.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    def __init__(self, f: IFrame):
        assert isinstance(f, IFrame)
        self._iframe = f

    @property
    def iframe(self) -> IFrame:
        return self._iframe

    @property
    def x_direction(self) -> Vector:
        return Vector(self.iframe.XDirection())

    @property
    def y_direction(self) -> Vector:
        return Vector(self.iframe.YDirection())

    @property
    def z_direction(self) -> Vector:
        return Vector(self.iframe.ZDirection())


class Transform:

    @classmethod
    def mirror(cls, origin: Point, normal: Vector) -> Transform:
        itransform = ITransform.MakeMirror(origin.ipoint, normal.ivector)
        return cls(itransform)

    def __init__(self, t: ITransform):
        assert isinstance(t, ITransform)
        self._itransform = t

    @property
    def itransform(self) -> ITransform:
        return self._itransform


class Curve:

    def __init__(self, c: ICurve):
        assert isinstance(c, ICurve)
        self._icurve = c

    @property
    def icurve(self) -> ICurve:
        return self._icurve

    def evaluate(self, u) -> Point:
        ipoint = self.icurve.Evaluate(u)
        return Point(ipoint)


class Line(Curve):

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Line:
        icurve = ICurve.MakeLine(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        super().__init__(c)
        assert c.Kind() == ICurveKind.Line


class Circle(Curve):

    @classmethod
    def by_radius(cls, frame: Frame, radius: float) -> Circle:
        icurve = ICurve.MakeCircle(frame.iframe, radius)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point, p2: Point, p3: Point) -> Circle:
        icurve = ICurve.MakeCircle(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        super().__init__(c)
        assert c.Kind() == ICurveKind.Circle

    @property
    def radius(self) -> float:
        return self.icurve.Radius()


class TrimmedCurve(Curve):

    @classmethod
    def by_circular_arc(cls, p1: Point, p2: Point, p3: Point) -> TrimmedCurve:
        icurve = ICurve.MakeCircularArc(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        super().__init__(c)
        assert c.Kind() == ICurveKind.Trimmed


class Surface:

    def __init__(self, s: ISurface):
        assert isinstance(s, ISurface)
        self._isurface = s

    @property
    def isurface(self) -> ISurface:
        return self._isurface


class CylindricalSurface(Surface):

    @classmethod
    def by_radius(cls, frame: Frame, radius: float) -> CylindricalSurface:
        isurface = ISurface.MakeCylindrical(frame.iframe, radius)
        return cls(isurface)

    def __init__(self, s: ISurface):
        super().__init__(s)
        assert s.Kind() == ISurfaceKind.Cylindrical
