# generate_model.py
import bpy
import bmesh
import sys
import os
import json
import mathutils

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # remove orphan data to keep Blender memory sane
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def create_wall_curve(vertices_px, img_w, img_h, scale_factor, thickness_norm, wall_height, name):
    """
    vertices_px: list of (x_px, y_px) coordinates (pixel coordinates from analysis)
    thickness_norm: relative to image width (normalized), we'll convert to Blender units using scale_factor
    """
    # convert to Blender coordinates: center origin? keep origin at image center offset so plan sits near origin
    pts = []
    for (nx, ny) in vertices_px:
        # vertices are normalized coordinates [0..1]. convert to blender xy
        x = (nx - 0.5) * img_w * scale_factor
        y = (0.5 - ny) * img_h * scale_factor  # flip Y so image coordinate -> Blender coordinate
        pts.append((x, y))

    # create curve
    curve_data = bpy.data.curves.new(name + "_curve", type='CURVE')
    curve_data.dimensions = '3D'
    poly = curve_data.splines.new('POLY')
    poly.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        poly.points[i].co = (x, y, 0.0, 1.0)
    # close the poly
    poly.use_cyclic_u = True

    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # thickness: convert normalized thickness to Blender units
    bevel_depth = thickness_norm * img_w * scale_factor
    if bevel_depth <= 0:
        bevel_depth = 0.02 * img_w * scale_factor  # fallback
    curve_data.bevel_depth = bevel_depth
    curve_data.extrude = wall_height  # extrude in Z

    # Give material
    mat = bpy.data.materials.new(name=f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs[0].default_value = (0.85, 0.85, 0.8, 1.0)
    curve_obj.data.materials.append(mat)
    return curve_obj

def convert_curve_to_mesh(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.convert(target='MESH')
    except Exception as e:
        print("Warning: convert failed:", e)
    obj.select_set(False)

def create_cube_at_norm_center(center_norm, w_norm, h_norm, img_w, img_h, scale_factor, depth=0.2, name="obj"):
    cx = (center_norm[0] - 0.5) * img_w * scale_factor
    cy = (0.5 - center_norm[1]) * img_h * scale_factor
    cz = depth / 2.0
    bw = w_norm * img_w * scale_factor
    bh = h_norm * img_h * scale_factor
    bd = depth * img_w * scale_factor  # depth scaled by image width
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (bw/2.0, bh/2.0, bd/2.0)
    # material
    mat = bpy.data.materials.new(name=f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs[0].default_value = (0.6, 0.3, 0.1, 1.0)
    obj.data.materials.append(mat)
    return obj

def create_floor_from_rooms(rooms, img_w, img_h, scale_factor):
    if not rooms:
        return None
    # Use union / bounding box of rooms
    minx = min(r["bounds"]["x"] for r in rooms)
    miny = min(r["bounds"]["y"] for r in rooms)
    maxx = max(r["bounds"]["x"] + r["bounds"]["width"] for r in rooms)
    maxy = max(r["bounds"]["y"] + r["bounds"]["height"] for r in rooms)

    # convert normalized coords to blender coords
    min_x = (minx - 0.5) * img_w * scale_factor
    min_y = (0.5 - maxy) * img_h * scale_factor
    max_x = (maxx - 0.5) * img_w * scale_factor
    max_y = (0.5 - miny) * img_h * scale_factor

    verts = [
        (min_x, min_y, 0),
        (max_x, min_y, 0),
        (max_x, max_y, 0),
        (min_x, max_y, 0),
    ]
    faces = [(0,1,2,3)]
    mesh = bpy.data.meshes.new("FloorMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    floor_obj = bpy.data.objects.new("Floor", mesh)
    bpy.context.collection.objects.link(floor_obj)
    mat = bpy.data.materials.new(name="Mat_Floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs[0].default_value = (0.7, 0.65, 0.55, 1.0)
    floor_obj.data.materials.append(mat)
    return floor_obj

def add_lighting(scale_factor):
    bpy.ops.object.light_add(type='SUN', location=(scale_factor, -scale_factor, scale_factor*3))
    sun = bpy.context.active_object
    sun.data.energy = 3

    bpy.ops.object.light_add(type='AREA', location=(0, 0, 4))
    area = bpy.context.active_object
    area.data.energy = 400
    area.data.size = max(1.0, scale_factor)

def add_camera(scale_factor):
    distance = scale_factor * 1.5
    bpy.ops.object.camera_add(location=(distance, -distance, distance))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.0, 0, 0.8)
    bpy.context.scene.camera = camera

def main():
    print("=== ADVANCED 3D GENERATOR ===")
    argv = sys.argv
    try:
        argv = argv[argv.index("--") + 1:]
    except ValueError:
        print("ERROR: No arguments passed to Blender script")
        sys.exit(1)

    if len(argv) != 2:
        print("ERROR: Need 2 arguments: analysis.json output.glb")
        sys.exit(1)

    analysis_file, output_path = argv
    if not os.path.exists(analysis_file):
        print("ERROR: analysis file not found:", analysis_file)
        sys.exit(1)

    with open(analysis_file, 'r') as f:
        data = json.load(f)

    scale_factor = data.get("scale_factor", 0.02)
    img_w = data.get("image_width", 800)
    img_h = data.get("image_height", 600)
    wall_height = data.get("wall_height", 3.0)

    try:
        print("Clearing scene...")
        clear_scene()

        walls = data.get("walls", [])
        doors = data.get("doors", [])
        windows = data.get("windows", [])
        rooms = data.get("rooms", [])

        print(f"Creating {len(walls)} walls...")
        created = []
        for w in walls:
            # vertices in analysis are normalized (nx,ny) so pass normalized verts
            verts_norm = w.get("vertices", [])
            wall_obj = create_wall_curve(verts_norm, img_w, img_h, scale_factor,
                                         thickness_norm=w.get("thickness", 0.02),
                                         wall_height=wall_height,
                                         name=w.get("id", "wall"))
            created.append(wall_obj)

        # Convert curves to mesh (so they are exported as solid)
        for obj in list(bpy.context.collection.all_objects):
            if obj.type == 'CURVE':
                convert_curve_to_mesh(obj)

        print(f"Creating {len(doors)} doors...")
        for d in doors:
            create_cube_at_norm_center(d["center"], d["width"], d["height"], img_w, img_h, scale_factor,
                                      depth=0.15, name=d.get("id", "door"))

        print(f"Creating {len(windows)} windows...")
        for w in windows:
            # thinner depth
            create_cube_at_norm_center(w["center"], w["width"], w["height"], img_w, img_h, scale_factor,
                                      depth=0.07, name=w.get("id", "window"))

        print("Creating floor...")
        floor = create_floor_from_rooms(rooms, img_w, img_h, scale_factor)

        print("Adding lights and camera...")
        add_lighting(max(img_w, img_h) * scale_factor * 0.25)
        add_camera(max(img_w, img_h) * scale_factor * 0.3)

        print("Exporting GLTF...")
        bpy.ops.export_scene.gltf(filepath=output_path, export_format='GLB', export_apply=True)

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"SUCCESS: {output_path} ({file_size} bytes)")
            sys.exit(0)
        else:
            print("ERROR: Output not created")
            sys.exit(1)

    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

