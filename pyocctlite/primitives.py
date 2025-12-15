from pyocctlite.geometry import Circle, Frame
from pyocctlite.topology import Edge, ExtrudeShape, Face, Solid, Wire

__all__ = ['Cylinder']


class Cylinder(Solid):

    @classmethod
    def by_size(cls, radius: float, height: float, frame: Frame):
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
        super().__init__(solid.ishape)

        self._solid = solid
        self._bottom_face = bottom_face
        self._top_face = top_face
        self._lateral_face = lateral_face

    @property
    def solid(self) -> Solid:
        return self._solid

    @property
    def bottom_face(self) -> Face:
        return self._bottom_face

    @property
    def top_face(self) -> Face:
        return self._top_face

    @property
    def lateral_face(self) -> Face:
        return self._lateral_face
