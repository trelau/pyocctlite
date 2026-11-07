"""
Points, vectors, frames, curves and surfaces.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cached_property

from pyocctlite._occtlite import (
    IAxis,
    IBoundingBox,
    ICurve,
    ICurve2D,
    ICurve2DKind,
    ICurveKind,
    IFrame,
    IFrame2D,
    IPoint,
    IPoint2D,
    ISurface,
    ISurfaceKind,
    ITransform,
    IVector,
    IVector2D,
    ProjectIPointToICurve,
)

__all__ = [
    "Axis",
    "BSplineCurve",
    "BoundingBox",
    "Circle",
    "Curve",
    "Curve2D",
    "CylindricalSurface",
    "Ellipse2D",
    "Frame",
    "Frame2D",
    "Line",
    "Line2D",
    "Point",
    "Point2D",
    "ProjectPointToCurve",
    "Surface",
    "Transform",
    "TrimmedCurve",
    "TrimmedCurve2D",
    "Vector",
    "Vector2D",
]


class Point2D:
    """
    Represents a 2D point.

    :ivar ipoint: Underlying 2D point.
    """

    @classmethod
    def by_xy(cls, x: float, y: float) -> Point2D:
        """
        Create a 2D point from coordinates.

        :param x: x coordinate.
        :param y: y coordinate.
        :return: New 2D point.
        """
        return cls(IPoint2D.MakeByXY(x, y))

    def __init__(self, p: IPoint2D):
        """
        Initialize from an IPoint2D.

        :param p: Underlying 2D point.
        """
        if not isinstance(p, IPoint2D):
            raise TypeError(f"Expected IPoint2D, got {type(p).__name__}.")
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint2D:
        """
        Underlying 2D point.

        :return: IPoint2D object.
        """
        return self._ipoint

    @property
    def x(self) -> float:
        """
        x coordinate.

        :return: x value.
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        y coordinate.

        :return: y value.
        """
        return self.ipoint.Y()

    def translate(self, vector: Vector2D) -> Point2D:
        """
        Create a copy of this point moved along a vector.

        :param vector: Translation direction and distance.
        :return: Moved point.
        """
        return Point2D(self.ipoint.Translated(vector.ivector))

    def distance(self, other: Point2D) -> float:
        """
        Get the distance to another point.

        :param other: Other point.
        :return: Distance.
        """
        return self.ipoint.Distance(other.ipoint)

    def is_equal(self, other: Point2D, tol: float = 1.0e-7) -> bool:
        """
        Check if this point is equal to another within a tolerance.

        :param other: Other point.
        :param tol: Distance tolerance.
        :return: True if the points are within the tolerance.
        """
        return self.ipoint.IsEqual(other.ipoint, tol)


class Vector2D:
    """
    Represents a 2D vector.

    :ivar ivector: Underlying 2D vector.
    """

    @classmethod
    def by_xy(cls, x: float, y: float) -> Vector2D:
        """
        Create a 2D vector from components.

        :param x: x component.
        :param y: y component.
        :return: New 2D vector.
        """
        return cls(IVector2D.MakeByXY(x, y))

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> Vector2D:
        """
        Create a vector from one point to another.

        :param p1: Start point.
        :param p2: End point.
        :return: New vector.
        """
        return cls(IVector2D.MakeByPoints(p1.ipoint, p2.ipoint))

    def __init__(self, v: IVector2D):
        """
        Initialize from an IVector2D.

        :param v: Underlying 2D vector.
        """
        if not isinstance(v, IVector2D):
            raise TypeError(f"Expected IVector2D, got {type(v).__name__}.")
        self._ivector = v

    @property
    def ivector(self) -> IVector2D:
        """
        Underlying 2D vector.

        :return: IVector2D object.
        """
        return self._ivector

    @property
    def x(self) -> float:
        """
        x component.

        :return: x value.
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        y component.

        :return: y value.
        """
        return self.ivector.Y()

    @cached_property
    def magnitude(self) -> float:
        """
        Magnitude of the vector.

        :return: Magnitude.
        """
        return self.ivector.Magnitude()

    def scale(self, scale: float) -> Vector2D:
        """
        Create a scaled version of this vector.

        :param scale: Scale factor.
        :return: Scaled vector.
        """
        return Vector2D(self.ivector.Scaled(scale))

    def add(self, other: Vector2D) -> Vector2D:
        """
        Create the sum of this vector and another.

        :param other: Other vector.
        :return: Sum.
        """
        return Vector2D(self.ivector.Added(other.ivector))

    def subtract(self, other: Vector2D) -> Vector2D:
        """
        Create the difference of this vector and another.

        :param other: Vector to subtract.
        :return: Difference.
        """
        return Vector2D(self.ivector.Subtracted(other.ivector))

    def reverse(self) -> Vector2D:
        """
        Create a copy of this vector pointing the opposite way.

        :return: Reversed vector.
        """
        return Vector2D(self.ivector.Reversed())

    def normalize(self) -> Vector2D:
        """
        Create a unit-length copy of this vector.

        :return: Unit vector.
        :raises RuntimeError: If the vector has zero length.
        """
        return Vector2D(self.ivector.Normalized())

    def dot(self, other: Vector2D) -> float:
        """
        Compute the dot product with another vector.

        :param other: Other vector.
        :return: Dot product.
        """
        return self.ivector.Dot(other.ivector)

    def cross(self, other: Vector2D) -> float:
        """
        Compute the scalar cross product with another vector.

        :param other: Other vector.
        :return: Signed area of the parallelogram, positive if ``other`` is counterclockwise.
        """
        return self.ivector.Cross(other.ivector)

    def is_equal(self, other: Vector2D, tol: float = 1.0e-7, angular_tol: float = 1.0e-12) -> bool:
        """
        Check if this vector has the same magnitude and direction as another within tolerances.

        :param other: Other vector.
        :param tol: Magnitude tolerance.
        :param angular_tol: Direction tolerance in radians.
        :return: True if the vectors are within the tolerances.
        """
        return self.ivector.IsEqual(other.ivector, tol, angular_tol)


class Frame2D:
    """
    Represents a 2D coordinate system.

    :ivar iframe: Underlying 2D frame.
    """

    @classmethod
    def by_origin(cls, origin: Point2D) -> Frame2D:
        """
        Create a 2D frame at an origin, aligned with the global axes.

        :param origin: Origin point.
        :return: New 2D frame.
        """
        iframe = IFrame2D.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vector(cls, origin: Point2D, xvec: Vector2D) -> Frame2D:
        """
        Create a 2D frame from an origin and x-direction.

        :param origin: Origin point.
        :param xvec: x-direction vector. Must be non-zero.
        :return: New 2D frame.
        :raises RuntimeError: If the vector has zero length.
        """
        iframe = IFrame2D.MakeByVector(origin.ipoint, xvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame2D):
        """
        Initialize from an IFrame2D.

        :param f: Underlying 2D frame.
        """
        if not isinstance(f, IFrame2D):
            raise TypeError(f"Expected IFrame2D, got {type(f).__name__}.")
        self._iframe = f

    @property
    def iframe(self) -> IFrame2D:
        """
        Underlying 2D frame.

        :return: IFrame2D object.
        """
        return self._iframe

    @cached_property
    def origin(self) -> Point2D:
        """
        Origin of the frame.

        :return: Origin point.
        """
        return Point2D(self.iframe.Origin())

    @cached_property
    def x_direction(self) -> Vector2D:
        """
        x-direction vector.

        :return: x-direction vector.
        """
        return Vector2D(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector2D:
        """
        y-direction vector.

        :return: y-direction vector.
        """
        return Vector2D(self.iframe.YDirection())


class Curve2D:
    """
    Base class for 2D curves.

    :ivar icurve: Underlying 2D curve.
    """

    @staticmethod
    def by_icurve2d(icurve: ICurve2D) -> Curve2D:
        """
        Create a 2D curve from an ICurve2D.

        :param icurve: Underlying 2D curve.
        :return: New 2D curve.
        """
        match icurve.Kind():
            case ICurve2DKind.Line:
                return Line2D(icurve)
            case ICurve2DKind.Ellipse:
                return Ellipse2D(icurve)
            case ICurve2DKind.Trimmed:
                return TrimmedCurve2D(icurve)
            case _:
                raise NotImplementedError(f"Unsupported 2D curve kind: {icurve.Kind()}.")

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param c: Underlying 2D curve.
        """
        if not isinstance(c, ICurve2D):
            raise TypeError(f"Expected ICurve2D, got {type(c).__name__}.")
        self._icurve = c

    @property
    def icurve(self) -> ICurve2D:
        """
        Underlying 2D curve.

        :return: ICurve2D object.
        """
        return self._icurve

    def evaluate(self, u: float) -> Point2D:
        """
        Evaluate the curve at a parameter.

        :param u: Curve parameter.
        :return: Evaluated point.
        """
        ipoint = self.icurve.Evaluate(u)
        return Point2D(ipoint)

    def derivative(self, u: float, order: int = 1) -> Vector2D:
        """
        Evaluate a derivative of the curve at a parameter.

        :param u: Curve parameter.
        :param order: Order of the derivative. Must be at least 1.
        :return: Derivative vector.
        :raises RuntimeError: If the order is less than 1.
        """
        return Vector2D(self.icurve.Derivative(u, order))

    @cached_property
    def is_closed(self) -> bool:
        """
        Check if the curve ends where it starts.

        :return: True if closed.
        """
        return self.icurve.IsClosed()

    @cached_property
    def is_periodic(self) -> bool:
        """
        Check if the curve repeats along its parameter.

        :return: True if periodic.
        """
        return self.icurve.IsPeriodic()

    @cached_property
    def first_parameter(self) -> float:
        """
        Parameter at the start of the curve.

        :return: First parameter.
        """
        return self.icurve.FirstParameter()

    @cached_property
    def last_parameter(self) -> float:
        """
        Parameter at the end of the curve.

        :return: Last parameter.
        """
        return self.icurve.LastParameter()


class Line2D(Curve2D):
    """
    Represents an unbounded 2D line, parameterized by the distance from the origin along the
    direction.
    """

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> Line2D:
        """
        Create a line through two points, with its origin at the first point.

        :param p1: First point.
        :param p2: Second point.
        :return: New 2D line.
        :raises RuntimeError: If the points coincide.
        """
        icurve = ICurve2D.MakeLine(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Line:
            raise TypeError(f"Expected ICurve2DKind.Line, got {c.Kind()}.")

    @cached_property
    def origin(self) -> Point2D:
        """
        Origin of the line.

        :return: Origin point.
        """
        return Point2D(self.icurve.LineData().Origin)

    @cached_property
    def direction(self) -> Vector2D:
        """
        Unit direction of the line.

        :return: Unit direction vector.
        """
        return Vector2D(self.icurve.LineData().Direction)


class Ellipse2D(Curve2D):
    """
    Represents a 2D ellipse with its major axis along the x-direction of the frame, parameterized by
    the angle in radians from that axis.
    """

    @classmethod
    def by_radii(cls, rmajor: float, rminor: float, frame: Frame2D | None = None) -> Ellipse2D:
        """
        Create an ellipse from radii and frame.

        :param rmajor: Major radius.
        :param rminor: Minor radius. Must not exceed the major radius.
        :param frame: Coordinate system. Defaults to the global origin.
        :return: New 2D ellipse.
        :raises RuntimeError: If the minor radius exceeds the major radius.
        """
        if frame is None:
            frame = Frame2D.by_origin(Point2D.by_xy(0.0, 0.0))

        icurve = ICurve2D.MakeEllipse(frame.iframe, rmajor, rminor)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Ellipse:
            raise TypeError(f"Expected ICurve2DKind.Ellipse, got {c.Kind()}.")

    @cached_property
    def frame(self) -> Frame2D:
        """
        Coordinate system of the ellipse, with its center at the origin.

        :return: Frame.
        """
        return Frame2D(self.icurve.EllipseData().Frame)

    @cached_property
    def rmajor(self) -> float:
        """
        Major radius of the ellipse.

        :return: Major radius.
        """
        return self.icurve.EllipseData().MajorRadius

    @cached_property
    def rminor(self) -> float:
        """
        Minor radius of the ellipse.

        :return: Minor radius.
        """
        return self.icurve.EllipseData().MinorRadius


class TrimmedCurve2D(Curve2D):
    """
    Represents a trimmed 2D curve, using the parameter of the underlying curve.
    """

    @classmethod
    def by_curve(cls, curve: Curve2D, u0: float, u1: float) -> TrimmedCurve2D:
        """
        Trim a curve between parameters.

        :param curve: Curve to trim.
        :param u0: Start parameter.
        :param u1: End parameter. Must differ from the start parameter.
        :return: New trimmed curve.
        :raises RuntimeError: If the parameters are equal.
        """
        icurve = ICurve2D.MakeTrimmed(curve.icurve, u0, u1)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> TrimmedCurve2D:
        """
        Create a line segment between points, parameterized by the distance from the start point.

        :param p1: Start point.
        :param p2: End point.
        :return: New trimmed curve.
        :raises RuntimeError: If the points coincide.
        """
        icurve = ICurve2D.MakeTrimmed(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Trimmed:
            raise TypeError(f"Expected ICurve2DKind.Trimmed, got {c.Kind()}.")


class Point:
    """
    Represents a 3D point.

    :ivar ipoint: Underlying 3D point.
    """

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Point:
        """
        Create a 3D point from coordinates.

        :param x: x coordinate.
        :param y: y coordinate.
        :param z: z coordinate.
        :return: New 3D point.
        """
        return cls(IPoint.MakeByXYZ(x, y, z))

    def __init__(self, p: IPoint):
        """
        Initialize from an IPoint.

        :param p: Underlying 3D point.
        """
        if not isinstance(p, IPoint):
            raise TypeError(f"Expected IPoint, got {type(p).__name__}.")
        self._ipoint = p

    @property
    def ipoint(self) -> IPoint:
        """
        Underlying 3D point.

        :return: IPoint object.
        """
        return self._ipoint

    @property
    def x(self) -> float:
        """
        x coordinate.

        :return: x value.
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        y coordinate.

        :return: y value.
        """
        return self.ipoint.Y()

    @property
    def z(self) -> float:
        """
        z coordinate.

        :return: z value.
        """
        return self.ipoint.Z()

    def translate(self, vector: Vector) -> Point:
        """
        Create a copy of this point moved along a vector.

        :param vector: Translation direction and distance.
        :return: Moved point.
        """
        return Point(self.ipoint.Translated(vector.ivector))

    def distance(self, other: Point) -> float:
        """
        Get the distance to another point.

        :param other: Other point.
        :return: Distance.
        """
        return self.ipoint.Distance(other.ipoint)

    def is_equal(self, other: Point, tol: float = 1.0e-7) -> bool:
        """
        Check if this point is equal to another within a tolerance.

        :param other: Other point.
        :param tol: Distance tolerance.
        :return: True if the points are within the tolerance.
        """
        return self.ipoint.IsEqual(other.ipoint, tol)


class Vector:
    """
    Represents a 3D vector.

    :ivar ivector: Underlying 3D vector.
    """

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Vector:
        """
        Create a 3D vector from components.

        :param x: x component.
        :param y: y component.
        :param z: z component.
        :return: New 3D vector.
        """
        return cls(IVector.MakeByXYZ(x, y, z))

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Vector:
        """
        Create a vector from one point to another.

        :param p1: Start point.
        :param p2: End point.
        :return: New vector.
        """
        return cls(IVector.MakeByPoints(p1.ipoint, p2.ipoint))

    def __init__(self, v: IVector):
        """
        Initialize from an IVector.

        :param v: Underlying 3D vector.
        """
        if not isinstance(v, IVector):
            raise TypeError(f"Expected IVector, got {type(v).__name__}.")
        self._ivector = v

    @property
    def ivector(self) -> IVector:
        """
        Underlying 3D vector.

        :return: IVector object.
        """
        return self._ivector

    @property
    def x(self) -> float:
        """
        x component.

        :return: x value.
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        y component.

        :return: y value.
        """
        return self.ivector.Y()

    @property
    def z(self) -> float:
        """
        z component.

        :return: z value.
        """
        return self.ivector.Z()

    @cached_property
    def magnitude(self) -> float:
        """
        Magnitude of the vector.

        :return: Magnitude.
        """
        return self.ivector.Magnitude()

    def scale(self, scale: float) -> Vector:
        """
        Create a scaled version of this vector.

        :param scale: Scale factor.
        :return: Scaled vector.
        """
        return Vector(self.ivector.Scaled(scale))

    def add(self, other: Vector) -> Vector:
        """
        Create the sum of this vector and another.

        :param other: Other vector.
        :return: Sum.
        """
        return Vector(self.ivector.Added(other.ivector))

    def subtract(self, other: Vector) -> Vector:
        """
        Create the difference of this vector and another.

        :param other: Vector to subtract.
        :return: Difference.
        """
        return Vector(self.ivector.Subtracted(other.ivector))

    def reverse(self) -> Vector:
        """
        Create a copy of this vector pointing the opposite way.

        :return: Reversed vector.
        """
        return Vector(self.ivector.Reversed())

    def normalize(self) -> Vector:
        """
        Create a unit-length copy of this vector.

        :return: Unit vector.
        :raises RuntimeError: If the vector has zero length.
        """
        return Vector(self.ivector.Normalized())

    def dot(self, other: Vector) -> float:
        """
        Compute the dot product with another vector.

        :param other: Other vector.
        :return: Dot product.
        """
        return self.ivector.Dot(other.ivector)

    def cross(self, other: Vector) -> Vector:
        """
        Compute the cross product with another vector.

        :param other: Other vector.
        :return: Cross product.
        """
        return Vector(self.ivector.Cross(other.ivector))

    def is_equal(self, other: Vector, tol: float = 1.0e-7, angular_tol: float = 1.0e-12) -> bool:
        """
        Check if this vector has the same magnitude and direction as another within tolerances.

        :param other: Other vector.
        :param tol: Magnitude tolerance.
        :param angular_tol: Direction tolerance in radians.
        :return: True if the vectors are within the tolerances.
        """
        return self.ivector.IsEqual(other.ivector, tol, angular_tol)


class Axis:
    """
    Represents a 3D axis.

    :ivar iaxis: Underlying 3D axis.
    """

    @classmethod
    def by_vector(cls, origin: Point, direction: Vector) -> Axis:
        """
        Create a 3D axis from an origin and a direction.

        :param origin: Origin point.
        :param direction: Direction. Must be non-zero. The axis stores it normalized.
        :return: New 3D axis.
        :raises RuntimeError: If the direction has zero length.
        """
        iaxis = IAxis.MakeByVector(origin.ipoint, direction.ivector)
        return cls(iaxis)

    def __init__(self, a: IAxis):
        """
        Initialize from an IAxis.

        :param a: Underlying 3D axis.
        """
        if not isinstance(a, IAxis):
            raise TypeError(f"Expected IAxis, got {type(a).__name__}.")
        self._iaxis = a

    @property
    def iaxis(self) -> IAxis:
        """
        Underlying 3D axis.

        :return: IAxis object.
        """
        return self._iaxis

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the axis.

        :return: Origin point.
        """
        return Point(self.iaxis.Origin())

    @cached_property
    def direction(self) -> Vector:
        """
        Direction of the axis.

        :return: Direction vector.
        """
        return Vector(self.iaxis.Direction())


class Frame:
    """
    Represents a 3D coordinate system.

    :ivar iframe: Underlying 3D frame.
    """

    @classmethod
    def by_origin(cls, origin: Point) -> Frame:
        """
        Create a 3D frame at an origin, aligned with the global axes.

        :param origin: Origin point.
        :return: New 3D frame.
        """
        iframe = IFrame.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vectors(cls, origin: Point, xvec: Vector, zvec: Vector) -> Frame:
        """
        Create a right-handed 3D frame from an origin, x-direction, and z-direction, keeping the
        z-direction.

        :param origin: Origin point.
        :param xvec: x-direction vector. Must be non-zero and not parallel to ``zvec``.
        :param zvec: z-direction vector. Must be non-zero.
        :return: New 3D frame.
        :raises RuntimeError: If a vector has zero length or the vectors are parallel.
        """
        iframe = IFrame.MakeByVectors(origin.ipoint, xvec.ivector, zvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame):
        """
        Initialize from an IFrame.

        :param f: Underlying 3D frame.
        """
        if not isinstance(f, IFrame):
            raise TypeError(f"Expected IFrame, got {type(f).__name__}.")
        self._iframe = f

    @property
    def iframe(self) -> IFrame:
        """
        Underlying 3D frame.

        :return: IFrame object.
        """
        return self._iframe

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the frame.

        :return: Origin point.
        """
        return Point(self.iframe.Origin())

    @cached_property
    def axis(self) -> Axis:
        """
        Axis through the origin along the z-direction.

        :return: Axis.
        """
        return Axis(self.iframe.Axis())

    @cached_property
    def x_direction(self) -> Vector:
        """
        x-direction vector.

        :return: x-direction vector.
        """
        return Vector(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector:
        """
        y-direction vector.

        :return: y-direction vector.
        """
        return Vector(self.iframe.YDirection())

    @cached_property
    def z_direction(self) -> Vector:
        """
        z-direction vector.

        :return: z-direction vector.
        """
        return Vector(self.iframe.ZDirection())


class Transform:
    """
    Represents a 3D geometric transformation.

    :ivar itransform: Underlying transformation.
    """

    @classmethod
    def by_mirror(cls, origin: Point, normal: Vector) -> Transform:
        """
        Create a mirror transformation.

        :param origin: Point on the mirror plane.
        :param normal: Normal of the mirror plane. Must be non-zero.
        :return: New transformation.
        :raises RuntimeError: If the normal has zero length.
        """
        itransform = ITransform.MakeMirror(origin.ipoint, normal.ivector)
        return cls(itransform)

    @classmethod
    def by_rotation(cls, axis: Axis, angle: float) -> Transform:
        """
        Create a rotation transformation.

        :param axis: Axis of rotation.
        :param angle: Angle in radians, counterclockwise when looking against the axis
            direction.
        :return: New transformation.
        """
        itransform = ITransform.MakeRotation(axis.iaxis, angle)
        return cls(itransform)

    @classmethod
    def by_translation(cls, vector: Vector) -> Transform:
        """
        Create a translation transformation.

        :param vector: Translation direction and distance.
        :return: New transformation.
        """
        itransform = ITransform.MakeTranslation(vector.ivector)
        return cls(itransform)

    def __init__(self, t: ITransform):
        """
        Initialize from an ITransform.

        :param t: Underlying transformation.
        """
        if not isinstance(t, ITransform):
            raise TypeError(f"Expected ITransform, got {type(t).__name__}.")
        self._itransform = t

    @property
    def itransform(self) -> ITransform:
        """
        Underlying transformation.

        :return: ITransform object.
        """
        return self._itransform


class BoundingBox:
    """
    Represents a 3D box aligned with the global axes.

    :ivar ibounding_box: Underlying bounding box.
    """

    def __init__(self, b: IBoundingBox):
        """
        Initialize from an IBoundingBox.

        :param b: Underlying bounding box.
        """
        if not isinstance(b, IBoundingBox):
            raise TypeError(f"Expected IBoundingBox, got {type(b).__name__}.")
        self._ibounding_box = b

    @property
    def ibounding_box(self) -> IBoundingBox:
        """
        Underlying bounding box.

        :return: IBoundingBox object.
        """
        return self._ibounding_box

    @cached_property
    def min_point(self) -> Point:
        """
        Corner with the smallest coordinates.

        :return: Minimum corner.
        """
        return Point(self.ibounding_box.MinPoint())

    @cached_property
    def max_point(self) -> Point:
        """
        Corner with the largest coordinates.

        :return: Maximum corner.
        """
        return Point(self.ibounding_box.MaxPoint())

    @cached_property
    def dx(self) -> float:
        """
        Size along the global x-direction.

        :return: Size in x.
        """
        return self.max_point.x - self.min_point.x

    @cached_property
    def dy(self) -> float:
        """
        Size along the global y-direction.

        :return: Size in y.
        """
        return self.max_point.y - self.min_point.y

    @cached_property
    def dz(self) -> float:
        """
        Size along the global z-direction.

        :return: Size in z.
        """
        return self.max_point.z - self.min_point.z

    @cached_property
    def center(self) -> Point:
        """
        Center of the box.

        :return: Center point.
        """
        return self.min_point.translate(Vector.by_points(self.min_point, self.max_point).scale(0.5))


class Curve:
    """
    Base class for 3D curves.

    :ivar icurve: Underlying 3D curve.
    """

    @staticmethod
    def by_icurve(icurve: ICurve) -> Curve:
        """
        Create a curve from an ICurve.

        :param icurve: Underlying 3D curve.
        :return: New curve.
        """
        match icurve.Kind():
            case ICurveKind.Line:
                return Line(icurve)
            case ICurveKind.Circle:
                return Circle(icurve)
            case ICurveKind.Trimmed:
                return TrimmedCurve(icurve)
            case ICurveKind.BSpline:
                return BSplineCurve(icurve)
            case _:
                raise NotImplementedError(f"Unsupported curve kind: {icurve.Kind()}.")

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param c: Underlying 3D curve.
        """
        if not isinstance(c, ICurve):
            raise TypeError(f"Expected ICurve, got {type(c).__name__}.")
        self._icurve = c

    @property
    def icurve(self) -> ICurve:
        """
        Underlying 3D curve.

        :return: ICurve object.
        """
        return self._icurve

    def evaluate(self, u: float) -> Point:
        """
        Evaluate the curve at a parameter.

        :param u: Curve parameter.
        :return: Evaluated point.
        """
        ipoint = self.icurve.Evaluate(u)
        return Point(ipoint)

    def derivative(self, u: float, order: int = 1) -> Vector:
        """
        Evaluate a derivative of the curve at a parameter.

        :param u: Curve parameter.
        :param order: Order of the derivative. Must be at least 1.
        :return: Derivative vector.
        :raises RuntimeError: If the order is less than 1.
        """
        return Vector(self.icurve.Derivative(u, order))

    @cached_property
    def is_closed(self) -> bool:
        """
        Check if the curve ends where it starts.

        :return: True if closed.
        """
        return self.icurve.IsClosed()

    @cached_property
    def is_periodic(self) -> bool:
        """
        Check if the curve repeats along its parameter.

        :return: True if periodic.
        """
        return self.icurve.IsPeriodic()

    @cached_property
    def first_parameter(self) -> float:
        """
        Parameter at the start of the curve.

        :return: First parameter.
        """
        return self.icurve.FirstParameter()

    @cached_property
    def last_parameter(self) -> float:
        """
        Parameter at the end of the curve.

        :return: Last parameter.
        """
        return self.icurve.LastParameter()


class Line(Curve):
    """
    Represents an unbounded 3D line, parameterized by the distance from the origin along the
    direction.
    """

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Line:
        """
        Create a line through two points, with its origin at the first point.

        :param p1: First point.
        :param p2: Second point.
        :return: New 3D line.
        :raises RuntimeError: If the points coincide.
        """
        icurve = ICurve.MakeLine(p1.ipoint, p2.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Line:
            raise TypeError(f"Expected ICurveKind.Line, got {c.Kind()}.")

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the line.

        :return: Origin point.
        """
        return Point(self.icurve.LineData().Origin)

    @cached_property
    def direction(self) -> Vector:
        """
        Unit direction of the line.

        :return: Unit direction vector.
        """
        return Vector(self.icurve.LineData().Direction)


class Circle(Curve):
    """
    Represents a 3D circle, parameterized by the angle in radians from the x-direction of the frame.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Frame | None = None) -> Circle:
        """
        Create a circle centered at the frame origin, in its xy-plane.

        :param radius: Circle radius. Must not be negative.
        :param frame: Coordinate system. Defaults to the global origin.
        :return: New 3D circle.
        :raises RuntimeError: If the radius is negative.
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        icurve = ICurve.MakeCircle(frame.iframe, radius)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point, p2: Point, p3: Point) -> Circle:
        """
        Create a circle through three points.

        :param p1: First point.
        :param p2: Second point.
        :param p3: Third point.
        :return: New 3D circle.
        :raises RuntimeError: If the points are collinear.
        """
        icurve = ICurve.MakeCircle(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Circle:
            raise TypeError(f"Expected ICurveKind.Circle, got {c.Kind()}.")

    @cached_property
    def frame(self) -> Frame:
        """
        Coordinate system of the circle, with its center at the origin.

        :return: Frame.
        """
        return Frame(self.icurve.CircleData().Frame)

    @cached_property
    def radius(self) -> float:
        """
        Radius of the circle.

        :return: Radius.
        """
        return self.icurve.CircleData().Radius


class TrimmedCurve(Curve):
    """
    Represents a trimmed 3D curve, using the parameter of the underlying curve.
    """

    @classmethod
    def by_circular_arc(cls, p1: Point, p2: Point, p3: Point) -> TrimmedCurve:
        """
        Create a circular arc through three points.

        :param p1: Start point.
        :param p2: Intermediate point.
        :param p3: End point.
        :return: New trimmed curve.
        :raises RuntimeError: If the points are collinear.
        """
        icurve = ICurve.MakeCircularArc(p1.ipoint, p2.ipoint, p3.ipoint)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.Trimmed:
            raise TypeError(f"Expected ICurveKind.Trimmed, got {c.Kind()}.")


class BSplineCurve(Curve):
    """
    Represents a 3D B-spline curve.
    """

    @classmethod
    def by_interpolation(cls, points: Iterable[Point], tol: float = 1.0e-7) -> BSplineCurve:
        """
        Create a smooth curve passing through ordered points.

        :param points: At least two points.
        :param tol: Distance below which two points count as coincident.
        :return: New B-spline curve.
        :raises BuildFailed: If the interpolation fails.
        :raises RuntimeError: If there are fewer than two points.
        """
        icurve = ICurve.MakeBSplineByInterpolation([p.ipoint for p in points], tol)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.BSpline:
            raise TypeError(f"Expected ICurveKind.BSpline, got {c.Kind()}.")


class Surface:
    """
    Base class for surfaces.

    :ivar isurface: Underlying surface.
    """

    @staticmethod
    def by_isurface(isurface: ISurface) -> Surface:
        """
        Create a surface from an ISurface.

        :param isurface: Underlying surface.
        :return: New surface.
        """
        match isurface.Kind():
            case ISurfaceKind.Cylindrical:
                return CylindricalSurface(isurface)
            case _:
                raise NotImplementedError(f"Unsupported surface kind: {isurface.Kind()}.")

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param s: Underlying surface.
        """
        if not isinstance(s, ISurface):
            raise TypeError(f"Expected ISurface, got {type(s).__name__}.")
        self._isurface = s

    @property
    def isurface(self) -> ISurface:
        """
        Underlying surface.

        :return: ISurface object.
        """
        return self._isurface


class CylindricalSurface(Surface):
    """
    Represents a cylindrical surface, parameterized by u, the angle in radians about the z-direction
    from the x-direction of the frame, and v, the distance along the z-direction.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Frame | None = None) -> CylindricalSurface:
        """
        Create a cylindrical surface from radius and frame.

        :param radius: Cylinder radius. Must not be negative.
        :param frame: Coordinate system. Defaults to the global origin.
        :return: New cylindrical surface.
        :raises RuntimeError: If the radius is negative.
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        isurface = ISurface.MakeCylindrical(frame.iframe, radius)
        return cls(isurface)

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param s: Underlying surface.
        """
        super().__init__(s)
        if s.Kind() != ISurfaceKind.Cylindrical:
            raise TypeError(f"Expected ISurfaceKind.Cylindrical, got {s.Kind()}.")

    @cached_property
    def frame(self) -> Frame:
        """
        Coordinate system of the surface, with its axis along the z-direction.

        :return: Frame.
        """
        return Frame(self.isurface.CylindricalData().Frame)

    @cached_property
    def radius(self) -> float:
        """
        Radius of the surface.

        :return: Radius.
        """
        return self.isurface.CylindricalData().Radius


class ProjectPointToCurve:
    """
    Tool to project a point onto a curve, finding where the line to the point is perpendicular to
    the curve.
    """

    def __init__(self, p: Point, c: Curve, u0: float | None = None, u1: float | None = None):
        """
        Initialize with a point, a curve, and an optional parameter range.

        :param p: Point to project.
        :param c: Curve.
        :param u0: Start of the range. Defaults to the start of the curve.
        :param u1: End of the range. Defaults to the end of the curve.
        :raises RuntimeError: If the start of the range is after its end.
        """
        start = c.first_parameter if u0 is None else u0
        end = c.last_parameter if u1 is None else u1
        self._itool = ProjectIPointToICurve(p.ipoint, c.icurve, start, end)

    def perform(self, p: Point) -> None:
        """
        Project a new point onto the same curve and range, replacing the results.

        :param p: Point to project.
        """
        self._itool.Perform(p.ipoint)

    @property
    def is_done(self) -> bool:
        """
        Check if the projection has results.

        :return: True if there is at least one result.
        """
        return self._itool.IsDone()

    @property
    def num_points(self) -> int:
        """
        Number of results.

        :return: Count.
        """
        return self._itool.NumPoints()

    def point(self, index: int) -> Point:
        """
        Get a projected point.

        :param index: 0-based index of the result.
        :return: Point on the curve.
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return Point(self._itool.Point(index + 1))

    def parameter(self, index: int) -> float:
        """
        Get the curve parameter of a projected point.

        :param index: 0-based index of the result.
        :return: Curve parameter.
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return self._itool.Parameter(index + 1)

    def distance(self, index: int) -> float:
        """
        Get the distance from the point to a projected point.

        :param index: 0-based index of the result.
        :return: Distance.
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return self._itool.Distance(index + 1)

    @property
    def nearest_point(self) -> Point:
        """
        Nearest projected point.

        :return: Point on the curve.
        :raises RuntimeError: If there are no results.
        """
        return Point(self._itool.NearestPoint())

    @property
    def nearest_parameter(self) -> float:
        """
        Curve parameter of the nearest projected point.

        :return: Curve parameter.
        :raises RuntimeError: If there are no results.
        """
        return self._itool.NearestParameter()

    @property
    def nearest_distance(self) -> float:
        """
        Distance to the nearest projected point.

        :return: Distance.
        :raises RuntimeError: If there are no results.
        """
        return self._itool.NearestDistance()
