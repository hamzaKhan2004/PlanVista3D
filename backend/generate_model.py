import sys, os
# Add user site-packages where ezdxf is installed
sys.path.append(r"C:\Users\Hamza Khan\AppData\Roaming\Python\Python311\site-packages")

import bpy
import sys
import os
import json
import bmesh
import ezdxf
from mathutils import Vector


# -------------------------------------------------
# SCENE CLEANUP
# -------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


# -------------------------------------------------
# CORE DXF → BUILDING
# -------------------------------------------------
def generate_building_from_dxf(config):
    dxf_path = config["dxf_path"]
    target_size = float(config.get("target_size", 30.0))
    wall_height = float(config.get("wall_height", 3.2))
    wall_thickness = float(config.get("wall_thickness", 0.25))
    floors = int(config.get("floors", 3))
    floor_height = float(config.get("floor_height", 3.5))
    slab_thickness = float(config.get("slab_thickness", 0.3))

    if not os.path.exists(dxf_path):
        raise RuntimeError(f"DXF file not found: {dxf_path}")

    print(f"📄 Loading DXF: {dxf_path}")
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    bm = bmesh.new()

    minx = miny = 1e9
    maxx = maxy = -1e9
    line_count = 0

    # Build wall faces from LINE entities
    for e in msp:
        if e.dxftype() != "LINE":
            continue

        p1 = Vector((e.dxf.start.x, e.dxf.start.y, 0))
        p2 = Vector((e.dxf.end.x, e.dxf.end.y, 0))

        d = p2 - p1
        if d.length < 1e-6:
            continue

        line_count += 1

        minx = min(minx, p1.x, p2.x)
        miny = min(miny, p1.y, p2.y)
        maxx = max(maxx, p1.x, p2.x)
        maxy = max(maxy, p1.y, p2.y)

        d.normalize()
        n = Vector((-d.y, d.x, 0)) * (wall_thickness / 2.0)

        try:
            v1 = bm.verts.new(p1 + n)
            v2 = bm.verts.new(p2 + n)
            v3 = bm.verts.new(p2 - n)
            v4 = bm.verts.new(p1 - n)
            bm.faces.new((v1, v2, v3, v4))
        except:
            # Ignore degenerate faces
            pass

    if line_count == 0 or not bm.faces:
        bm.free()
        raise RuntimeError("No usable LINE entities for walls in DXF")

    # Center the geometry around origin
    center = Vector(((minx + maxx) / 2.0, (miny + maxy) / 2.0, 0))
    for v in bm.verts:
        v.co -= center

    mesh = bpy.data.meshes.new("Walls")
    bm.to_mesh(mesh)
    bm.free()

    wall_obj = bpy.data.objects.new("Walls", mesh)
    bpy.context.collection.objects.link(wall_obj)

    # Auto-scale to target_size
    plan_size = max(maxx - minx, maxy - miny)
    if plan_size <= 0:
        raise RuntimeError("Invalid plan size from DXF")

    scale = target_size / plan_size
    wall_obj.scale = (scale, scale, scale)
    bpy.context.view_layer.objects.active = wall_obj
    wall_obj.select_set(True)
    bpy.ops.object.transform_apply(scale=True)

    # Extrude wall height
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, wall_height)}
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    # Floor slab (tight fit)
    bbox = [wall_obj.matrix_world @ Vector(c) for c in wall_obj.bound_box]
    minx = min(v.x for v in bbox)
    maxx = max(v.x for v in bbox)
    miny = min(v.y for v in bbox)
    maxy = max(v.y for v in bbox)

    sx = maxx - minx
    sy = maxy - miny

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, -slab_thickness / 2.0))
    slab = bpy.context.object
    slab.name = "FloorSlab"
    slab.scale = (sx / 2.0, sy / 2.0, slab_thickness / 2.0)

    # Multi-floor duplication
    floors_objs = []
    for i in range(floors):
        w = wall_obj.copy()
        w.data = wall_obj.data.copy()
        w.location.z = i * floor_height
        bpy.context.collection.objects.link(w)
        floors_objs.append(w)

        s = slab.copy()
        s.data = slab.data.copy()
        s.location.z = i * floor_height
        bpy.context.collection.objects.link(s)

    bpy.data.objects.remove(wall_obj)
    bpy.data.objects.remove(slab)

    # Material for walls
    mat = bpy.data.materials.new("WallDark")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1)
    bsdf.inputs["Roughness"].default_value = 0.7

    for o in floors_objs:
        o.data.materials.append(mat)

    # Light & camera
    bpy.ops.object.light_add(type="SUN", location=(30, -30, 50))
    bpy.context.object.data.energy = 4

    bpy.ops.object.camera_add(
        location=(25, -25, 25),
        rotation=(1.1, 0, 0.9),
    )
    bpy.context.scene.camera = bpy.context.object


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    # Blender passes its own args; we read after "--"
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Missing '--' and config arguments")

    argv = argv[argv.index("--") + 1 :]
    if len(argv) < 2:
        raise RuntimeError("Usage: blender ... --python generate_model.py -- <config.json> <output.glb>")

    config_path, output_path = argv[0], argv[1]

    if not os.path.exists(config_path):
        raise RuntimeError(f"Config JSON not found: {config_path}")

    with open(config_path, "r") as f:
        config = json.load(f)

    clear_scene()
    generate_building_from_dxf(config)

    # Export GLB
    print(f"📦 Exporting GLB to: {output_path}")
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        export_apply=True,
    )
    print("✅ Export done")


if __name__ == "__main__":
    main()
