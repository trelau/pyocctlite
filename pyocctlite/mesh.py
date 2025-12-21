from __future__ import annotations

from typing import Iterable, Optional

from pyocctlite._occtlite import IMesh, IMeshControl

from pyocctlite.topology import Shape

__all__ = ['MeshControl', 'Mesh']


class MeshControl:
    """
    Controls mesh generation.

    :ivar IMeshControl imeshcontrol: Underlying mesh control.
    """

    @classmethod
    def by_control_1d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None) -> MeshControl:
        """
        Create 1D mesh control.

        :param Shape shape: Shape to control.
        :param Optional[float] edge_size: Edge size.
        :param Optional[float] deflection: Deflection.
        :return: New mesh control.
        :rtype: MeshControl
        """
        c = IMeshControl.Make1D(shape.ishape, edge_size, deflection)
        return cls(c)

    @classmethod
    def by_control_2d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None, allow_quads: bool = False) -> MeshControl:
        """
        Create 2D mesh control.

        :param Shape shape: Shape to control.
        :param Optional[float] edge_size: Edge size.
        :param Optional[float] deflection: Deflection.
        :param bool allow_quads: Whether to allow quadrilaterals.
        :return: New mesh control.
        :rtype: MeshControl
        """
        c = IMeshControl.Make2D(shape.ishape, edge_size, deflection, allow_quads)
        return cls(c)

    @classmethod
    def by_control_3d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None) -> MeshControl:
        """
        Create 3D mesh control.

        :param Shape shape: Shape to control.
        :param Optional[float] edge_size: Edge size.
        :param Optional[float] deflection: Deflection.
        :return: New mesh control.
        :rtype: MeshControl
        """
        c = IMeshControl.Make3D(shape.ishape, edge_size, deflection)
        return cls(c)

    def __init__(self, c: IMeshControl):
        """
        Initialize from an IMeshControl.

        :param IMeshControl c: Underlying mesh control.
        """
        assert isinstance(c, IMeshControl)
        self._icontrol = c

    @property
    def imeshcontrol(self) -> IMeshControl:
        """
        Underlying mesh control.

        :return: IMeshControl object.
        :rtype: IMeshControl
        """
        return self._icontrol

    @property
    def edge_size(self) -> Optional[float]:
        """
        Edge size.

        :return: Size value.
        :rtype: Optional[float]
        """
        return self.imeshcontrol.EdgeSize()

    @property
    def deflection(self) -> Optional[float]:
        """
        Deflection.

        :return: Deflection value.
        :rtype: Optional[float]
        """
        return self.imeshcontrol.Deflection()

    @property
    def allow_quads(self) -> Optional[bool]:
        """
        Whether quadrilaterals are allowed.

        :return: True if allowed.
        :rtype: Optional[bool]
        """
        return self.imeshcontrol.AllowQuads()


class Mesh:
    """
    Represents a generated mesh.

    :ivar IMesh imesh: Underlying mesh.
    """

    @classmethod
    def generate(cls, shape: Shape, global_control: MeshControl, local_controls: Optional[Iterable[
        MeshControl]] = None) -> Mesh:
        """
        Generate a mesh for a shape.

        :param Shape shape: Shape to mesh.
        :param MeshControl global_control: Global mesh control.
        :param Optional[Iterable[MeshControl]] local_controls: Local mesh controls.
        :return: Generated mesh.
        :rtype: Mesh
        """
        if local_controls is None:
            imesh = IMesh.MakeMesh(shape.ishape, global_control.imeshcontrol)
        else:
            local_imeshcontrols = [c.imeshcontrol for c in local_controls]
            imesh = IMesh.MakeMesh(shape.ishape, global_control.imeshcontrol, local_imeshcontrols)
        return cls(imesh)

    def __init__(self, m: IMesh):
        """
        Initialize from an IMesh.

        :param IMesh m: Underlying mesh.
        """
        assert isinstance(m, IMesh)
        self._imesh = m

    @property
    def imesh(self) -> IMesh:
        """
        Underlying mesh.

        :return: IMesh object.
        :rtype: IMesh
        """
        return self._imesh

    @property
    def num_nodes(self) -> int:
        """
        Number of nodes in the mesh.

        :return: Node count.
        :rtype: int
        """
        return self.imesh.NumNodes()

    @property
    def num_tetras(self) -> int:
        """
        Number of tetrahedra in the mesh.

        :return: Tetrahedron count.
        :rtype: int
        """
        return self.imesh.NumTetras()

    def export_unv(self, path: str) -> None:
        """
        Export the mesh to a UNV file.

        :param str path: File path.
        :return: None
        :rtype: None
        """
        self.imesh.ExportUNV(path)
