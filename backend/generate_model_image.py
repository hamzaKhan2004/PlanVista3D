import bpy
import sys
import os
import json


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
# MATERIALS
# -------------------------------------------------
def wall_material():
    mat = bpy.data.materials.new("WallMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 35

    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.88, 0.88, 0.88, 1)
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Specular IOR Level"].default_value = 0.2

    out = nodes.new("ShaderNodeOutputMaterial")

    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def floor_material():
    mat = bpy.data.materials.new("FloorMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (6, 6, 1)

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(
        os.path.join(os.path.dirname(__file__), "textures", "wood_floor2.jpg")
    )

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.45

    out = nodes.new("ShaderNodeOutputMaterial")

    links.new(tex_coord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def door_material():
    mat = bpy.data.materials.new("DoorMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.32, 0.15, 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    return mat


def window_material():
    mat = bpy.data.materials.new("WindowMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.7, 0.85, 1.0, 0.3)
    bsdf.inputs["Transmission"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.05
    return mat


# -------------------------------------------------
# GEOMETRY
# -------------------------------------------------
def create_wall(vertices, img_w, img_h, scale, thickness, height, name):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    poly = curve.splines.new("POLY")
    poly.points.add(len(vertices) - 1)

    for i, (nx, ny) in enumerate(vertices):
        x = (nx - 0.5) * img_w * scale
        y = (0.5 - ny) * img_h * scale
        poly.points[i].co = (x, y, 0, 1)

    poly.use_cyclic_u = True
    curve.bevel_depth = thickness * img_w * scale
    curve.extrude = height

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(wall_material())
    return obj


def convert_to_mesh(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)


def create_box(center, w, h, img_w, img_h, scale, depth, name, mat):
    cx = (center[0] - 0.5) * img_w * scale
    cy = (0.5 - center[1]) * img_h * scale
    cz = depth / 2

    bpy.ops.mesh.primitive_cube_add(location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (w * img_w * scale / 2, h * img_h * scale / 2, depth / 2)
    obj.data.materials.append(mat)
    return obj


def create_floor(rooms, img_w, img_h, scale):
    minx = min(r["bounds"]["x"] for r in rooms)
    miny = min(r["bounds"]["y"] for r in rooms)
    maxx = max(r["bounds"]["x"] + r["bounds"]["width"] for r in rooms)
    maxy = max(r["bounds"]["y"] + r["bounds"]["height"] for r in rooms)

    verts = [
        ((minx - 0.5) * img_w * scale, (0.5 - maxy) * img_h * scale, 0),
        ((maxx - 0.5) * img_w * scale, (0.5 - maxy) * img_h * scale, 0),
        ((maxx - 0.5) * img_w * scale, (0.5 - miny) * img_h * scale, 0),
        ((minx - 0.5) * img_w * scale, (0.5 - miny) * img_h * scale, 0),
    ]

    mesh = bpy.data.meshes.new("FloorMesh")
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("Floor", mesh)
    bpy.context.collection.objects.link(obj)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.unwrap()
    bpy.ops.object.mode_set(mode="OBJECT")

    obj.data.materials.append(floor_material())
    return obj


# -------------------------------------------------
# LIGHT + CAMERA
# -------------------------------------------------
def add_lighting(scale):
    bpy.ops.object.light_add(type="SUN", location=(scale, -scale, scale * 3))
    bpy.context.active_object.data.energy = 4.5

    bpy.ops.object.light_add(type="AREA", location=(0, 0, scale * 2))
    area = bpy.context.active_object
    area.data.energy = 700
    area.data.size = scale * 2


def add_camera(scale):
    bpy.ops.object.camera_add(location=(scale, -scale, scale))
    cam = bpy.context.active_object
    cam.rotation_euler = (1.15, 0, 0.9)
    bpy.context.scene.camera = cam


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]
    analysis_file, output_path = argv

    with open(analysis_file) as f:
        data = json.load(f)

    clear_scene()

    img_w = data["image_width"]
    img_h = data["image_height"]
    scale = data["scale_factor"]
    wall_h = data["wall_height"]

    for w in data["walls"]:
        obj = create_wall(
            w["vertices"],
            img_w,
            img_h,
            scale,
            w["thickness"],
            wall_h,
            w["id"],
        )
        convert_to_mesh(obj)

    for d in data["doors"]:
        create_box(
            d["center"],
            d["width"],
            d["height"],
            img_w,
            img_h,
            scale,
            0.15,
            d["id"],
            door_material(),
        )

    for w in data["windows"]:
        create_box(
            w["center"],
            w["width"],
            w["height"],
            img_w,
            img_h,
            scale,
            0.07,
            w["id"],
            window_material(),
        )

    if data["rooms"]:
        create_floor(data["rooms"], img_w, img_h, scale)

    add_lighting(max(img_w, img_h) * scale * 0.3)
    add_camera(max(img_w, img_h) * scale * 0.35)

    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        export_apply=True,
    )


if __name__ == "__main__":
    main()
