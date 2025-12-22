from __future__ import annotations

from typing import Optional

from pyocctlite._occtlite import (ICurve, ICurve2D, ICurve2DKind, ICurveKind, IFrame, IFrame2D,
                                  IPoint, IPoint2D, ISurface, ISurfaceKind, ITransform, IVector,
                                  IVector2D)


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
        return cls(IPoint2D(x, y))

    def __init__(self, p: IPoint2D):
        """
        Initialize from an IPoint2D.

        :param IPoint2D p: Underlying 2D point.
        """
        assert isinstance(p, IPoint2D)
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
        return cls(IVector2D(x, y))

    def __init__(self, v: IVector2D):
        """
        Initialize from an IVector2D.

        :param IVector2D v: Underlying 2D vector.
        """
        assert isinstance(v, IVector2D)
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
        return Vector2D(self.ivector.scaled(scale))


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
        assert isinstance(f, IFrame2D)
        self._iframe = f

    @property
    def iframe(self) -> IFrame2D:
        """
        Underlying 2D frame.

        :return: IFrame2D object.
        :rtype: IFrame2D
        """
        return self._iframe

    @property
    def x_direction(self) -> Vector2D:
        """
        X direction vector.

        :return: X direction.
        :rtype: Vector2D
        """
        return Vector2D(self.iframe.XDirection())

    @property
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

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        assert isinstance(c, ICurve2D)
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
    def by_radii(cls, frame: Frame2D, rmajor: float, rminor: float) -> Ellipse2D:
        """
        Create an ellipse from frame and radii.

        :param Frame2D frame: Coordinate system.
        :param float rmajor: Major radius.
        :param float rminor: Minor radius.
        :return: New 2D ellipse.
        :rtype: Ellipse2D
        """
        icurve = ICurve2D.MakeEllipse(frame.iframe, rmajor, rminor)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        super().__init__(c)
        assert c.Kind() == ICurve2DKind.Ellipse


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
        return TrimmedCurve2D(icurve)

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
        return TrimmedCurve2D(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        super().__init__(c)
        assert c.Kind() == ICurve2DKind.Trimmed


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
        return cls(IPoint(x, y, z))

    def __init__(self, p: IPoint):
        """
        Initialize from an IPoint.

        :param IPoint p: Underlying 3D point.
        """
        assert isinstance(p, IPoint)
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
        return cls(IVector(x, y, z))

    def __init__(self, v: IVector):
        """
        Initialize from an IVector.

        :param IVector v: Underlying 3D vector.
        """
        assert isinstance(v, IVector)
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
        assert isinstance(f, IFrame)
        self._iframe = f

    @property
    def iframe(self) -> IFrame:
        """
        Underlying 3D frame.

        :return: IFrame object.
        :rtype: IFrame
        """
        return self._iframe

    @property
    def x_direction(self) -> Vector:
        """
        X direction vector.

        :return: X direction.
        :rtype: Vector
        """
        return Vector(self.iframe.XDirection())

    @property
    def y_direction(self) -> Vector:
        """
        Y direction vector.

        :return: Y direction.
        :rtype: Vector
        """
        return Vector(self.iframe.YDirection())

    @property
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
    def mirror(cls, origin: Point, normal: Vector) -> Transform:
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
        assert isinstance(t, ITransform)
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

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        assert isinstance(c, ICurve)
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
        assert c.Kind() == ICurveKind.Line


class Circle(Curve):
    """
    Represents a 3D circle.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Optional[Frame] = None) -> Circle:
        """
        Create a circle from frame and radius.

        :param float radius: Circle radius.
        :param Optional[Frame] frame: Coordinate system.
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
        assert c.Kind() == ICurveKind.Circle

    @property
    def radius(self) -> float:
        """
        Radius of the circle.

        :return: Radius.
        :rtype: float
        """
        idata = self.icurve.CircleData()
        if idata is None:
            raise TypeError('Curve is not a circle.')

        return idata.radius


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
        assert c.Kind() == ICurveKind.Trimmed


class Surface:
    """
    Base class for surfaces.

    :ivar ISurface isurface: Underlying surface.
    """

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        assert isinstance(s, ISurface)
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
    def by_radius(cls, frame: Frame, radius: float) -> CylindricalSurface:
        """
        Create a cylindrical surface from frame and radius.

        :param Frame frame: Coordinate system.
        :param float radius: Cylinder radius.
        :return: New cylindrical surface.
        :rtype: CylindricalSurface
        """
        isurface = ISurface.MakeCylindrical(frame.iframe, radius)
        return cls(isurface)

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        super().__init__(s)
        assert s.Kind() == ISurfaceKind.Cylindrical
