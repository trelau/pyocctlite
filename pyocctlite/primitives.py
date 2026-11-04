from __future__ import annotations

from typing import Self

from pyocctlite.geometry import Circle, Frame, Point, Transform, Vector
from pyocctlite.topology import CopyShape, Edge, ExtrudeShape, Face, Solid, TransformShape, Wire


class Cylinder(Solid):
    """
    Represents a cylinder.

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
        """
        if frame is None:
            frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, 0.0))

        # make a circle at frame of radius
        c = Circle.by_radius(radius, frame)

        # make a face from that circle
        e = Edge.by_curve(c)
        w = Wire.by_edge(e)
        f = Face.by_wire(w)

        # get vector of height in z-direction of frame
        v = frame.z_direction.scaled(height)

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

    def copy(self) -> Self:
        """
        Create a copy of this cylinder, including its named faces.

        :return: Copied cylinder.
        :rtype: Self
        """
        return self._by_history(CopyShape(self))

    def mirror(self, origin: Point, normal: Vector) -> Self:
        """
        Create a mirrored version of this cylinder, including its named faces.

        :param Point origin: Mirror origin.
        :param Vector normal: Mirror normal.
        :return: Mirrored cylinder.
        :rtype: Self
        """
        t = Transform.by_mirror(origin, normal)
        return self._by_history(TransformShape(self, t))

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
