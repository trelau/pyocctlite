from __future__ import annotations

from functools import cached_property
from typing import Optional

from pyocctlite._occtlite import (IAxis, ICurve, ICurve2D, ICurve2DKind, ICurveKind, IFrame,
                                  IFrame2D, IPoint, IPoint2D, ISurface, ISurfaceKind, ITransform,
                                  IVector, IVector2D)


class Point2D:
    """
    Represents a 2D point.

    :ivar IPoint2D ipoint: Underlying 2D point.
    """

    @classmethod
    def by_xy(cls, x: float, y: float) -> Point2D:
        """
        Create a 2D point from coordinates.

        :param float x: X coordinate.
        :param float y: Y coordinate.
        :return: New 2D point.
        :rtype: Point2D
        """
        return cls(IPoint2D.MakeByXY(x, y))

    def __init__(self, p: IPoint2D):
        """
        Initialize from an IPoint2D.

        :param IPoint2D p: Underlying 2D point.
        """
        if not isinstance(p, IPoint2D):
            raise TypeError(f'Expected IPoint2D, got {type(p).__name__}.')
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint2D:
        """
        Underlying 2D point.

        :return: IPoint2D object.
        :rtype: IPoint2D
        """
        return self._ipoint

    @property
    def x(self) -> float:
        """
        X coordinate.

        :return: X value.
        :rtype: float
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        Y coordinate.

        :return: Y value.
        :rtype: float
        """
        return self.ipoint.Y()

    def is_equal(self, other: Point2D, tol: float = 1.0e-7) -> bool:
        """
        Check if this point is equal to another within a tolerance.

        :param Point2D other: Other point.
        :param float tol: Distance tolerance.
        :return: True if the points are within the tolerance.
        :rtype: bool
        """
        return self.ipoint.IsEqual(other.ipoint, tol)


class Vector2D:
    """
    Represents a 2D vector.

    :ivar IVector2D ivector: Underlying 2D vector.
    """

    @classmethod
    def by_xy(cls, x: float, y: float) -> Vector2D:
        """
        Create a 2D vector from components.

        :param float x: X component.
        :param float y: Y component.
        :return: New 2D vector.
        :rtype: Vector2D
        """
        return cls(IVector2D.MakeByXY(x, y))

    def __init__(self, v: IVector2D):
        """
        Initialize from an IVector2D.

        :param IVector2D v: Underlying 2D vector.
        """
        if not isinstance(v, IVector2D):
            raise TypeError(f'Expected IVector2D, got {type(v).__name__}.')
        self._ivector = v

    @property
    def ivector(self) -> IVector2D:
        """
        Underlying 2D vector.

        :return: IVector2D object.
        :rtype: IVector2D
        """
        return self._ivector

    @property
    def x(self) -> float:
        """
        X component.

        :return: X value.
        :rtype: float
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        Y component.

        :return: Y value.
        :rtype: float
        """
        return self.ivector.Y()

    @property
    def magnitude(self) -> float:
        """
        Magnitude of the vector.

        :return: Magnitude.
        :rtype: float
        """
        return self.ivector.Magnitude()

    def scaled(self, scale: float) -> Vector2D:
        """
        Create a scaled version of this vector.

        :param float scale: Scale factor.
        :return: Scaled vector.
        :rtype: Vector2D
        """
        return Vector2D(self.ivector.Scaled(scale))


class Frame2D:
    """
    Represents a 2D coordinate system.

    :ivar IFrame2D iframe: Underlying 2D frame.
    """

    @classmethod
    def by_origin(cls, origin: Point2D) -> Frame2D:
        """
        Create a 2D frame from an origin.

        :param Point2D origin: Origin point.
        :return: New 2D frame.
        :rtype: Frame2D
        """
        iframe = IFrame2D.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vector(cls, origin: Point2D, xvec: Vector2D) -> Frame2D:
        """
        Create a 2D frame from origin and X direction.

        :param Point2D origin: Origin point.
        :param Vector2D xvec: X direction vector.
        :return: New 2D frame.
        :rtype: Frame2D
        """
        iframe = IFrame2D.MakeByVector(origin.ipoint, xvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame2D):
        """
        Initialize from an IFrame2D.

        :param IFrame2D f: Underlying 2D frame.
        """
        if not isinstance(f, IFrame2D):
            raise TypeError(f'Expected IFrame2D, got {type(f).__name__}.')
        self._iframe = f

    @property
    def iframe(self) -> IFrame2D:
        """
        Underlying 2D frame.

        :return: IFrame2D object.
        :rtype: IFrame2D
        """
        return self._iframe

    @cached_property
    def x_direction(self) -> Vector2D:
        """
        X direction vector.

        :return: X direction.
        :rtype: Vector2D
        """
        return Vector2D(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector2D:
        """
        Y direction vector.

        :return: Y direction.
        :rtype: Vector2D
        """
        return Vector2D(self.iframe.YDirection())


class Curve2D:
    """
    Base class for 2D curves.

    :ivar ICurve2D icurve: Underlying 2D curve.
    """

    @staticmethod
    def by_icurve2d(icurve: ICurve2D) -> Curve2D:
        """
        Create a 2D curve from an ICurve2D.

        :param ICurve2D icurve: Underlying 2D curve.
        :return: The 2D curve.
        :rtype: Curve2D
        """
        match icurve.Kind():
            case ICurve2DKind.Ellipse:
                return Ellipse2D(icurve)
            case ICurve2DKind.Trimmed:
                return TrimmedCurve2D(icurve)
            case _:
                raise NotImplementedError(f'Unsupported 2D curve kind: {icurve.Kind()}.')

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        if not isinstance(c, ICurve2D):
            raise TypeError(f'Expected ICurve2D, got {type(c).__name__}.')
        self._icurve = c

    @property
    def icurve(self) -> ICurve2D:
        """
        Underlying 2D curve.

        :return: ICurve2D object.
        :rtype: ICurve2D
        """
        return self._icurve

    def evaluate(self, u: float) -> Point2D:
        """
        Evaluate the curve at a parameter.

        :param float u: Parameter value.
        :return: Evaluated point.
        :rtype: Point2D
        """
        ipoint = self.icurve.Evaluate(u)
        return Point2D(ipoint)


class Ellipse2D(Curve2D):
    """
    Represents a 2D ellipse.
    """

    @classmethod
    def by_radii(cls, rmajor: float, rminor: float, frame: Optional[Frame2D] = None) -> Ellipse2D:
        """
        Create an ellipse from radii and frame.

        :param float rmajor: Major radius.
        :param float rminor: Minor radius.
        :param Optional[Frame2D] frame: Coordinate system. Defaults to the global origin.
        :return: New 2D ellipse.
        :rtype: Ellipse2D
        """
        if frame is None:
            frame = Frame2D.by_origin(Point2D.by_xy(0., 0.))

        icurve = ICurve2D.MakeEllipse(frame.iframe, rmajor, rminor)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Ellipse:
            raise TypeError(f'Expected ICurve2DKind.Ellipse, got {c.Kind()}.')


class TrimmedCurve2D(Curve2D):
    """
    Represents a trimmed 2D curve.
    """

    @classmethod
    def by_curve(cls, curve: Curve2D, u0: float, u1: float) -> TrimmedCurve2D:
        """
        Trim a curve between parameters.

        :param Curve2D curve: Curve to trim.
        :param float u0: Start parameter.
        :param float u1: End parameter.
        :return: New trimmed curve.
        :rtype: TrimmedCurve2D
        """
        icurve = ICurve2D.MakeTrimmed(curve.icurve, u0, u1)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> TrimmedCurve2D:
        """
        Create a line segment between points.

        :param Point2D p1: Start point.
        :param Point2D p2: End point.
        :return: New trimmed curve.
        :rtype: TrimmedCurve2D
        """
        icurve = ICurve2D.MakeTrimmed(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Trimmed:
            raise TypeError(f'Expected ICurve2DKind.Trimmed, got {c.Kind()}.')


class Point:
    """
    Represents a 3D point.

    :ivar IPoint ipoint: Underlying 3D point.
    """

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Point:
        """
        Create a 3D point from coordinates.

        :param float x: X coordinate.
        :param float y: Y coordinate.
        :param float z: Z coordinate.
        :return: New 3D point.
        :rtype: Point
        """
        return cls(IPoint.MakeByXYZ(x, y, z))

    def __init__(self, p: IPoint):
        """
        Initialize from an IPoint.

        :param IPoint p: Underlying 3D point.
        """
        if not isinstance(p, IPoint):
            raise TypeError(f'Expected IPoint, got {type(p).__name__}.')
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint:
        """
        Underlying 3D point.

        :return: IPoint object.
        :rtype: IPoint
        """
        return self._ipoint

    @property
    def x(self) -> float:
        """
        X coordinate.

        :return: X value.
        :rtype: float
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        Y coordinate.

        :return: Y value.
        :rtype: float
        """
        return self.ipoint.Y()

    @property
    def z(self) -> float:
        """
        Z coordinate.

        :return: Z value.
        :rtype: float
        """
        return self.ipoint.Z()

    def is_equal(self, other: Point, tol: float = 1.0e-7) -> bool:
        """
        Check if this point is equal to another within a tolerance.

        :param Point other: Other point.
        :param float tol: Distance tolerance.
        :return: True if the points are within the tolerance.
        :rtype: bool
        """
        return self.ipoint.IsEqual(other.ipoint, tol)


class Vector:
    """
    Represents a 3D vector.

    :ivar IVector ivector: Underlying 3D vector.
    """

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Vector:
        """
        Create a 3D vector from components.

        :param float x: X component.
        :param float y: Y component.
        :param float z: Z component.
        :return: New 3D vector.
        :rtype: Vector
        """
        return cls(IVector.MakeByXYZ(x, y, z))

    def __init__(self, v: IVector):
        """
        Initialize from an IVector.

        :param IVector v: Underlying 3D vector.
        """
        if not isinstance(v, IVector):
            raise TypeError(f'Expected IVector, got {type(v).__name__}.')
        self._ivector = v

    @property
    def ivector(self) -> IVector:
        """
        Underlying 3D vector.

        :return: IVector object.
        :rtype: IVector
        """
        return self._ivector

    @property
    def x(self) -> float:
        """
        X component.

        :return: X value.
        :rtype: float
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        Y component.

        :return: Y value.
        :rtype: float
        """
        return self.ivector.Y()

    @property
    def z(self) -> float:
        """
        Z component.

        :return: Z value.
        :rtype: float
        """
        return self.ivector.Z()

    @property
    def magnitude(self) -> float:
        """
        Magnitude of the vector.

        :return: Magnitude.
        :rtype: float
        """
        return self.ivector.Magnitude()

    def scaled(self, scale: float) -> Vector:
        """
        Create a scaled version of this vector.

        :param float scale: Scale factor.
        :return: Scaled vector.
        :rtype: Vector
        """
        return Vector(self.ivector.Scaled(scale))


class Axis:
    """
    Represents a 3D axis.

    :ivar IAxis iaxis: Underlying 3D axis.
    """

    def __init__(self, a: IAxis):
        """
        Initialize from an IAxis.

        :param IAxis a: Underlying 3D axis.
        """
        if not isinstance(a, IAxis):
            raise TypeError(f'Expected IAxis, got {type(a).__name__}.')
        self._iaxis = a

    @property
    def iaxis(self) -> IAxis:
        """
        Underlying 3D axis.

        :return: IAxis object.
        :rtype: IAxis
        """
        return self._iaxis

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the axis.

        :return: Origin of the axis.
        :rtype: Point
        """
        return Point(self.iaxis.Origin())

    @cached_property
    def direction(self) -> Vector:
        """
        Direction of the axis.

        :return: Direction of the axis.
        :rtype: Vector
        """
        return Vector(self.iaxis.Direction())


class Frame:
    """
    Represents a 3D coordinate system.

    :ivar IFrame iframe: Underlying 3D frame.
    """

    @classmethod
    def by_origin(cls, origin: Point) -> Frame:
        """
        Create a 3D frame from an origin.

        :param Point origin: Origin point.
        :return: New 3D frame.
        :rtype: Frame
        """
        iframe = IFrame.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    def __init__(self, f: IFrame):
        """
        Initialize from an IFrame.

        :param IFrame f: Underlying 3D frame.
        """
        if not isinstance(f, IFrame):
            raise TypeError(f'Expected IFrame, got {type(f).__name__}.')
        self._iframe = f

    @property
    def iframe(self) -> IFrame:
        """
        Underlying 3D frame.

        :return: IFrame object.
        :rtype: IFrame
        """
        return self._iframe

    @cached_property
    def x_direction(self) -> Vector:
        """
        X direction vector.

        :return: X direction.
        :rtype: Vector
        """
        return Vector(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector:
        """
        Y direction vector.

        :return: Y direction.
        :rtype: Vector
        """
        return Vector(self.iframe.YDirection())

    @cached_property
    def z_direction(self) -> Vector:
        """
        Z direction vector.

        :return: Z direction.
        :rtype: Vector
        """
        return Vector(self.iframe.ZDirection())


class Transform:
    """
    Represents a 3D geometric transformation.

    :ivar ITransform itransform: Underlying transformation.
    """

    @classmethod
    def by_mirror(cls, origin: Point, normal: Vector) -> Transform:
        """
        Create a mirror transformation.

        :param Point origin: Point on mirror plane.
        :param Vector normal: Mirror plane normal.
        :return: New transformation.
        :rtype: Transform
        """
        itransform = ITransform.MakeMirror(origin.ipoint, normal.ivector)
        return cls(itransform)

    def __init__(self, t: ITransform):
        """
        Initialize from an ITransform.

        :param ITransform t: Underlying transformation.
        """
        if not isinstance(t, ITransform):
            raise TypeError(f'Expected ITransform, got {type(t).__name__}.')
        self._itransform = t

    @property
    def itransform(self) -> ITransform:
        """
        Underlying transformation.

        :return: ITransform object.
        :rtype: ITransform
        """
        return self._itransform


class Curve:
    """
    Base class for 3D curves.

    :ivar ICurve icurve: Underlying 3D curve.
    """

    @staticmethod
    def by_icurve(icurve: ICurve) -> Curve:
        """
        Create a curve from an ICurve.

        :param ICurve icurve: Underlying curve.
        :return: The curve.
        :rtype: Curve
        """
        match icurve.Kind():
            case ICurveKind.Line:
                return Line(icurve)
            case ICurveKind.Circle:
                return Circle(icurve)
            case ICurveKind.Trimmed:
                return TrimmedCurve(icurve)
            case _:
                raise NotImplementedError(f'Unsupported curve kind: {icurve.Kind()}.')

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        if not isinstance(c, ICurve):
            raise TypeError(f'Expected ICurve, got {type(c).__name__}.')
        self._icurve = c

    @property
    def icurve(self) -> ICurve:
        """
        Underlying 3D curve.

        :return: ICurve object.
        :rtype: ICurve
        """
        return self._icurve

    def evaluate(self, u: float) -> Point:
        """
        Evaluate the curve at a parameter.

        :param float u: Parameter value.
        :return: Evaluated point.
        :rtype: Point
        """
        ipoint = self.icurve.Evaluate(u)
        return Point(ipoint)


class Line(Curve):
    """
    Represents a 3D line.
    """

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Line:
        """
        Create a line through two points.

        :param Point p1: First point.
        :param Point p2: Second point.
        :return: New 3D line.
        :rtype: Line
        """
        icurve = ICurve.MakeLine(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Line:
            raise TypeError(f'Expected ICurveKind.Line, got {c.Kind()}.')

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the line

        :return: The origin of the line.
        :rtype: Point
        """
        idata = self.icurve.LineData()
        return Point(idata.Origin)

    @cached_property
    def direction(self) -> Vector:
        """
        Direction vector of the line

        :return: The direction vector of the line.
        :rtype: Vector
        """
        idata = self.icurve.LineData()
        return Vector(idata.Direction)


class Circle(Curve):
    """
    Represents a 3D circle.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Optional[Frame] = None) -> Circle:
        """
        Create a circle from frame and radius.

        :param float radius: Circle radius.
        :param Optional[Frame] frame: Coordinate system. Defaults to the global origin.
        :return: New 3D circle.
        :rtype: Circle
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0., 0., 0.))

        icurve = ICurve.MakeCircle(frame.iframe, radius)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point, p2: Point, p3: Point) -> Circle:
        """
        Create a circle through three points.

        :param Point p1: First point.
        :param Point p2: Second point.
        :param Point p3: Third point.
        :return: New 3D circle.
        :rtype: Circle
        """
        icurve = ICurve.MakeCircle(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Circle:
            raise TypeError(f'Expected ICurveKind.Circle, got {c.Kind()}.')

    @cached_property
    def radius(self) -> float:
        """
        Radius of the circle.

        :return: Radius.
        :rtype: float
        """
        idata = self.icurve.CircleData()
        return idata.Radius


class TrimmedCurve(Curve):
    """
    Represents a trimmed 3D curve.
    """

    @classmethod
    def by_circular_arc(cls, p1: Point, p2: Point, p3: Point) -> TrimmedCurve:
        """
        Create a circular arc through three points.

        :param Point p1: Start point.
        :param Point p2: Intermediate point.
        :param Point p3: End point.
        :return: New trimmed curve.
        :rtype: TrimmedCurve
        """
        icurve = ICurve.MakeCircularArc(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Trimmed:
            raise TypeError(f'Expected ICurveKind.Trimmed, got {c.Kind()}.')


class Surface:
    """
    Base class for surfaces.

    :ivar ISurface isurface: Underlying surface.
    """

    @staticmethod
    def by_isurface(isurface: ISurface) -> Surface:
        """
        Create a surface from an ISurface.

        :param ISurface isurface: Underlying surface.
        :return: The surface.
        :rtype: Surface
        """
        match isurface.Kind():
            case ISurfaceKind.Cylindrical:
                return CylindricalSurface(isurface)
            case _:
                raise NotImplementedError(f'Unsupported surface kind: {isurface.Kind()}.')

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        if not isinstance(s, ISurface):
            raise TypeError(f'Expected ISurface, got {type(s).__name__}.')
        self._isurface = s

    @property
    def isurface(self) -> ISurface:
        """
        Underlying surface.

        :return: ISurface object.
        :rtype: ISurface
        """
        return self._isurface


class CylindricalSurface(Surface):
    """
    Represents a cylindrical surface.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Optional[Frame] = None) -> CylindricalSurface:
        """
        Create a cylindrical surface from radius and frame.

        :param float radius: Cylinder radius.
        :param Optional[Frame] frame: Coordinate system. Defaults to the global origin.
        :return: New cylindrical surface.
        :rtype: CylindricalSurface
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0., 0., 0.))

        isurface = ISurface.MakeCylindrical(frame.iframe, radius)
        return cls(isurface)

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        super().__init__(s)
        if s.Kind() != ISurfaceKind.Cylindrical:
            raise TypeError(f'Expected ISurfaceKind.Cylindrical, got {s.Kind()}.')
