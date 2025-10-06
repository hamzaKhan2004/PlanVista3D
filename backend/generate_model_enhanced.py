# import bpy
# import sys
# import os
# import bmesh
# import mathutils
# from mathutils import Vector
# import numpy as np

# # Check if OpenCV is available - if not, fall back to basic model
# try:
#     import cv2
#     OPENCV_AVAILABLE = True
#     print("✅ OpenCV available - blueprint analysis enabled")
# except ImportError:
#     OPENCV_AVAILABLE = False
#     print("⚠️ OpenCV not available - using fallback basic model")

# def clear_scene():
#     """Clear all objects from the scene"""
#     bpy.ops.object.select_all(action='SELECT')
#     bpy.ops.object.delete(use_global=False)

# def analyze_blueprint_image(image_path):
#     """
#     Analyze blueprint image to extract structural elements
#     Returns: dict with walls, doors, windows coordinates
#     """
#     if not OPENCV_AVAILABLE:
#         print("⚠️ OpenCV not available - returning default layout")
#         return get_default_layout()
    
#     try:
#         print(f"🔍 Analyzing blueprint: {image_path}")
        
#         # Read image
#         if not os.path.exists(image_path):
#             print(f"❌ Image file not found: {image_path}")
#             return get_default_layout()
            
#         image = cv2.imread(image_path)
#         if image is None:
#             print("❌ Could not load image - using default layout")
#             return get_default_layout()
        
#         # Convert to grayscale
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
#         # Get image dimensions for scaling
#         height, width = gray.shape
#         scale_factor = 10.0 / max(width, height)  # Scale to ~10 Blender units
        
#         # Preprocessing
#         # Apply Gaussian blur to reduce noise
#         blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
#         # Apply threshold to get binary image
#         _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
#         # Apply morphological operations to clean up
#         kernel = np.ones((3,3), np.uint8)
#         thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
#         thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
#         # Edge detection
#         edges = cv2.Canny(thresh, 50, 150)
        
#         # Find contours
#         contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
#         walls = []
#         doors = []
#         windows = []
        
#         # Process contours to identify walls
#         for contour in contours:
#             # Filter by area (ignore very small contours)
#             area = cv2.contourArea(contour)
#             if area < 100:
#                 continue
                
#             # Approximate contour to polygon
#             epsilon = 0.02 * cv2.arcLength(contour, True)
#             approx = cv2.approxPolyDP(contour, epsilon, True)
            
#             # Convert to Blender coordinates (flip Y axis and scale)
#             wall_points = []
#             for point in approx:
#                 x = (point[0][0] - width/2) * scale_factor
#                 y = (height/2 - point[0][1]) * scale_factor  # Flip Y
#                 wall_points.append((x, y, 0))
                
#             if len(wall_points) >= 3:
#                 walls.append(wall_points)
        
#         # Use Hough line detection for better wall detection
#         lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
#         line_walls = []
#         if lines is not None:
#             for line in lines:
#                 x1, y1, x2, y2 = line[0]
#                 # Convert to Blender coordinates
#                 start_x = (x1 - width/2) * scale_factor
#                 start_y = (height/2 - y1) * scale_factor
#                 end_x = (x2 - width/2) * scale_factor  
#                 end_y = (height/2 - y2) * scale_factor
                
#                 # Calculate line length
#                 length = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
                
#                 # Only keep longer lines (likely walls)
#                 if length > 1.0:
#                     line_walls.append([(start_x, start_y, 0), (end_x, end_y, 0)])
        
#         # Detect potential doors and windows (gaps in walls or smaller rectangles)
#         # This is a simplified approach - in practice, you'd use more sophisticated methods
#         small_contours = [c for c in contours if 50 < cv2.contourArea(c) < 500]
        
#         for contour in small_contours:
#             # Get bounding rectangle
#             x, y, w, h = cv2.boundingRect(contour)
            
#             # Convert to Blender coordinates
#             center_x = (x + w/2 - width/2) * scale_factor
#             center_y = (height/2 - (y + h/2)) * scale_factor
#             door_width = w * scale_factor
#             door_height = h * scale_factor
            
#             # Classify as door or window based on aspect ratio and size
#             aspect_ratio = w / h if h > 0 else 1
            
#             if 0.3 < aspect_ratio < 3.0:  # Reasonable aspect ratio
#                 if door_width > 0.5 and door_height > 1.0:  # Likely a door
#                     doors.append({
#                         'center': (center_x, center_y, 1.0),
#                         'size': (door_width, 0.2, 2.0)
#                     })
#                 elif door_width > 0.3 and door_height > 0.3:  # Likely a window
#                     windows.append({
#                         'center': (center_x, center_y, 1.5),
#                         'size': (door_width, 0.15, 1.0)
#                     })
        
#         # Combine polygon walls and line walls
#         all_walls = walls + line_walls
        
#         print(f"✅ Detected {len(all_walls)} walls, {len(doors)} doors, {len(windows)} windows")
        
#         return {
#             'walls': all_walls,
#             'doors': doors,
#             'windows': windows,
#             'scale_factor': scale_factor
#         }
        
#     except Exception as e:
#         print(f"❌ Blueprint analysis failed: {e}")
#         print("🔄 Falling back to default layout")
#         return get_default_layout()

# def get_default_layout():
#     """Return a default house layout when image analysis fails"""
#     return {
#         'walls': [
#             # Rectangular house outline
#             [(-2, -2, 0), (-2, 2, 0), (2, 2, 0), (2, -2, 0), (-2, -2, 0)]
#         ],
#         'doors': [
#             {'center': (2, 0, 1.0), 'size': (0.2, 1.0, 2.0)}
#         ],
#         'windows': [
#             {'center': (-2, -1, 1.5), 'size': (0.15, 1.0, 1.0)},
#             {'center': (-2, 1, 1.5), 'size': (0.15, 1.0, 1.0)}
#         ],
#         'scale_factor': 1.0
#     }

# def create_wall_from_points(wall_points, wall_height=3.0, wall_thickness=0.2, wall_name="Wall"):
#     """Create a wall mesh from a list of points using bmesh"""
#     try:
#         # Create bmesh
#         bm = bmesh.new()
        
#         # Create vertices for bottom face
#         bottom_verts = []
#         for point in wall_points:
#             v = bm.verts.new((point[0], point[1], 0))
#             bottom_verts.append(v)
        
#         # Create bottom face if we have enough vertices
#         if len(bottom_verts) >= 3:
#             # Remove duplicate last vertex if it matches first (closed polygon)
#             if len(bottom_verts) > 3:
#                 first_pos = bottom_verts[0].co
#                 last_pos = bottom_verts[-1].co
#                 if (first_pos - last_pos).length < 0.001:
#                     bm.verts.remove(bottom_verts[-1])
#                     bottom_verts = bottom_verts[:-1]
            
#             if len(bottom_verts) >= 3:
#                 bm.faces.new(bottom_verts)
        
#         # Update bmesh
#         bm.normal_update()
#         bm.faces.ensure_lookup_table()
        
#         # Extrude upward to create walls
#         if bm.faces:
#             faces_to_extrude = list(bm.faces)
#             extruded = bmesh.ops.extrude_face_region(bm, geom=faces_to_extrude)
            
#             # Move extruded vertices up
#             extruded_verts = [v for v in extruded["geom"] if isinstance(v, bmesh.types.BMVert)]
#             bmesh.ops.translate(bm, vec=(0, 0, wall_height), verts=extruded_verts)
        
#         # Create mesh object
#         mesh = bpy.data.meshes.new(wall_name)
#         bm.to_mesh(mesh)
#         bm.free()
        
#         # Create object
#         wall_obj = bpy.data.objects.new(wall_name, mesh)
#         bpy.context.collection.objects.link(wall_obj)
        
#         return wall_obj
        
#     except Exception as e:
#         print(f"⚠️ Wall creation failed for {wall_name}: {e}")
#         return None

# def create_line_wall(start_point, end_point, wall_height=3.0, wall_thickness=0.2, wall_name="LineWall"):
#     """Create a wall from two points (line)"""
#     try:
#         # Calculate wall direction and perpendicular
#         direction = Vector((end_point[0] - start_point[0], end_point[1] - start_point[1], 0))
#         if direction.length < 0.001:
#             return None
            
#         direction.normalize()
#         perpendicular = Vector((-direction.y, direction.x, 0)) * (wall_thickness / 2)
        
#         # Create wall rectangle points
#         wall_points = [
#             (start_point[0] - perpendicular.x, start_point[1] - perpendicular.y, 0),
#             (start_point[0] + perpendicular.x, start_point[1] + perpendicular.y, 0),
#             (end_point[0] + perpendicular.x, end_point[1] + perpendicular.y, 0),
#             (end_point[0] - perpendicular.x, end_point[1] - perpendicular.y, 0)
#         ]
        
#         return create_wall_from_points(wall_points, wall_height, wall_thickness, wall_name)
        
#     except Exception as e:
#         print(f"⚠️ Line wall creation failed: {e}")
#         return None

# def create_opening(center, size, opening_name="Opening"):
#     """Create door or window opening"""
#     try:
#         bpy.ops.mesh.primitive_cube_add(size=1, location=center)
#         opening = bpy.context.active_object
#         opening.scale = size
#         opening.name = opening_name
#         return opening
#     except Exception as e:
#         print(f"⚠️ Opening creation failed: {e}")
#         return None

# def create_model_from_analysis(analysis_data):
#     """Create 3D model from blueprint analysis results"""
#     print(f"🏗️ Creating 3D model from analysis...")
    
#     walls = analysis_data.get('walls', [])
#     doors = analysis_data.get('doors', [])
#     windows = analysis_data.get('windows', [])
    
#     created_objects = []
    
#     # Create walls
#     for i, wall in enumerate(walls):
#         wall_name = f"Wall_{i+1}"
        
#         if len(wall) == 2:  # Line wall (two points)
#             wall_obj = create_line_wall(wall[0], wall[1], wall_name=wall_name)
#         else:  # Polygon wall (multiple points)
#             wall_obj = create_wall_from_points(wall, wall_name=wall_name)
        
#         if wall_obj:
#             created_objects.append(wall_obj)
    
#     # Create floor (find bounding box of all walls)
#     if walls:
#         all_points = []
#         for wall in walls:
#             all_points.extend(wall)
        
#         if all_points:
#             xs = [p[0] for p in all_points]
#             ys = [p[1] for p in all_points]
#             min_x, max_x = min(xs), max(xs)
#             min_y, max_y = min(ys), max(ys)
            
#             # Create floor slightly larger than building footprint
#             padding = 0.5
#             floor_size_x = max_x - min_x + padding * 2
#             floor_size_y = max_y - min_y + padding * 2
#             floor_center = ((max_x + min_x) / 2, (max_y + min_y) / 2, -0.1)
            
#             bpy.ops.mesh.primitive_cube_add(size=1, location=floor_center)
#             floor = bpy.context.active_object
#             floor.scale = (floor_size_x, floor_size_y, 0.2)
#             floor.name = "Floor"
#             created_objects.append(floor)
    
#     # Create doors
#     for i, door in enumerate(doors):
#         door_obj = create_opening(door['center'], door['size'], f"Door_{i+1}")
#         if door_obj:
#             created_objects.append(door_obj)
    
#     # Create windows
#     for i, window in enumerate(windows):
#         window_obj = create_opening(window['center'], window['size'], f"Window_{i+1}")
#         if window_obj:
#             created_objects.append(window_obj)
    
#     print(f"✅ Created {len(created_objects)} objects from blueprint analysis")
#     return created_objects

# def add_materials():
#     """Add basic materials to objects"""
#     try:
#         # Create materials
#         wall_mat = bpy.data.materials.new(name="WallMaterial")
#         wall_mat.use_nodes = True
#         wall_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.7, 1.0)
        
#         floor_mat = bpy.data.materials.new(name="FloorMaterial")
#         floor_mat.use_nodes = True
#         floor_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.4, 0.3, 0.2, 1.0)
        
#         door_mat = bpy.data.materials.new(name="DoorMaterial")
#         door_mat.use_nodes = True
#         door_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.6, 0.4, 0.2, 1.0)
        
#         window_mat = bpy.data.materials.new(name="WindowMaterial")
#         window_mat.use_nodes = True
#         window_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.7, 0.9, 1.0, 0.3)
#         window_mat.node_tree.nodes["Principled BSDF"].inputs[21].default_value = 0.7  # Alpha
        
#         # Assign materials
#         for obj in bpy.context.scene.objects:
#             if obj.type == 'MESH':
#                 if "Wall" in obj.name:
#                     obj.data.materials.append(wall_mat)
#                 elif "Floor" in obj.name:
#                     obj.data.materials.append(floor_mat)
#                 elif "Door" in obj.name:
#                     obj.data.materials.append(door_mat)
#                 elif "Window" in obj.name:
#                     obj.data.materials.append(window_mat)
        
#         print("✅ Added materials to objects")
        
#     except Exception as e:
#         print(f"⚠️ Material creation failed: {e}")

# def add_lighting_and_camera():
#     """Add proper lighting and camera"""
#     try:
#         # Add sun light
#         bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
#         sun = bpy.context.active_object
#         sun.data.energy = 5
#         sun.rotation_euler = (0.785, 0, 0.524)
#         sun.name = "SunLight"
        
#         # Add area light for fill lighting
#         bpy.ops.object.light_add(type='AREA', location=(-3, -3, 6))
#         area = bpy.context.active_object
#         area.data.energy = 100
#         area.data.size = 5
#         area.name = "FillLight"
        
#         # Add camera positioned to view the building
#         bpy.ops.object.camera_add(location=(8, -8, 6))
#         camera = bpy.context.active_object
#         camera.rotation_euler = (1.0, 0, 0.785)
#         camera.name = "MainCamera"
        
#         print("✅ Added lighting and camera")
        
#     except Exception as e:
#         print(f"⚠️ Lighting setup failed: {e}")

# def main():
#     print("=== BLUEPRINT TO 3D MODEL GENERATOR (ENHANCED) ===")
#     print(f"Blender version: {bpy.app.version_string}")
    
#     # Get command line arguments
#     argv = sys.argv
#     try:
#         argv = argv[argv.index("--") + 1:]
#         print(f"Arguments: {argv}")
#     except ValueError:
#         print("ERROR: No arguments provided")
#         sys.exit(1)
    
#     if len(argv) != 2:
#         print("Usage: blender --background --python generate_model.py -- <input_path> <output_path>")
#         sys.exit(1)
    
#     input_path, output_path = argv
#     print(f"📥 Input: {input_path}")
#     print(f"📤 Output: {output_path}")
    
#     try:
#         # Check input file exists
#         if not os.path.exists(input_path):
#             print(f"❌ Input file not found: {input_path}")
#             sys.exit(1)
#         else:
#             print(f"✅ Input file found: {input_path}")
        
#         # Clear the scene
#         print("🧹 Clearing default scene...")
#         clear_scene()
        
#         # Analyze the blueprint image
#         print("🔍 Analyzing blueprint image...")
#         analysis_data = analyze_blueprint_image(input_path)
        
#         # Create the 3D model based on analysis
#         print("🏗️ Building 3D model from blueprint...")
#         created_objects = create_model_from_analysis(analysis_data)
        
#         if not created_objects:
#             print("⚠️ No objects created - creating fallback model")
#             # Fallback to basic house if analysis completely fails
#             analysis_data = get_default_layout()
#             created_objects = create_model_from_analysis(analysis_data)
        
#         # Add materials
#         print("🎨 Adding materials...")
#         add_materials()
        
#         # Add lighting and camera
#         print("💡 Setting up lighting and camera...")
#         add_lighting_and_camera()
        
#         # Export to GLB
#         print(f"💾 Exporting to GLB: {output_path}")
#         bpy.ops.export_scene.gltf(filepath=output_path)
        
#         # Verify output file was created
#         if os.path.exists(output_path):
#             file_size = os.path.getsize(output_path)
#             print(f"✅ SUCCESS! GLB file created: {output_path} ({file_size} bytes)")
            
#             # Print summary
#             walls_count = len(analysis_data.get('walls', []))
#             doors_count = len(analysis_data.get('doors', []))
#             windows_count = len(analysis_data.get('windows', []))
#             print(f"📊 Model summary: {walls_count} walls, {doors_count} doors, {windows_count} windows")
            
#         else:
#             print(f"❌ ERROR: Output file not created: {output_path}")
#             sys.exit(1)
    
#     except Exception as e:
#         print(f"❌ ERROR: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)

# if __name__ == "__main__":
#     main()
