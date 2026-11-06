from __future__ import annotations

import math
from typing import Self

from pyocctlite._occtlite import IShape
from pyocctlite.geometry import Circle, Frame, Point
from pyocctlite.topology import (
    CopyShape,
    Edge,
    ExtrudeShape,
    Face,
    Solid,
    TransformShape,
    Vertex,
    Wire,
)

# Smallest size that is distinct from zero, matching OCCT's Precision::Confusion
_MIN_SIZE = 1.0e-7


def _check_size(name: str, value: float) -> None:
    """
    Check that a size is finite and large enough for OCCT to build.

    :param str name: Name of the size, used in the error message.
    :param float value: Size to check.
    :raises ValueError: If the size is not finite or is too small.
    """
    if not _MIN_SIZE < value < math.inf:
        raise ValueError(f"Expected {name} to be finite and above {_MIN_SIZE}, got {value}.")


class Box(Solid):
    """
    Represents a box with one corner at the frame origin, extending along its positive axes.

    :ivar Face bottom_face: Bottom face (minimum z).
    :ivar Face top_face: Top face (maximum z).
    :ivar Face back_face: Back face (maximum y).
    :ivar Face front_face: Front face (minimum y).
    :ivar Face left_face: Left face (minimum x).
    :ivar Face right_face: Right face (maximum x).
    """

    @classmethod
    def by_size(cls, dx: float, dy: float, dz: float, frame: Frame | None = None) -> Box:
        """
        Create a box from size and location.

        :param float dx: Size along the x-direction of the frame.
        :param float dy: Size along the y-direction of the frame.
        :param float dz: Size along the z-direction of the frame.
        :param Frame | None frame: Coordinate system. Defaults to the global origin.
        :return: New box.
        :rtype: Box
        :raises ValueError: If a size is not finite or is too small.
        """
        _check_size("dx", dx)
        _check_size("dy", dy)
        _check_size("dz", dz)

        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        # make the corners of the bottom face in the xy-plane of the frame
        o = frame.origin
        vx = frame.x_direction.scale(dx)
        vy = frame.y_direction.scale(dy)
        v1, v2, v3, v4 = (
            Vertex.by_point(o.translate(vx.scale(a)).translate(vy.scale(b)))
            for a, b in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        )

        # make the edges between those shared corners, so that the wire keeps these same edges
        front_edge = Edge.by_vertices(v1, v2)
        right_edge = Edge.by_vertices(v2, v3)
        back_edge = Edge.by_vertices(v3, v4)
        left_edge = Edge.by_vertices(v4, v1)

        # make a face from those edges
        w = Wire.by_edges((front_edge, right_edge, back_edge, left_edge))
        f = Face.by_wire(w)

        # get vector of height in z-direction of frame
        v = frame.z_direction.scale(dz)

        # extrude that face by height
        tool = ExtrudeShape(f, v)

        # get solid
        solid = tool.shape()

        # get faces
        bottom_face = tool.first_shape()
        top_face = tool.last_shape()
        back_face = tool.generated_shapes(back_edge)[0]
        front_face = tool.generated_shapes(front_edge)[0]
        left_face = tool.generated_shapes(left_edge)[0]
        right_face = tool.generated_shapes(right_edge)[0]

        # make sure shapes are the expected types
        assert isinstance(solid, Solid)
        assert isinstance(bottom_face, Face)
        assert isinstance(top_face, Face)
        assert isinstance(back_face, Face)
        assert isinstance(front_face, Face)
        assert isinstance(left_face, Face)
        assert isinstance(right_face, Face)

        return cls(solid, bottom_face, top_face, back_face, front_face, left_face, right_face)

    def __init__(
        self,
        solid: Solid,
        bottom_face: Face,
        top_face: Face,
        back_face: Face,
        front_face: Face,
        left_face: Face,
        right_face: Face,
    ):
        """
        Initialize from component faces.

        :param Solid solid: Underlying solid.
        :param Face bottom_face: Bottom face.
        :param Face top_face: Top face.
        :param Face back_face: Back face.
        :param Face front_face: Front face.
        :param Face left_face: Left face.
        :param Face right_face: Right face.
        """
        super().__init__(solid.ishape)

        self._bottom_face = bottom_face
        self._top_face = top_face
        self._back_face = back_face
        self._front_face = front_face
        self._left_face = left_face
        self._right_face = right_face

    @property
    def bottom_face(self) -> Face:
        """
        Bottom face.

        :return: Face object.
        :rtype: Face
        """
        return self._bottom_face

    @property
    def top_face(self) -> Face:
        """
        Top face.

        :return: Face object.
        :rtype: Face
        """
        return self._top_face

    @property
    def back_face(self) -> Face:
        """
        Back face.

        :return: Face object.
        :rtype: Face
        """
        return self._back_face

    @property
    def front_face(self) -> Face:
        """
        Front face.

        :return: Face object.
        :rtype: Face
        """
        return self._front_face

    @property
    def left_face(self) -> Face:
        """
        Left face.

        :return: Face object.
        :rtype: Face
        """
        return self._left_face

    @property
    def right_face(self) -> Face:
        """
        Right face.

        :return: Face object.
        :rtype: Face
        """
        return self._right_face

    def _by_history(self, tool: CopyShape[Self] | TransformShape[Self]) -> Self:
        """
        Build a box from a kind-preserving tool by mapping each named face through its history.

        :param CopyShape[Self] | TransformShape[Self] tool: Tool applied to this box.
        :return: New box.
        :rtype: Self
        """
        return type(self)(
            tool.shape(),
            tool.modified_shape(self.bottom_face),
            tool.modified_shape(self.top_face),
            tool.modified_shape(self.back_face),
            tool.modified_shape(self.front_face),
            tool.modified_shape(self.left_face),
            tool.modified_shape(self.right_face),
        )


class Sphere(Solid):
    """
    Represents a sphere centered at the frame origin.

    :ivar Face face: Spherical face.
    """

    @classmethod
    def by_size(cls, radius: float, frame: Frame | None = None) -> Sphere:
        """
        Create a sphere from size and location.

        :param float radius: Radius.
        :param Frame | None frame: Coordinate system. Defaults to the global origin.
        :return: New sphere.
        :rtype: Sphere
        :raises ValueError: If the radius is not finite or is too small.
        """
        _check_size("radius", radius)

        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        solid = Solid(IShape.MakeSphere(frame.iframe, radius))

        # a full sphere has exactly one face
        face = solid.faces()[0]

        return cls(solid, face)

    def __init__(self, solid: Solid, face: Face):
        """
        Initialize from component faces.

        :param Solid solid: Underlying solid.
        :param Face face: Spherical face.
        """
        super().__init__(solid.ishape)

        self._face = face

    @property
    def face(self) -> Face:
        """
        Spherical face.

        :return: Face object.
        :rtype: Face
        """
        return self._face

    def _by_history(self, tool: CopyShape[Self] | TransformShape[Self]) -> Self:
        """
        Build a sphere from a kind-preserving tool by mapping its named face through its history.

        :param CopyShape[Self] | TransformShape[Self] tool: Tool applied to this sphere.
        :return: New sphere.
        :rtype: Self
        """
        return type(self)(tool.shape(), tool.modified_shape(self.face))


class Cylinder(Solid):
    """
    Represents a cylinder with its base centered at the frame origin, extending along its
    z-direction.

    :ivar Face bottom_face: Bottom face.
    :ivar Face top_face: Top face.
    :ivar Face lateral_face: Lateral face.
    """

    @classmethod
    def by_size(cls, radius: float, height: float, frame: Frame | None = None) -> Cylinder:
        """
        Create a cylinder from size and location.

        :param float radius: Radius.
        :param float height: Height.
        :param Frame | None frame: Coordinate system. Defaults to the global origin.
        :return: New cylinder.
        :rtype: Cylinder
        :raises ValueError: If a size is not finite or is too small.
        """
        _check_size("radius", radius)
        _check_size("height", height)

        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        # make a circle at frame of radius
        c = Circle.by_radius(radius, frame)

        # make a face from that circle
        e = Edge.by_curve(c)
        w = Wire.by_edge(e)
        f = Face.by_wire(w)

        # get vector of height in z-direction of frame
        v = frame.z_direction.scale(height)

        # extrude that circle by height
        tool = ExtrudeShape(f, v)

        # get solid
        solid = tool.shape()

        # get faces
        bottom_face = tool.first_shape()
        top_face = tool.last_shape()
        lateral_face = tool.generated_shapes(e)[0]

        # make sure shapes are the expected types
        assert isinstance(solid, Solid)
        assert isinstance(bottom_face, Face)
        assert isinstance(top_face, Face)
        assert isinstance(lateral_face, Face)

        return cls(solid, bottom_face, top_face, lateral_face)

    def __init__(self, solid: Solid, bottom_face: Face, top_face: Face, lateral_face: Face):
        """
        Initialize from component faces.

        :param Solid solid: Underlying solid.
        :param Face bottom_face: Bottom face.
        :param Face top_face: Top face.
        :param Face lateral_face: Lateral face.
        """
        super().__init__(solid.ishape)

        self._bottom_face = bottom_face
        self._top_face = top_face
        self._lateral_face = lateral_face

    @property
    def bottom_face(self) -> Face:
        """
        Bottom face.

        :return: Face object.
        :rtype: Face
        """
        return self._bottom_face

    @property
    def top_face(self) -> Face:
        """
        Top face.

        :return: Face object.
        :rtype: Face
        """
        return self._top_face

    @property
    def lateral_face(self) -> Face:
        """
        Lateral face.

        :return: Face object.
        :rtype: Face
        """
        return self._lateral_face

    def _by_history(self, tool: CopyShape[Self] | TransformShape[Self]) -> Self:
        """
        Build a cylinder from a kind-preserving tool by mapping each named face through its history.

        :param CopyShape[Self] | TransformShape[Self] tool: Tool applied to this cylinder.
        :return: New cylinder.
        :rtype: Self
        """
        return type(self)(
            tool.shape(),
            tool.modified_shape(self.bottom_face),
            tool.modified_shape(self.top_face),
            tool.modified_shape(self.lateral_face),
        )
