import GeomTypes
import Geom3D
import isometry
shape = Geom3D.CompoundShape(
    simpleShapes = [
        Geom3D.SimpleShape(
            Vs = [
                GeomTypes.Vec3([1.0, 1.0, 1.0]),
                GeomTypes.Vec3([-1.0, 1.0, 1.0]),
                GeomTypes.Vec3([-1.0, -1.0, 1.0]),
                GeomTypes.Vec3([1.0, -1.0, 1.0]),
                GeomTypes.Vec3([1.0, 1.0, -1.0]),
                GeomTypes.Vec3([-1.0, 1.0, -1.0]),
                GeomTypes.Vec3([-1.0, -1.0, -1.0]),
                GeomTypes.Vec3([1.0, -1.0, -1.0]),
                GeomTypes.Vec3([1.0, 1.0, -2.0]),
                GeomTypes.Vec3([0.5, 1.0, 1.0])
            ],
            Fs = [
                [0, 1, 2, 3],
                [0, 3, 7, 4],
                [1, 0, 4, 5],
                [2, 1, 5, 6],
                [3, 2, 6, 7],
                [7, 6, 5, 4]
            ],
            Es = [],
            colors = ([[0.99609400000000003, 0.0, 0.0]], [0, 0, 0, 0, 0, 0]),
            name = "SimpleShape"
        ),
        Geom3D.SimpleShape(
            Vs = [
                GeomTypes.Vec3([0.0, 0.0, 2.0]),
                GeomTypes.Vec3([2.0, 0.0, 0.0]),
                GeomTypes.Vec3([0.0, 2.0, 0.0]),
                GeomTypes.Vec3([-2.0, 0.0, 0.0]),
                GeomTypes.Vec3([0.0, -2.0, 0.0]),
                GeomTypes.Vec3([0.0, 0.0, 2.0])
            ],
            Fs = [
                [0, 1, 2],
                [0, 2, 3],
                [0, 3, 4],
                [0, 4, 1],
                [5, 2, 1],
                [5, 3, 2],
                [5, 4, 3],
                [5, 1, 4]
            ],
            Es = [],
            colors = ([[0.99609400000000003, 0.0, 0.0]], [0, 0, 0, 0, 0, 0, 0, 0]),
            name = "SimpleShape"
        )
    ],
    name = "CompoundShape"
)
