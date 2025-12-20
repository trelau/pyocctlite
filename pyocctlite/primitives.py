from pyocctlite.geometry import Circle, Frame
from pyocctlite.topology import Edge, ExtrudeShape, Face, Solid, Wire

__all__ = ['Cylinder']


class Cylinder(Solid):
    """
    Represents a cylinder.

    :ivar Solid solid: Underlying solid.
    :ivar Face bottom_face: Bottom face.
    :ivar Face top_face: Top face.
    :ivar Face lateral_face: Lateral face.
    """

    @classmethod
    def by_size(cls, radius: float, height: float, frame: Frame):
        """
        Create a cylinder from size and location.

        :param float radius: Radius.
        :param float height: Height.
        :param Frame frame: Coordinate system.
        :return: New cylinder.
        :rtype: Cylinder
        """
        # make a circle at frame of radius
        c = Circle.by_radius(frame, radius)

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
        bottom_face = f
        top_face = tool.last_shape()
        lateral_face = tool.generated_shapes(e)[0]

        # make sure shapes are the expected types
        assert isinstance(solid, Solid)
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

        self._solid = solid
        self._bottom_face = bottom_face
        self._top_face = top_face
        self._lateral_face = lateral_face

    @property
    def solid(self) -> Solid:
        """
        Underlying solid.

        :return: Solid object.
        :rtype: Solid
        """
        return self._solid

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
