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


class Point2D:
    """
    Represents a 2D point.

    :ivar IPoint2D ipoint: Underlying 2D point.
    """

    @classmethod
    def by_xy(cls, x: float, y: float) -> Point2D:
        """
        Create a 2D point from coordinates.

        :param float x: x coordinate.
        :param float y: y coordinate.
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
            raise TypeError(f"Expected IPoint2D, got {type(p).__name__}.")
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
        x coordinate.

        :return: x value.
        :rtype: float
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        y coordinate.

        :return: y value.
        :rtype: float
        """
        return self.ipoint.Y()

    def translate(self, vector: Vector2D) -> Point2D:
        """
        Create a copy of this point moved along a vector.

        :param Vector2D vector: Translation direction and distance.
        :return: Moved point.
        :rtype: Point2D
        """
        return Point2D(self.ipoint.Translated(vector.ivector))

    def distance(self, other: Point2D) -> float:
        """
        Get the distance to another point.

        :param Point2D other: Other point.
        :return: Distance.
        :rtype: float
        """
        return self.ipoint.Distance(other.ipoint)

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

        :param float x: x component.
        :param float y: y component.
        :return: New 2D vector.
        :rtype: Vector2D
        """
        return cls(IVector2D.MakeByXY(x, y))

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> Vector2D:
        """
        Create a vector from one point to another.

        :param Point2D p1: Start point.
        :param Point2D p2: End point.
        :return: New vector.
        :rtype: Vector2D
        """
        return cls(IVector2D.MakeByPoints(p1.ipoint, p2.ipoint))

    def __init__(self, v: IVector2D):
        """
        Initialize from an IVector2D.

        :param IVector2D v: Underlying 2D vector.
        """
        if not isinstance(v, IVector2D):
            raise TypeError(f"Expected IVector2D, got {type(v).__name__}.")
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
        x component.

        :return: x value.
        :rtype: float
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        y component.

        :return: y value.
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

    def scale(self, scale: float) -> Vector2D:
        """
        Create a scaled version of this vector.

        :param float scale: Scale factor.
        :return: Scaled vector.
        :rtype: Vector2D
        """
        return Vector2D(self.ivector.Scaled(scale))

    def normalize(self) -> Vector2D:
        """
        Create a unit-length copy of this vector.

        :return: Unit vector.
        :rtype: Vector2D
        :raises RuntimeError: If the vector has zero length.
        """
        return Vector2D(self.ivector.Normalized())

    def dot(self, other: Vector2D) -> float:
        """
        Compute the dot product with another vector.

        :param Vector2D other: Other vector.
        :return: Dot product.
        :rtype: float
        """
        return self.ivector.Dot(other.ivector)

    def cross(self, other: Vector2D) -> float:
        """
        Compute the scalar cross product with another vector.

        :param Vector2D other: Other vector.
        :return: Signed area of the parallelogram, positive if ``other`` is counterclockwise.
        :rtype: float
        """
        return self.ivector.Cross(other.ivector)

    def is_equal(self, other: Vector2D, tol: float = 1.0e-7, angular_tol: float = 1.0e-12) -> bool:
        """
        Check if this vector has the same magnitude and direction as another within tolerances.

        :param Vector2D other: Other vector.
        :param float tol: Magnitude tolerance.
        :param float angular_tol: Direction tolerance in radians.
        :return: True if the vectors are within the tolerances.
        :rtype: bool
        """
        return self.ivector.IsEqual(other.ivector, tol, angular_tol)


class Frame2D:
    """
    Represents a 2D coordinate system.

    :ivar IFrame2D iframe: Underlying 2D frame.
    """

    @classmethod
    def by_origin(cls, origin: Point2D) -> Frame2D:
        """
        Create a 2D frame at an origin, aligned with the global axes.

        :param Point2D origin: Origin point.
        :return: New 2D frame.
        :rtype: Frame2D
        """
        iframe = IFrame2D.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vector(cls, origin: Point2D, xvec: Vector2D) -> Frame2D:
        """
        Create a 2D frame from an origin and x-direction.

        :param Point2D origin: Origin point.
        :param Vector2D xvec: x-direction vector. Must be non-zero.
        :return: New 2D frame.
        :rtype: Frame2D
        :raises RuntimeError: If the vector has zero length.
        """
        iframe = IFrame2D.MakeByVector(origin.ipoint, xvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame2D):
        """
        Initialize from an IFrame2D.

        :param IFrame2D f: Underlying 2D frame.
        """
        if not isinstance(f, IFrame2D):
            raise TypeError(f"Expected IFrame2D, got {type(f).__name__}.")
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
    def origin(self) -> Point2D:
        """
        Origin of the frame.

        :return: Origin point.
        :rtype: Point2D
        """
        return Point2D(self.iframe.Origin())

    @cached_property
    def x_direction(self) -> Vector2D:
        """
        x-direction vector.

        :return: x-direction vector.
        :rtype: Vector2D
        """
        return Vector2D(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector2D:
        """
        y-direction vector.

        :return: y-direction vector.
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
        :return: New 2D curve.
        :rtype: Curve2D
        """
        match icurve.Kind():
            case ICurve2DKind.Ellipse:
                return Ellipse2D(icurve)
            case ICurve2DKind.Trimmed:
                return TrimmedCurve2D(icurve)
            case _:
                raise NotImplementedError(f"Unsupported 2D curve kind: {icurve.Kind()}.")

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        if not isinstance(c, ICurve2D):
            raise TypeError(f"Expected ICurve2D, got {type(c).__name__}.")
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

        :param float u: Curve parameter.
        :return: Evaluated point.
        :rtype: Point2D
        """
        ipoint = self.icurve.Evaluate(u)
        return Point2D(ipoint)

    def derivative(self, u: float, order: int = 1) -> Vector2D:
        """
        Evaluate a derivative of the curve at a parameter.

        :param float u: Curve parameter.
        :param int order: Order of the derivative. Must be at least 1.
        :return: Derivative vector.
        :rtype: Vector2D
        :raises RuntimeError: If the order is less than 1.
        """
        return Vector2D(self.icurve.Derivative(u, order))

    @cached_property
    def is_closed(self) -> bool:
        """
        Check if the curve ends where it starts.

        :return: True if closed.
        :rtype: bool
        """
        return self.icurve.IsClosed()

    @cached_property
    def is_periodic(self) -> bool:
        """
        Check if the curve repeats along its parameter.

        :return: True if periodic.
        :rtype: bool
        """
        return self.icurve.IsPeriodic()

    @cached_property
    def first_parameter(self) -> float:
        """
        Parameter at the start of the curve.

        :return: First parameter.
        :rtype: float
        """
        return self.icurve.FirstParameter()

    @cached_property
    def last_parameter(self) -> float:
        """
        Parameter at the end of the curve.

        :return: Last parameter.
        :rtype: float
        """
        return self.icurve.LastParameter()


class Ellipse2D(Curve2D):
    """
    Represents a 2D ellipse with its major axis along the x-direction of the frame, parameterized by
    the angle in radians from that axis.
    """

    @classmethod
    def by_radii(cls, rmajor: float, rminor: float, frame: Frame2D | None = None) -> Ellipse2D:
        """
        Create an ellipse from radii and frame.

        :param float rmajor: Major radius.
        :param float rminor: Minor radius. Must not exceed the major radius.
        :param Frame2D | None frame: Coordinate system. Defaults to the global origin.
        :return: New 2D ellipse.
        :rtype: Ellipse2D
        :raises RuntimeError: If the minor radius exceeds the major radius.
        """
        if frame is None:
            frame = Frame2D.by_origin(Point2D.by_xy(0.0, 0.0))

        icurve = ICurve2D.MakeEllipse(frame.iframe, rmajor, rminor)
        return cls(icurve)

    def __init__(self, c: ICurve2D):
        """
        Initialize from an ICurve2D.

        :param ICurve2D c: Underlying 2D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurve2DKind.Ellipse:
            raise TypeError(f"Expected ICurve2DKind.Ellipse, got {c.Kind()}.")


class TrimmedCurve2D(Curve2D):
    """
    Represents a trimmed 2D curve, using the parameter of the underlying curve.
    """

    @classmethod
    def by_curve(cls, curve: Curve2D, u0: float, u1: float) -> TrimmedCurve2D:
        """
        Trim a curve between parameters.

        :param Curve2D curve: Curve to trim.
        :param float u0: Start parameter.
        :param float u1: End parameter. Must differ from the start parameter.
        :return: New trimmed curve.
        :rtype: TrimmedCurve2D
        :raises RuntimeError: If the parameters are equal.
        """
        icurve = ICurve2D.MakeTrimmed(curve.icurve, u0, u1)
        return cls(icurve)

    @classmethod
    def by_points(cls, p1: Point2D, p2: Point2D) -> TrimmedCurve2D:
        """
        Create a line segment between points, parameterized by the distance from the start point.

        :param Point2D p1: Start point.
        :param Point2D p2: End point.
        :return: New trimmed curve.
        :rtype: TrimmedCurve2D
        :raises RuntimeError: If the points coincide.
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
            raise TypeError(f"Expected ICurve2DKind.Trimmed, got {c.Kind()}.")


class Point:
    """
    Represents a 3D point.

    :ivar IPoint ipoint: Underlying 3D point.
    """

    @classmethod
    def by_xyz(cls, x: float, y: float, z: float) -> Point:
        """
        Create a 3D point from coordinates.

        :param float x: x coordinate.
        :param float y: y coordinate.
        :param float z: z coordinate.
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
            raise TypeError(f"Expected IPoint, got {type(p).__name__}.")
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
        x coordinate.

        :return: x value.
        :rtype: float
        """
        return self.ipoint.X()

    @property
    def y(self) -> float:
        """
        y coordinate.

        :return: y value.
        :rtype: float
        """
        return self.ipoint.Y()

    @property
    def z(self) -> float:
        """
        z coordinate.

        :return: z value.
        :rtype: float
        """
        return self.ipoint.Z()

    def translate(self, vector: Vector) -> Point:
        """
        Create a copy of this point moved along a vector.

        :param Vector vector: Translation direction and distance.
        :return: Moved point.
        :rtype: Point
        """
        return Point(self.ipoint.Translated(vector.ivector))

    def distance(self, other: Point) -> float:
        """
        Get the distance to another point.

        :param Point other: Other point.
        :return: Distance.
        :rtype: float
        """
        return self.ipoint.Distance(other.ipoint)

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

        :param float x: x component.
        :param float y: y component.
        :param float z: z component.
        :return: New 3D vector.
        :rtype: Vector
        """
        return cls(IVector.MakeByXYZ(x, y, z))

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Vector:
        """
        Create a vector from one point to another.

        :param Point p1: Start point.
        :param Point p2: End point.
        :return: New vector.
        :rtype: Vector
        """
        return cls(IVector.MakeByPoints(p1.ipoint, p2.ipoint))

    def __init__(self, v: IVector):
        """
        Initialize from an IVector.

        :param IVector v: Underlying 3D vector.
        """
        if not isinstance(v, IVector):
            raise TypeError(f"Expected IVector, got {type(v).__name__}.")
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
        x component.

        :return: x value.
        :rtype: float
        """
        return self.ivector.X()

    @property
    def y(self) -> float:
        """
        y component.

        :return: y value.
        :rtype: float
        """
        return self.ivector.Y()

    @property
    def z(self) -> float:
        """
        z component.

        :return: z value.
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

    def scale(self, scale: float) -> Vector:
        """
        Create a scaled version of this vector.

        :param float scale: Scale factor.
        :return: Scaled vector.
        :rtype: Vector
        """
        return Vector(self.ivector.Scaled(scale))

    def normalize(self) -> Vector:
        """
        Create a unit-length copy of this vector.

        :return: Unit vector.
        :rtype: Vector
        :raises RuntimeError: If the vector has zero length.
        """
        return Vector(self.ivector.Normalized())

    def dot(self, other: Vector) -> float:
        """
        Compute the dot product with another vector.

        :param Vector other: Other vector.
        :return: Dot product.
        :rtype: float
        """
        return self.ivector.Dot(other.ivector)

    def cross(self, other: Vector) -> Vector:
        """
        Compute the cross product with another vector.

        :param Vector other: Other vector.
        :return: Cross product.
        :rtype: Vector
        """
        return Vector(self.ivector.Cross(other.ivector))

    def is_equal(self, other: Vector, tol: float = 1.0e-7, angular_tol: float = 1.0e-12) -> bool:
        """
        Check if this vector has the same magnitude and direction as another within tolerances.

        :param Vector other: Other vector.
        :param float tol: Magnitude tolerance.
        :param float angular_tol: Direction tolerance in radians.
        :return: True if the vectors are within the tolerances.
        :rtype: bool
        """
        return self.ivector.IsEqual(other.ivector, tol, angular_tol)


class Axis:
    """
    Represents a 3D axis.

    :ivar IAxis iaxis: Underlying 3D axis.
    """

    @classmethod
    def by_vector(cls, origin: Point, direction: Vector) -> Axis:
        """
        Create a 3D axis from an origin and a direction.

        :param Point origin: Origin point.
        :param Vector direction: Direction. Must be non-zero. The axis stores it normalized.
        :return: New 3D axis.
        :rtype: Axis
        :raises RuntimeError: If the direction has zero length.
        """
        iaxis = IAxis.MakeByVector(origin.ipoint, direction.ivector)
        return cls(iaxis)

    def __init__(self, a: IAxis):
        """
        Initialize from an IAxis.

        :param IAxis a: Underlying 3D axis.
        """
        if not isinstance(a, IAxis):
            raise TypeError(f"Expected IAxis, got {type(a).__name__}.")
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

        :return: Origin point.
        :rtype: Point
        """
        return Point(self.iaxis.Origin())

    @cached_property
    def direction(self) -> Vector:
        """
        Direction of the axis.

        :return: Direction vector.
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
        Create a 3D frame at an origin, aligned with the global axes.

        :param Point origin: Origin point.
        :return: New 3D frame.
        :rtype: Frame
        """
        iframe = IFrame.MakeByOrigin(origin.ipoint)
        return cls(iframe)

    @classmethod
    def by_vectors(cls, origin: Point, xvec: Vector, zvec: Vector) -> Frame:
        """
        Create a right-handed 3D frame from an origin, x-direction, and z-direction, keeping the
        z-direction.

        :param Point origin: Origin point.
        :param Vector xvec: x-direction vector. Must be non-zero and not parallel to ``zvec``.
        :param Vector zvec: z-direction vector. Must be non-zero.
        :return: New 3D frame.
        :rtype: Frame
        :raises RuntimeError: If a vector has zero length or the vectors are parallel.
        """
        iframe = IFrame.MakeByVectors(origin.ipoint, xvec.ivector, zvec.ivector)
        return cls(iframe)

    def __init__(self, f: IFrame):
        """
        Initialize from an IFrame.

        :param IFrame f: Underlying 3D frame.
        """
        if not isinstance(f, IFrame):
            raise TypeError(f"Expected IFrame, got {type(f).__name__}.")
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
    def origin(self) -> Point:
        """
        Origin of the frame.

        :return: Origin point.
        :rtype: Point
        """
        return Point(self.iframe.Origin())

    @cached_property
    def axis(self) -> Axis:
        """
        Axis through the origin along the z-direction.

        :return: Axis.
        :rtype: Axis
        """
        return Axis(self.iframe.Axis())

    @cached_property
    def x_direction(self) -> Vector:
        """
        x-direction vector.

        :return: x-direction vector.
        :rtype: Vector
        """
        return Vector(self.iframe.XDirection())

    @cached_property
    def y_direction(self) -> Vector:
        """
        y-direction vector.

        :return: y-direction vector.
        :rtype: Vector
        """
        return Vector(self.iframe.YDirection())

    @cached_property
    def z_direction(self) -> Vector:
        """
        z-direction vector.

        :return: z-direction vector.
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

        :param Point origin: Point on the mirror plane.
        :param Vector normal: Normal of the mirror plane. Must be non-zero.
        :return: New transformation.
        :rtype: Transform
        :raises RuntimeError: If the normal has zero length.
        """
        itransform = ITransform.MakeMirror(origin.ipoint, normal.ivector)
        return cls(itransform)

    @classmethod
    def by_rotation(cls, axis: Axis, angle: float) -> Transform:
        """
        Create a rotation transformation.

        :param Axis axis: Axis of rotation.
        :param float angle: Angle in radians, counterclockwise when looking against the axis
            direction.
        :return: New transformation.
        :rtype: Transform
        """
        itransform = ITransform.MakeRotation(axis.iaxis, angle)
        return cls(itransform)

    @classmethod
    def by_translation(cls, vector: Vector) -> Transform:
        """
        Create a translation transformation.

        :param Vector vector: Translation direction and distance.
        :return: New transformation.
        :rtype: Transform
        """
        itransform = ITransform.MakeTranslation(vector.ivector)
        return cls(itransform)

    def __init__(self, t: ITransform):
        """
        Initialize from an ITransform.

        :param ITransform t: Underlying transformation.
        """
        if not isinstance(t, ITransform):
            raise TypeError(f"Expected ITransform, got {type(t).__name__}.")
        self._itransform = t

    @property
    def itransform(self) -> ITransform:
        """
        Underlying transformation.

        :return: ITransform object.
        :rtype: ITransform
        """
        return self._itransform


class BoundingBox:
    """
    Represents a 3D box aligned with the global axes.

    :ivar IBoundingBox ibounding_box: Underlying bounding box.
    """

    def __init__(self, b: IBoundingBox):
        """
        Initialize from an IBoundingBox.

        :param IBoundingBox b: Underlying bounding box.
        """
        if not isinstance(b, IBoundingBox):
            raise TypeError(f"Expected IBoundingBox, got {type(b).__name__}.")
        self._ibounding_box = b

    @property
    def ibounding_box(self) -> IBoundingBox:
        """
        Underlying bounding box.

        :return: IBoundingBox object.
        :rtype: IBoundingBox
        """
        return self._ibounding_box

    @cached_property
    def min_point(self) -> Point:
        """
        Corner with the smallest coordinates.

        :return: Minimum corner.
        :rtype: Point
        """
        return Point(self.ibounding_box.MinPoint())

    @cached_property
    def max_point(self) -> Point:
        """
        Corner with the largest coordinates.

        :return: Maximum corner.
        :rtype: Point
        """
        return Point(self.ibounding_box.MaxPoint())

    @cached_property
    def dx(self) -> float:
        """
        Size along the global x-direction.

        :return: Size in x.
        :rtype: float
        """
        return self.max_point.x - self.min_point.x

    @cached_property
    def dy(self) -> float:
        """
        Size along the global y-direction.

        :return: Size in y.
        :rtype: float
        """
        return self.max_point.y - self.min_point.y

    @cached_property
    def dz(self) -> float:
        """
        Size along the global z-direction.

        :return: Size in z.
        :rtype: float
        """
        return self.max_point.z - self.min_point.z

    @cached_property
    def center(self) -> Point:
        """
        Center of the box.

        :return: Center point.
        :rtype: Point
        """
        return self.min_point.translate(Vector.by_points(self.min_point, self.max_point).scale(0.5))


class Curve:
    """
    Base class for 3D curves.

    :ivar ICurve icurve: Underlying 3D curve.
    """

    @staticmethod
    def by_icurve(icurve: ICurve) -> Curve:
        """
        Create a curve from an ICurve.

        :param ICurve icurve: Underlying 3D curve.
        :return: New curve.
        :rtype: Curve
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

        :param ICurve c: Underlying 3D curve.
        """
        if not isinstance(c, ICurve):
            raise TypeError(f"Expected ICurve, got {type(c).__name__}.")
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

        :param float u: Curve parameter.
        :return: Evaluated point.
        :rtype: Point
        """
        ipoint = self.icurve.Evaluate(u)
        return Point(ipoint)

    def derivative(self, u: float, order: int = 1) -> Vector:
        """
        Evaluate a derivative of the curve at a parameter.

        :param float u: Curve parameter.
        :param int order: Order of the derivative. Must be at least 1.
        :return: Derivative vector.
        :rtype: Vector
        :raises RuntimeError: If the order is less than 1.
        """
        return Vector(self.icurve.Derivative(u, order))

    @cached_property
    def is_closed(self) -> bool:
        """
        Check if the curve ends where it starts.

        :return: True if closed.
        :rtype: bool
        """
        return self.icurve.IsClosed()

    @cached_property
    def is_periodic(self) -> bool:
        """
        Check if the curve repeats along its parameter.

        :return: True if periodic.
        :rtype: bool
        """
        return self.icurve.IsPeriodic()

    @cached_property
    def first_parameter(self) -> float:
        """
        Parameter at the start of the curve.

        :return: First parameter.
        :rtype: float
        """
        return self.icurve.FirstParameter()

    @cached_property
    def last_parameter(self) -> float:
        """
        Parameter at the end of the curve.

        :return: Last parameter.
        :rtype: float
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

        :param Point p1: First point.
        :param Point p2: Second point.
        :return: New 3D line.
        :rtype: Line
        :raises RuntimeError: If the points coincide.
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
            raise TypeError(f"Expected ICurveKind.Line, got {c.Kind()}.")

    @cached_property
    def origin(self) -> Point:
        """
        Origin of the line.

        :return: Origin point.
        :rtype: Point
        """
        idata = self.icurve.LineData()
        assert idata is not None  # guaranteed by the kind check in __init__
        return Point(idata.Origin)

    @cached_property
    def direction(self) -> Vector:
        """
        Unit direction of the line.

        :return: Unit direction vector.
        :rtype: Vector
        """
        idata = self.icurve.LineData()
        assert idata is not None  # guaranteed by the kind check in __init__
        return Vector(idata.Direction)


class Circle(Curve):
    """
    Represents a 3D circle, parameterized by the angle in radians from the x-direction of the frame.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Frame | None = None) -> Circle:
        """
        Create a circle centered at the frame origin, in its xy-plane.

        :param float radius: Circle radius. Must not be negative.
        :param Frame | None frame: Coordinate system. Defaults to the global origin.
        :return: New 3D circle.
        :rtype: Circle
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

        :param Point p1: First point.
        :param Point p2: Second point.
        :param Point p3: Third point.
        :return: New 3D circle.
        :rtype: Circle
        :raises RuntimeError: If the points are collinear.
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
            raise TypeError(f"Expected ICurveKind.Circle, got {c.Kind()}.")

    @cached_property
    def frame(self) -> Frame:
        """
        Coordinate system of the circle, with its center at the origin.

        :return: Frame.
        :rtype: Frame
        """
        idata = self.icurve.CircleData()
        assert idata is not None  # guaranteed by the kind check in __init__
        return Frame(idata.Frame)

    @cached_property
    def radius(self) -> float:
        """
        Radius of the circle.

        :return: Radius.
        :rtype: float
        """
        idata = self.icurve.CircleData()
        assert idata is not None  # guaranteed by the kind check in __init__
        return idata.Radius


class TrimmedCurve(Curve):
    """
    Represents a trimmed 3D curve, using the parameter of the underlying curve.
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
        :raises RuntimeError: If the points are collinear.
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
            raise TypeError(f"Expected ICurveKind.Trimmed, got {c.Kind()}.")


class BSplineCurve(Curve):
    """
    Represents a 3D B-spline curve.
    """

    @classmethod
    def by_interpolation(cls, points: Iterable[Point], tol: float = 1.0e-7) -> BSplineCurve:
        """
        Create a smooth curve passing through ordered points.

        :param Iterable[Point] points: At least two points.
        :param float tol: Distance below which two points count as coincident.
        :return: New B-spline curve.
        :rtype: BSplineCurve
        :raises BuildFailed: If the interpolation fails.
        """
        icurve = ICurve.MakeBSplineByInterpolation([p.ipoint for p in points], tol)
        return cls(icurve)

    def __init__(self, c: ICurve):
        """
        Initialize from an ICurve.

        :param ICurve c: Underlying 3D curve.
        """
        super().__init__(c)
        if c.Kind() != ICurveKind.BSpline:
            raise TypeError(f"Expected ICurveKind.BSpline, got {c.Kind()}.")


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
        :return: New surface.
        :rtype: Surface
        """
        match isurface.Kind():
            case ISurfaceKind.Cylindrical:
                return CylindricalSurface(isurface)
            case _:
                raise NotImplementedError(f"Unsupported surface kind: {isurface.Kind()}.")

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        if not isinstance(s, ISurface):
            raise TypeError(f"Expected ISurface, got {type(s).__name__}.")
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
    Represents a cylindrical surface, parameterized by u, the angle in radians about the z-direction
    from the x-direction of the frame, and v, the distance along the z-direction.
    """

    @classmethod
    def by_radius(cls, radius: float, frame: Frame | None = None) -> CylindricalSurface:
        """
        Create a cylindrical surface from radius and frame.

        :param float radius: Cylinder radius. Must not be negative.
        :param Frame | None frame: Coordinate system. Defaults to the global origin.
        :return: New cylindrical surface.
        :rtype: CylindricalSurface
        :raises RuntimeError: If the radius is negative.
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        isurface = ISurface.MakeCylindrical(frame.iframe, radius)
        return cls(isurface)

    def __init__(self, s: ISurface):
        """
        Initialize from an ISurface.

        :param ISurface s: Underlying surface.
        """
        super().__init__(s)
        if s.Kind() != ISurfaceKind.Cylindrical:
            raise TypeError(f"Expected ISurfaceKind.Cylindrical, got {s.Kind()}.")


class ProjectPointToCurve:
    """
    Tool to project a point onto a curve, finding where the line to the point is perpendicular to
    the curve.
    """

    def __init__(self, p: Point, c: Curve, u0: float | None = None, u1: float | None = None):
        """
        Initialize with a point, a curve, and an optional parameter range.

        :param Point p: Point to project.
        :param Curve c: Curve.
        :param float | None u0: Start of the range. Defaults to the start of the curve.
        :param float | None u1: End of the range. Defaults to the end of the curve.
        :raises RuntimeError: If the start of the range is after its end.
        """
        start = c.first_parameter if u0 is None else u0
        end = c.last_parameter if u1 is None else u1
        self._itool = ProjectIPointToICurve(p.ipoint, c.icurve, start, end)

    def perform(self, p: Point) -> None:
        """
        Project a new point onto the same curve and range, replacing the results.

        :param Point p: Point to project.
        """
        self._itool.Perform(p.ipoint)

    @property
    def is_done(self) -> bool:
        """
        Check if the projection has results.

        :return: True if there is at least one result.
        :rtype: bool
        """
        return self._itool.IsDone()

    @property
    def num_points(self) -> int:
        """
        Number of results.

        :return: Count.
        :rtype: int
        """
        return self._itool.NumPoints()

    def point(self, index: int) -> Point:
        """
        Get a projected point.

        :param int index: 0-based index of the result.
        :return: Point on the curve.
        :rtype: Point
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return Point(self._itool.Point(index + 1))

    def parameter(self, index: int) -> float:
        """
        Get the curve parameter of a projected point.

        :param int index: 0-based index of the result.
        :return: Curve parameter.
        :rtype: float
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return self._itool.Parameter(index + 1)

    def distance(self, index: int) -> float:
        """
        Get the distance from the point to a projected point.

        :param int index: 0-based index of the result.
        :return: Distance.
        :rtype: float
        :raises RuntimeError: If the index is out of range.
        """
        # Python is 0-based, OCCT is 1-based
        return self._itool.Distance(index + 1)

    @property
    def nearest_point(self) -> Point:
        """
        Nearest projected point.

        :return: Point on the curve.
        :rtype: Point
        :raises RuntimeError: If there are no results.
        """
        return Point(self._itool.NearestPoint())

    @property
    def nearest_parameter(self) -> float:
        """
        Curve parameter of the nearest projected point.

        :return: Curve parameter.
        :rtype: float
        :raises RuntimeError: If there are no results.
        """
        return self._itool.NearestParameter()

    @property
    def nearest_distance(self) -> float:
        """
        Distance to the nearest projected point.

        :return: Distance.
        :rtype: float
        :raises RuntimeError: If there are no results.
        """
        return self._itool.NearestDistance()
