from __future__ import annotations

from typing import Iterable, Optional

from pyocctlite._occtlite import IMesh, IMeshControl

from pyocctlite.topology import Shape

__all__ = ['MeshControl', 'Mesh']


class MeshControl:

    @classmethod
    def by_control_1d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None) -> MeshControl:
        c = IMeshControl.MakeControl1D(shape.ishape, edge_size, deflection)
        return cls(c)

    @classmethod
    def by_control_2d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None, allow_quads: bool = False) -> MeshControl:
        c = IMeshControl.MakeControl2D(shape.ishape, edge_size, deflection, allow_quads)
        return cls(c)

    @classmethod
    def by_control_3d(cls, shape: Shape, edge_size: Optional[float] = None,
                      deflection: Optional[float] = None) -> MeshControl:
        c = IMeshControl.MakeControl3D(shape.ishape, edge_size, deflection)
        return cls(c)

    def __init__(self, c: IMeshControl):
        assert isinstance(c, IMeshControl)
        self._icontrol = c

    @property
    def imeshcontrol(self) -> IMeshControl:
        return self._icontrol

    @property
    def edge_size(self) -> Optional[float]:
        return self.imeshcontrol.EdgeSize()

    @property
    def deflection(self) -> Optional[float]:
        return self.imeshcontrol.Deflection()

    @property
    def allow_quads(self) -> Optional[bool]:
        return self.imeshcontrol.AllowQuads()


class Mesh:

    @classmethod
    def generate(cls, shape: Shape, global_control: MeshControl, local_controls: Optional[Iterable[
        MeshControl]] = None) -> Mesh:
        if local_controls is None:
            imesh = IMesh.MakeMesh(shape.ishape, global_control.imeshcontrol)
        else:
            local_imeshcontrols = [c.imeshcontrol for c in local_controls]
            imesh = IMesh.MakeMesh(shape.ishape, global_control.imeshcontrol, local_imeshcontrols)
        return cls(imesh)

    def __init__(self, m: IMesh):
        assert isinstance(m, IMesh)
        self._imesh = m

    @property
    def imesh(self) -> IMesh:
        return self._imesh

    @property
    def num_nodes(self) -> int:
        return self.imesh.NumNodes()

    @property
    def num_tetras(self) -> int:
        return self.imesh.NumTetras()

    def export_unv(self, path: str) -> None:
        self.imesh.ExportUNV(path)
