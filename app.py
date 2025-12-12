import json
import math
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Patch, Rectangle, Arc
from matplotlib.lines import Line2D
from shapely.geometry import LineString, Point, Polygon
from scipy.spatial import ConvexHull
import io
import base64

matplotlib.use('Agg')

app = Flask(__name__)
if CORS:
    CORS(app)  # Enable CORS for Flutter app

class RoomPlanWallExtractor:
    def __init__(self):
        self.objects = []
        self.walls = []
        self.doors = []
        self.floors = []
        self.sections = []
        self.windows = []
        self.openings = []
        self.fig = None
        self.ax = None
        # Scaling factor (like SpriteKit example uses 200)
        self.scaling_factor = 200.0
        # Rotation angle will be calculated automatically from floor transform
        self.plan_rotation = 0.0  # Will be calculated in calculate_plan_rotation()
        
    def translate_room_name(self, room_name):
        """Translate room name to Ukrainian"""
        translations = {
            'BATHROOM': 'ВАННА КІМНАТА',
            'BEDROOM': 'СПАЛЬНЯ',
            'KITCHEN': 'КУХНЯ',
            'LIVING ROOM': 'ВІТАЛЬНЯ',
            'DINING ROOM': 'ЇДАЛЬНЯ',
            'HALL': 'ХОЛ',
            'CORRIDOR': 'КОРИДОР',
            'ROOM': 'КІМНАТА',
            'OFFICE': 'ОФІС',
            'STUDY': 'КАБІНЕТ',
            'CLOSET': 'ШАФА',
            'STORAGE': 'КОМОРА',
            'GARAGE': 'ГАРАЖ',
            'BALCONY': 'БАЛКОН',
            'TERRACE': 'ТЕРАСА',
            'ENTRANCE': 'ВХІД',
            'HALLWAY': 'ПЕРЕДПОКІЙ',
        }
        
        room_upper = room_name.upper()
        return translations.get(room_upper, room_upper)
    
    def calculate_plan_rotation(self):
        """Calculate rotation angle from floor transform (like Flutter code)"""
        if not self.floors or len(self.floors) == 0:
            return 0.0
        
        floor = self.floors[0]
        transform = floor.get('transform', [])
        
        if len(transform) < 16:
            return 0.0
        
        # Extract transform[0] and transform[2] (like Flutter: floors[0]['transform'][0] and [2])
        # Flutter code: angle1 = -atan2(floors[0]['transform'][0], floors[0]['transform'][2]) - pi/2
        transform_0 = transform[0]
        transform_2 = transform[2]
        
        # Calculate angle like Flutter code
        angle1 = -np.arctan2(transform_0, transform_2) - np.pi / 2
        
        return angle1
        
    def parse_room_plan_api(self, json_data):
        """Parse Room Plan API JSON"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
                
            # Parse main arrays - walls are in separate 'walls' array
            self.objects = data.get('objects', [])
            self.walls = data.get('walls', [])
            self.doors = data.get('doors', [])
            self.floors = data.get('floors', [])
            self.sections = data.get('sections', [])
            self.windows = data.get('windows', [])
            self.openings = data.get('openings', [])
            
            # If walls/doors/windows not in separate arrays, try to extract from objects
            if not self.walls and self.objects:
                for obj in self.objects:
                    category = obj.get('category', {})
                    obj_type = list(category.keys())[0] if category else 'unknown'
                    
                    if obj_type == 'wall':
                        self.walls.append(obj)
                    elif obj_type in ['door', 'doorway']:
                        self.doors.append(obj)
                    elif obj_type == 'window':
                        self.windows.append(obj)
                    elif obj_type == 'opening':
                        self.openings.append(obj)
            
            print(f"Parsed: {len(self.walls)} walls, {len(self.doors)} doors, {len(self.windows)} windows, {len(self.sections)} sections")
            return True
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_transform_position(self, transform):
        """Extract 3D position from 4x4 transform matrix"""
        if not transform or len(transform) < 16:
            return np.array([0, 0, 0])
        return np.array([transform[12], transform[13], transform[14]])
    
    def extract_transform_rotation(self, transform):
        """Extract rotation matrix from 4x4 transform"""
        if len(transform) < 16:
            return np.eye(3)
        return np.array([
            [transform[0], transform[1], transform[2]],
            [transform[4], transform[5], transform[6]],
            [transform[8], transform[9], transform[10]]
        ])
    
    def extract_euler_angles(self, transform):
        """Extract Euler angles from 4x4 transform matrix (like SpriteKit example)"""
        if len(transform) < 16:
            return np.array([0, 0, 0])
        
        rot = self.extract_transform_rotation(transform)
        # Extract Euler angles using the same formula as SpriteKit example
        # eulerAngles.x = asin(-rot[2][1])
        # eulerAngles.y = atan2(rot[2][0], rot[2][2])
        # eulerAngles.z = atan2(rot[0][1], rot[1][1])
        euler_x = np.arcsin(-rot[2][1])
        euler_y = np.arctan2(rot[2][0], rot[2][2])
        euler_z = np.arctan2(rot[0][1], rot[1][1])
        return np.array([euler_x, euler_y, euler_z])
    
    
    def get_wall_segments(self):
        """Extract all wall segments as lines (like SpriteKit approach)"""
        wall_segments = []
        
        for wall in self.walls:
            dims = wall.get('dimensions', [1.0, 0.2, 3.0])
            transform = wall.get('transform', [])
            
            if len(transform) < 16:
                continue
            
            # Wall length is dimensions.x (first value)
            wall_length = abs(dims[0]) if len(dims) > 0 else 1.0
            
            # Extract position and Euler angles
            position = self.extract_transform_position(transform)
            euler_angles = self.extract_euler_angles(transform)
            
            # Calculate 2D position (like SpriteKit: -x for x, z for y)
            pos_2d_x = -position[0] * self.scaling_factor
            pos_2d_y = position[2] * self.scaling_factor  # z becomes y in 2D
            
            # Calculate rotation (like SpriteKit: -(eulerAngles.z - eulerAngles.y))
            rotation = -(euler_angles[2] - euler_angles[1])
            
            # Calculate half length (wall extends from -halfLength to +halfLength)
            half_length = wall_length * self.scaling_factor / 2.0
            
            # Calculate endpoints in local coordinates (along X axis)
            point_a_local = np.array([-half_length, 0])
            point_b_local = np.array([half_length, 0])
            
            # Apply rotation to endpoints
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            
            point_a_rotated = rot_matrix @ point_a_local
            point_b_rotated = rot_matrix @ point_b_local
            
            # Translate to world position
            point_a = np.array([pos_2d_x + point_a_rotated[0], pos_2d_y + point_a_rotated[1]])
            point_b = np.array([pos_2d_x + point_b_rotated[0], pos_2d_y + point_b_rotated[1]])
            
            # Get wall identifier if available
            wall_id = wall.get('identifier', f'wall_{len(wall_segments)}')
            
            wall_segments.append({
                'point_a': point_a,
                'point_b': point_b,
                'center': [pos_2d_x, pos_2d_y],
                'length': wall_length,
                'rotation': rotation,
                'transform': transform,
                'category': 'wall',
                'id': wall_id,
                'index': len(wall_segments)  # Index for reference
            })
        
        return wall_segments
    
    def normalize_wall_angles(self, wall_segments, threshold_degrees=5.0):
        """Normalize wall angles - if deviation is small, align to axes (0°, 90°, 180°, 270°)"""
        threshold_rad = np.deg2rad(threshold_degrees)
        
        # Main axis angles: 0, π/2, π, 3π/2 (0°, 90°, 180°, 270°)
        axis_angles = [0, np.pi/2, np.pi, 3*np.pi/2]
        
        normalized_segments = []
        for segment in wall_segments:
            rotation = segment['rotation']
            center = np.array(segment['center'])
            length = segment['length'] * self.scaling_factor
            
            # Normalize rotation to [0, 2π)
            rotation_normalized = rotation % (2 * np.pi)
            if rotation_normalized < 0:
                rotation_normalized += 2 * np.pi
            
            # Find closest axis angle
            min_diff = float('inf')
            closest_axis = rotation_normalized
            
            for axis_angle in axis_angles:
                # Calculate difference (considering wrap-around)
                diff1 = abs(rotation_normalized - axis_angle)
                diff2 = abs(rotation_normalized - axis_angle + 2*np.pi)
                diff3 = abs(rotation_normalized - axis_angle - 2*np.pi)
                diff = min(diff1, diff2, diff3)
                
                if diff < min_diff:
                    min_diff = diff
                    closest_axis = axis_angle
            
            # If deviation is small, use normalized angle
            if min_diff < threshold_rad:
                normalized_rotation = closest_axis
            else:
                normalized_rotation = rotation
            
            # Recalculate points with normalized rotation
            half_length = length / 2.0
            point_a_local = np.array([-half_length, 0])
            point_b_local = np.array([half_length, 0])
            
            cos_r = np.cos(normalized_rotation)
            sin_r = np.sin(normalized_rotation)
            rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            
            point_a_rotated = rot_matrix @ point_a_local
            point_b_rotated = rot_matrix @ point_b_local
            
            point_a = center + point_a_rotated
            point_b = center + point_b_rotated
            
            normalized_segments.append({
                'point_a': point_a,
                'point_b': point_b,
                'center': center,
                'length': segment['length'],
                'rotation': normalized_rotation,
                'transform': segment['transform'],
                'category': segment['category']
            })
        
        return normalized_segments
    
    def merge_collinear_walls(self, wall_segments, threshold_distance=50.0, threshold_angle_degrees=2.0):
        """Merge wall segments that are collinear (on the same line)"""
        if len(wall_segments) == 0:
            return wall_segments
        
        threshold_angle = np.deg2rad(threshold_angle_degrees)
        merged = []
        used = set()
        
        for i, seg1 in enumerate(wall_segments):
            if i in used:
                continue
            
            # Start with this segment
            merged_group = [seg1]
            used.add(i)
            
            # Find all segments that are collinear with this one
            for j, seg2 in enumerate(wall_segments):
                if j in used or i == j:
                    continue
                
                # Check if segments are collinear
                if self._are_segments_collinear(seg1, seg2, threshold_distance, threshold_angle):
                    merged_group.append(seg2)
                    used.add(j)
            
            # Merge all collinear segments into one
            if len(merged_group) > 1:
                merged_seg = self._merge_segments(merged_group)
                merged.append(merged_seg)
            else:
                merged.append(seg1)
        
        return merged
    
    def _are_segments_collinear(self, seg1, seg2, threshold_distance, threshold_angle):
        """Check if two wall segments are collinear (on the same line)"""
        # Get direction vectors
        dir1 = seg1['point_b'] - seg1['point_a']
        dir2 = seg2['point_b'] - seg2['point_a']
        
        # Normalize
        len1 = np.linalg.norm(dir1)
        len2 = np.linalg.norm(dir2)
        
        if len1 < 1e-6 or len2 < 1e-6:
            return False
        
        dir1_norm = dir1 / len1
        dir2_norm = dir2 / len2
        
        # Check if directions are parallel (same or opposite)
        dot_product = abs(np.dot(dir1_norm, dir2_norm))
        if dot_product < np.cos(threshold_angle):
            return False  # Not parallel
        
        # Check if segments are on the same line
        # Calculate distance from seg2 endpoints to line of seg1
        p1_a = seg1['point_a']
        p1_b = seg1['point_b']
        p2_a = seg2['point_a']
        p2_b = seg2['point_b']
        
        # Distance from point to line
        def point_to_line_dist(point, line_start, line_end):
            line_vec = line_end - line_start
            point_vec = point - line_start
            line_len = np.linalg.norm(line_vec)
            if line_len < 1e-6:
                return np.linalg.norm(point - line_start)
            return abs(np.cross(line_vec, point_vec)) / line_len
        
        dist_a = point_to_line_dist(p2_a, p1_a, p1_b)
        dist_b = point_to_line_dist(p2_b, p1_a, p1_b)
        
        # If both endpoints are close to the line, segments are collinear
        if dist_a < threshold_distance and dist_b < threshold_distance:
            return True
        
        return False
    
    def _merge_segments(self, segments):
        """Merge multiple collinear segments into one"""
        # Collect all endpoints
        all_points = []
        for seg in segments:
            all_points.append(seg['point_a'])
            all_points.append(seg['point_b'])
        
        all_points = np.array(all_points)
        
        # Find the two points that are farthest apart (these are the merged endpoints)
        max_dist = 0
        best_a = None
        best_b = None
        
        for i in range(len(all_points)):
            for j in range(i + 1, len(all_points)):
                dist = np.linalg.norm(all_points[i] - all_points[j])
                if dist > max_dist:
                    max_dist = dist
                    best_a = all_points[i]
                    best_b = all_points[j]
        
        # Calculate center and rotation
        center = (best_a + best_b) / 2
        direction = best_b - best_a
        length = np.linalg.norm(direction)
        rotation = np.arctan2(direction[1], direction[0])
        
        return {
            'point_a': best_a,
            'point_b': best_b,
            'center': center,
            'length': length / self.scaling_factor,
            'rotation': rotation,
            'transform': segments[0]['transform'],  # Keep first segment's transform
            'category': 'wall'
        }
    
    def extract_door_positions(self):
        """Extract door positions as lines (like SpriteKit approach)"""
        doors = []
        
        for door in self.doors:
            dims = door.get('dimensions', [1.0, 0.1, 2.0])
            transform = door.get('transform', [])
            
            if len(transform) < 16:
                continue
            
            # Door width is dimensions.x
            door_width = abs(dims[0]) if len(dims) > 0 else 1.0
            
            # Extract position and Euler angles
            position = self.extract_transform_position(transform)
            euler_angles = self.extract_euler_angles(transform)
            
            # Calculate 2D position
            pos_2d_x = -position[0] * self.scaling_factor
            pos_2d_y = position[2] * self.scaling_factor
            
            # Calculate rotation (like SpriteKit: -(eulerAngles.z - eulerAngles.y))
            rotation = -(euler_angles[2] - euler_angles[1])
            
            # Calculate half length
            half_length = door_width * self.scaling_factor / 2.0
            
            # Calculate endpoints
            point_a_local = np.array([-half_length, 0])
            point_b_local = np.array([half_length, 0])
            
            # Apply rotation
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            
            point_a_rotated = rot_matrix @ point_a_local
            point_b_rotated = rot_matrix @ point_b_local
            
            # Translate to world position
            point_a = np.array([pos_2d_x + point_a_rotated[0], pos_2d_y + point_a_rotated[1]])
            point_b = np.array([pos_2d_x + point_b_rotated[0], pos_2d_y + point_b_rotated[1]])
            
            # Calculate point C (rotated door position for open door) - not used anymore but keep for compatibility
            door_open_angle = 0.25 * np.pi
            point_c_local = point_b_local.copy()
            # Rotate point_c_local around point_a_local
            rel_pos = point_c_local - point_a_local
            cos_open = np.cos(door_open_angle)
            sin_open = np.sin(door_open_angle)
            rot_open = np.array([[cos_open, -sin_open], [sin_open, cos_open]])
            rel_rotated = rot_open @ rel_pos
            point_c_local_rotated = point_a_local + rel_rotated
            point_c_rotated = rot_matrix @ point_c_local_rotated
            point_c = np.array([pos_2d_x + point_c_rotated[0], pos_2d_y + point_c_rotated[1]])
            
            doors.append({
                'point_a': point_a,
                'point_b': point_b,
                'point_c': point_c,
                'center': [pos_2d_x, pos_2d_y],
                'width': door_width,
                'rotation': rotation,
                'transform': transform,
                'parent_id': door.get('parentIdentifier'),
                'category': 'door'
            })
        
        return doors
    
    def extract_window_positions(self):
        """Extract window positions as lines (like SpriteKit approach)"""
        windows = []
        
        # From windows array
        for window in self.windows:
            dims = window.get('dimensions', [1.0, 0.1, 1.5])
            transform = window.get('transform', [])
            
            if len(transform) < 16:
                continue
            
            # Window width is dimensions.x
            window_width = abs(dims[0]) if len(dims) > 0 else 1.0
            
            # Extract position and Euler angles
            position = self.extract_transform_position(transform)
            euler_angles = self.extract_euler_angles(transform)
            
            # Calculate 2D position
            pos_2d_x = -position[0] * self.scaling_factor
            pos_2d_y = position[2] * self.scaling_factor
            
            # Calculate rotation (like SpriteKit: -(eulerAngles.z - eulerAngles.y))
            rotation = -(euler_angles[2] - euler_angles[1])
            
            # Calculate half length
            half_length = window_width * self.scaling_factor / 2.0
            
            # Calculate endpoints
            point_a_local = np.array([-half_length, 0])
            point_b_local = np.array([half_length, 0])
            
            # Apply rotation
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            
            point_a_rotated = rot_matrix @ point_a_local
            point_b_rotated = rot_matrix @ point_b_local
            
            # Translate to world position
            point_a = np.array([pos_2d_x + point_a_rotated[0], pos_2d_y + point_a_rotated[1]])
            point_b = np.array([pos_2d_x + point_b_rotated[0], pos_2d_y + point_b_rotated[1]])
            
            windows.append({
                'point_a': point_a,
                'point_b': point_b,
                'center': [pos_2d_x, pos_2d_y],
                'width': window_width,
                'rotation': rotation,
                'transform': transform,
                'parent_id': window.get('parentIdentifier'),
                'category': 'window'
            })
        
        return windows
    
    def calculate_room_area(self, section, wall_segments, threshold_distance=500.0):
        """Calculate room area by finding walls near the room center and building a polygon"""
        from shapely.geometry import Polygon, Point
        from shapely.ops import unary_union
        
        center_3d = section.get('center', [0, 0, 0])
        if len(center_3d) < 3:
            return 0.0
        
        # Convert section center to 2D coordinates
        pos_2d_x = -center_3d[0] * self.scaling_factor
        pos_2d_y = center_3d[2] * self.scaling_factor
        room_center_2d = np.array([pos_2d_x, pos_2d_y])
        
        # Apply plan rotation if available
        if hasattr(self, '_plan_center') and hasattr(self, '_rot_plan'):
            room_center_2d = self._rot_plan @ (room_center_2d - self._plan_center) + self._plan_center
        
        # Find walls that are close to this room center
        nearby_walls = []
        for segment in wall_segments:
            point_a = segment['point_a']
            point_b = segment['point_b']
            wall_center = (point_a + point_b) / 2
            
            # Calculate distance from room center to wall center
            distance = np.linalg.norm(room_center_2d - wall_center)
            
            if distance < threshold_distance:
                nearby_walls.append(segment)
        
        if len(nearby_walls) < 3:
            return 0.0
        
        # Collect all wall endpoints
        all_points = []
        for wall in nearby_walls:
            all_points.append(tuple(wall['point_a']))
            all_points.append(tuple(wall['point_b']))
        
        # Remove duplicates
        unique_points = list(set(all_points))
        
        if len(unique_points) < 3:
            return 0.0
        
        # Try to create a polygon from the points
        # Use convex hull as a simple approach
        try:
            from scipy.spatial import ConvexHull
            points_array = np.array(unique_points)
            hull = ConvexHull(points_array)
            
            # Get hull vertices
            hull_points = points_array[hull.vertices]
            
            # Create polygon
            polygon = Polygon(hull_points)
            
            # Calculate area in scaled units, then convert to square meters
            area_scaled = polygon.area
            area_m2 = area_scaled / (self.scaling_factor ** 2)
            
            return area_m2
        except Exception as e:
            # Fallback: try simple polygon from points sorted by angle
            try:
                # Sort points by angle from center
                center_point = np.mean(unique_points, axis=0)
                angles = [np.arctan2(p[1] - center_point[1], p[0] - center_point[0]) 
                         for p in unique_points]
                sorted_indices = np.argsort(angles)
                sorted_points = [unique_points[i] for i in sorted_indices]
                
                polygon = Polygon(sorted_points)
                area_scaled = polygon.area
                area_m2 = area_scaled / (self.scaling_factor ** 2)
                
                return area_m2
            except:
                return 0.0
    
    def extract_opening_positions(self):
        """Extract opening positions as lines (like SpriteKit approach)"""
        openings = []
        
        for opening in self.openings:
            dims = opening.get('dimensions', [1.0, 0.1, 2.0])
            transform = opening.get('transform', [])
            
            if len(transform) < 16:
                continue
            
            opening_width = abs(dims[0]) if len(dims) > 0 else 1.0
            
            position = self.extract_transform_position(transform)
            euler_angles = self.extract_euler_angles(transform)
            
            pos_2d_x = -position[0] * self.scaling_factor
            pos_2d_y = position[2] * self.scaling_factor
            # Calculate rotation (like SpriteKit: -(eulerAngles.z - eulerAngles.y))
            rotation = -(euler_angles[2] - euler_angles[1])
            
            half_length = opening_width * self.scaling_factor / 2.0
            
            point_a_local = np.array([-half_length, 0])
            point_b_local = np.array([half_length, 0])
            
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            rot_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            
            point_a_rotated = rot_matrix @ point_a_local
            point_b_rotated = rot_matrix @ point_b_local
            
            point_a = np.array([pos_2d_x + point_a_rotated[0], pos_2d_y + point_a_rotated[1]])
            point_b = np.array([pos_2d_x + point_b_rotated[0], pos_2d_y + point_b_rotated[1]])
            
            openings.append({
                'point_a': point_a,
                'point_b': point_b,
                'center': [pos_2d_x, pos_2d_y],
                'width': opening_width,
                'rotation': rotation,
                'transform': transform,
                'category': 'opening'
            })
        
        return openings
    
    def get_bounds(self):
        """Get bounds from walls and sections"""
        wall_segments = self.get_wall_segments()
        doors = self.extract_door_positions()
        windows = self.extract_window_positions()
        openings = self.extract_opening_positions()
        
        all_points = []
        for segment in wall_segments:
            all_points.append(segment['point_a'])
            all_points.append(segment['point_b'])
        
        for door in doors:
            all_points.append(door['point_a'])
            all_points.append(door['point_b'])
        
        for window in windows:
            all_points.append(window['point_a'])
            all_points.append(window['point_b'])
        
        for opening in openings:
            all_points.append(opening['point_a'])
            all_points.append(opening['point_b'])
        
        for section in self.sections:
            center = section.get('center', [0, 0, 0])
            if len(center) >= 3:
                # Convert section center to 2D coordinates
                pos_2d_x = -center[0] * self.scaling_factor
                pos_2d_y = center[2] * self.scaling_factor
                all_points.append([pos_2d_x, pos_2d_y])
        
        if len(all_points) == 0:
            return {'minX': -1000, 'maxX': 1000, 'minY': -1000, 'maxY': 1000}
        
        points_array = np.array(all_points)
        padding = 200  # Padding in scaled units
        
        return {
            'minX': float(np.min(points_array[:, 0])) - padding,
            'maxX': float(np.max(points_array[:, 0])) + padding,
            'minY': float(np.min(points_array[:, 1])) - padding,
            'maxY': float(np.max(points_array[:, 1])) + padding
        }
    
    
    def generate_floor_plan(self, wall_line_width=None):
        """Generate floor plan using SpriteKit-like approach: walls as lines"""
        # Calculate rotation angle from floor transform (like Flutter code)
        self.plan_rotation = self.calculate_plan_rotation()
        
        # Create figure first (bounds will be recalculated after rotation)
        self.fig, self.ax = plt.subplots(figsize=(16, 14), dpi=120)
        self.ax.invert_yaxis()
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.15, linestyle=':', linewidth=0.5, color='gray')
        self.ax.set_facecolor('#FAFAFA')
        self.ax.set_title('Architectural Plan', fontsize=20, fontweight='bold', pad=25, color='#333')
        self.ax.set_xlabel('X (scaled)', fontsize=13, color='#555')
        self.ax.set_ylabel('Y (scaled)', fontsize=13, color='#555')
        
        # Get all elements
        wall_segments = self.get_wall_segments()
        
        # Normalize wall angles (straighten walls that are close to axes) - disabled for now
        # wall_segments = self.normalize_wall_angles(wall_segments, threshold_degrees=2.0)
        
        # Merge collinear wall segments (combine segments on the same line) - disabled for now
        # wall_segments = self.merge_collinear_walls(wall_segments, threshold_distance=30.0, threshold_angle_degrees=1.0)
        
        doors = self.extract_door_positions()
        windows = self.extract_window_positions()
        openings = self.extract_opening_positions()
        
        # Calculate center of plan for rotation
        all_points_for_center = []
        for segment in wall_segments:
            all_points_for_center.append(segment['point_a'])
            all_points_for_center.append(segment['point_b'])
        for door in doors:
            all_points_for_center.append(door['point_a'])
            all_points_for_center.append(door['point_b'])
        for window in windows:
            all_points_for_center.append(window['point_a'])
            all_points_for_center.append(window['point_b'])
        for opening in openings:
            all_points_for_center.append(opening['point_a'])
            all_points_for_center.append(opening['point_b'])
        
        if len(all_points_for_center) > 0:
            points_array = np.array(all_points_for_center)
            plan_center = np.array([np.mean(points_array[:, 0]), np.mean(points_array[:, 1])])
        else:
            plan_center = np.array([0, 0])
        
        # Store plan center for use in label rotation
        self._plan_center = plan_center
        
        # Apply plan rotation (45 degrees clockwise) to all points relative to plan center
        cos_plan = np.cos(self.plan_rotation)
        sin_plan = np.sin(self.plan_rotation)
        rot_plan = np.array([[cos_plan, -sin_plan], [sin_plan, cos_plan]])
        
        # Store rot_plan for use in label rotation
        self._rot_plan = rot_plan
        
        # Rotate all wall segments
        for segment in wall_segments:
            segment['point_a'] = rot_plan @ (segment['point_a'] - plan_center) + plan_center
            segment['point_b'] = rot_plan @ (segment['point_b'] - plan_center) + plan_center
        
        # Rotate all doors
        for door in doors:
            door['point_a'] = rot_plan @ (door['point_a'] - plan_center) + plan_center
            door['point_b'] = rot_plan @ (door['point_b'] - plan_center) + plan_center
            if 'point_c' in door:
                door['point_c'] = rot_plan @ (door['point_c'] - plan_center) + plan_center
        
        # Rotate all windows
        for window in windows:
            window['point_a'] = rot_plan @ (window['point_a'] - plan_center) + plan_center
            window['point_b'] = rot_plan @ (window['point_b'] - plan_center) + plan_center
        
        # Rotate all openings
        for opening in openings:
            opening['point_a'] = rot_plan @ (opening['point_a'] - plan_center) + plan_center
            opening['point_b'] = rot_plan @ (opening['point_b'] - plan_center) + plan_center
        
        # Recalculate bounds after rotation
        bounds = self.get_bounds()
        self.ax.set_xlim(bounds['minX'], bounds['maxX'])
        self.ax.set_ylim(bounds['minY'], bounds['maxY'])
        
        # Define colors and line widths (like SpriteKit example)
        wall_color = '#3E3E3E'
        if wall_line_width is None:
            wall_line_width = 22.0  # Default like surfaceWidth in SpriteKit
        window_line_width = 8.0  # Same width for windows and doors
        background_color = '#FAFAFA'
        door_perpendicular_line_length = 125.0  # Fixed length for door perpendicular lines (in scaled units) - 25% longer
        
        # Z-order values (higher = on top)
        z_dimension = -1  # Dimensions behind walls
        z_wall = 0
        z_hide_surface = 1
        z_window = 10
        z_door = 10  # Same z-order as windows
        z_label = 30
        
        # Step 1: Draw walls as lines (like SpriteKit)
        for segment in wall_segments:
            point_a = segment['point_a']
            point_b = segment['point_b']
            self.ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
                        color=wall_color, linewidth=wall_line_width, 
                        zorder=z_wall, solid_capstyle='projecting')
            
            # Calculate wall length in meters
            wall_length_m = segment.get('length', np.linalg.norm(point_b - point_a) / self.scaling_factor)
            
            # Calculate wall direction and perpendicular
            wall_dir = point_b - point_a
            wall_length_px = np.linalg.norm(wall_dir)
            if wall_length_px < 1e-6:
                continue
            
            wall_dir_norm = wall_dir / wall_length_px
            perp_dir = np.array([-wall_dir_norm[1], wall_dir_norm[0]])  # Perpendicular to wall
            
            # Offset distance for dimension line (away from wall)
            dimension_offset = 40.0  # Distance from wall in pixels
            
            # Calculate dimension line position (parallel to wall, offset perpendicularly)
            dim_line_start = point_a + perp_dir * dimension_offset
            dim_line_end = point_b + perp_dir * dimension_offset
            
            # Draw dimension line (thin line parallel to wall) - behind walls
            dimension_color = '#666666'
            dimension_linewidth = 1.0
            self.ax.plot([dim_line_start[0], dim_line_end[0]], 
                        [dim_line_start[1], dim_line_end[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension, linestyle='-')
            
            # Draw extension lines (perpendicular lines from wall edge to dimension line) - behind walls
            # Extension lines start from wall edges and go to dimension line
            ext_start_a = point_a  # Start from wall edge
            ext_end_a = dim_line_start  # End at dimension line
            ext_start_b = point_b  # Start from wall edge
            ext_end_b = dim_line_end  # End at dimension line
            
            self.ax.plot([ext_start_a[0], ext_end_a[0]], 
                        [ext_start_a[1], ext_end_a[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension, linestyle='-')
            self.ax.plot([ext_start_b[0], ext_end_b[0]], 
                        [ext_start_b[1], ext_end_b[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension, linestyle='-')
            
            # Draw arrowheads at ends of dimension line - behind walls
            # Arrows pointing outward (away from wall)
            arrow_length = 8.0
            arrow_width = 3.0
            
            # Arrow at start (pointing outward, away from wall)
            arrow_dir_start = wall_dir_norm  # Pointing outward
            arrow_perp_start = perp_dir
            arrow_tip_start = dim_line_start
            arrow_base1_start = dim_line_start + arrow_dir_start * arrow_length + arrow_perp_start * arrow_width
            arrow_base2_start = dim_line_start + arrow_dir_start * arrow_length - arrow_perp_start * arrow_width
            
            self.ax.plot([arrow_tip_start[0], arrow_base1_start[0]], 
                        [arrow_tip_start[1], arrow_base1_start[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension)
            self.ax.plot([arrow_tip_start[0], arrow_base2_start[0]], 
                        [arrow_tip_start[1], arrow_base2_start[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension)
            
            # Arrow at end (pointing outward, away from wall)
            arrow_dir_end = -wall_dir_norm  # Pointing outward (opposite direction)
            arrow_perp_end = perp_dir
            arrow_tip_end = dim_line_end
            arrow_base1_end = dim_line_end + arrow_dir_end * arrow_length + arrow_perp_end * arrow_width
            arrow_base2_end = dim_line_end + arrow_dir_end * arrow_length - arrow_perp_end * arrow_width
            
            self.ax.plot([arrow_tip_end[0], arrow_base1_end[0]], 
                        [arrow_tip_end[1], arrow_base1_end[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension)
            self.ax.plot([arrow_tip_end[0], arrow_base2_end[0]], 
                        [arrow_tip_end[1], arrow_base2_end[1]],
                        color=dimension_color, linewidth=dimension_linewidth,
                        zorder=z_dimension)
            
            # Calculate center of dimension line for text placement
            dim_center = (dim_line_start + dim_line_end) / 2
            
            # Calculate angle of wall for text rotation
            wall_angle_deg = np.degrees(np.arctan2(wall_dir[1], wall_dir[0]))
            
            # Format length text (show 2 decimal places, remove trailing zeros)
            length_text = f'{wall_length_m:.2f}'.rstrip('0').rstrip('.') + 'm'
            
            # Add text label on dimension line - behind walls
            self.ax.text(dim_center[0], dim_center[1], length_text,
                        fontsize=10, ha='center', va='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                alpha=0.95, edgecolor='none', linewidth=0),
                        rotation=wall_angle_deg,
                        zorder=z_dimension, color='#333')
        
        # Step 2: Draw openings to hide walls (like SpriteKit)
        # Hide only the exact width of the opening - use same width as wall to cover it exactly
        for opening in openings:
            point_a = opening['point_a']
            point_b = opening['point_b']
            # Draw line with background color to hide wall - use wall_line_width to exactly cover the wall
            self.ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
                        color=background_color, linewidth=wall_line_width,
                        zorder=z_hide_surface, solid_capstyle='butt')
        
        # Step 3: Draw windows (hide wall first, then draw gray line along window - same style as doors)
        # Hide only the exact width of the window - use same width as wall to cover it exactly
        for window in windows:
            point_a = window['point_a']
            point_b = window['point_b']
            # Hide wall underneath - use wall_line_width to exactly cover the wall
            self.ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
                        color=background_color, linewidth=wall_line_width,
                        zorder=z_hide_surface, solid_capstyle='butt')
            
            # Draw thin gray line along window - same position and length as blue line was, but gray and thin like doors
            door_line_width = 1.5
            self.ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
                        color='#888888', linewidth=door_line_width,
                        zorder=z_window, solid_capstyle='butt')
        
        # Step 4: Draw doors (hide wall, draw gray perpendicular line)
        # Hide only the exact width of the door - use same width as wall to cover it exactly
        for i, door in enumerate(doors):
            point_a = door['point_a']
            point_b = door['point_b']
            
            # Hide wall underneath door - use wall_line_width to exactly cover the wall
            self.ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]],
                        color=background_color, linewidth=wall_line_width,
                        zorder=z_hide_surface, solid_capstyle='butt')
            
            # Draw thin gray perpendicular line in the center of the door
            # Calculate door center
            door_center = np.array([(point_a[0] + point_b[0]) / 2, (point_a[1] + point_b[1]) / 2])
            
            # Calculate door direction vector
            door_dir = point_b - point_a
            door_length = np.linalg.norm(door_dir)
            
            # Calculate perpendicular direction (rotate 90 degrees)
            perp_dir = np.array([-door_dir[1], door_dir[0]]) / door_length  # Normalized perpendicular
            
            # Draw thin gray line perpendicular to door - fixed length for all doors
            line_length = door_perpendicular_line_length
            perp_start = door_center - perp_dir * (line_length / 2)
            perp_end = door_center + perp_dir * (line_length / 2)
            
            # Use very thin line width for doors
            door_line_width = 1.5
            self.ax.plot([perp_start[0], perp_end[0]], [perp_start[1], perp_end[1]],
                        color='#888888', linewidth=door_line_width,
                        zorder=z_door, solid_capstyle='butt',
                        label='Door' if i == 0 else '')
        
        # Step 5: Draw room labels with perimeter
        for section in self.sections:
            center_3d = section.get('center', [0, 0, 0])
            if len(center_3d) >= 3:
                # Convert to 2D coordinates
                pos_2d_x = -center_3d[0] * self.scaling_factor
                pos_2d_y = center_3d[2] * self.scaling_factor
                # Apply plan rotation (use plan_center from generate_floor_plan)
                center_2d = np.array([pos_2d_x, pos_2d_y])
                # Calculate plan center if not already calculated
                if not hasattr(self, '_plan_center'):
                    self._plan_center = np.array([0, 0])
                if not hasattr(self, '_rot_plan'):
                    cos_plan = np.cos(self.plan_rotation)
                    sin_plan = np.sin(self.plan_rotation)
                    self._rot_plan = np.array([[cos_plan, -sin_plan], [sin_plan, cos_plan]])
                center_rotated = self._rot_plan @ (center_2d - self._plan_center) + self._plan_center
                label_en = section.get('label', 'Room').upper()
                label = self.translate_room_name(label_en)
                
                # Calculate room area
                room_area = self.calculate_room_area(section, wall_segments, threshold_distance=500.0)
                area_text = f'{room_area:.2f} м²'
                
                # Draw area at original position (where name was)
                self.ax.text(center_rotated[0], center_rotated[1], area_text,
                            fontsize=11, ha='center', va='center', fontweight='normal',
                            style='italic',
                            zorder=z_label, color='#666666')
                
                # Draw room name below area (where area was) - in Ukrainian
                self.ax.text(center_rotated[0], center_rotated[1] + 25, label,
                            fontsize=14, ha='center', va='center', fontweight='bold',
                            zorder=z_label, color='#333')
        
        # Legend removed per user request
        
        plt.tight_layout()
    
    def get_figure_as_base64(self):
        """Convert figure to base64"""
        if self.fig is None:
            return None
        
        buffer = io.BytesIO()
        self.fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(self.fig)
        return image_base64
    
    def get_statistics(self):
        """Get plan statistics"""
        wall_segments = self.get_wall_segments()
        doors = self.extract_door_positions()
        windows = self.extract_window_positions()
        
        # Calculate total wall length (perimeter)
        total_length = 0
        for segment in wall_segments:
            # Calculate length from point_a to point_b
            length = segment.get('length', np.linalg.norm(segment['point_b'] - segment['point_a']) / self.scaling_factor)
            total_length += length
        
        return {
            'walls': len(wall_segments),
            'doors': len(doors),
            'windows': len(windows),
            'rooms': len(self.sections),
            'room_names': [s.get('label', 'Room') for s in self.sections],
            'perimeter': float(total_length)
        }

# Converter will be created per request to avoid state issues

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Architectural Floor Plan Generator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            overflow: hidden;
        }
        .header {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        .upload-btn {
            background: #333;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .upload-btn:hover {
            background: #000;
        }
        .upload-btn input[type="file"] {
            display: none;
        }
        #fileInput { display: none; }
        #canvas {
            width: 100%;
            height: calc(100vh - 80px);
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: auto;
        }
        .canvas-image { 
            max-width: 100%; 
            max-height: 100%; 
            object-fit: contain;
        }
        .thickness-control {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            border: 1px solid #e0e0e0;
            min-width: 250px;
        }
        .thickness-control label {
            display: block;
            margin-bottom: 10px;
            font-weight: 500;
            color: #333;
            font-size: 14px;
        }
        .thickness-control input[type="range"] {
            width: 100%;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="header">
        <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
            Upload JSON
        </button>
        <input type="file" id="fileInput" accept=".json" onchange="handleFileUpload(event)">
    </div>
    
    <div id="canvas">
        <div style="text-align: center; color: #999; font-size: 18px;">
            Завантажте JSON файл для відображення плану
            </div>
        </div>
        
    <div class="thickness-control">
        <label for="wallThickness">
            Товщина стін: <span id="wallThicknessValue">0.22</span> м
        </label>
        <input type="range" id="wallThickness" min="5" max="50" value="22" step="1" 
               oninput="updateWallThickness(this.value)">
    </div>

    <script>
        let currentJsonData = '';
        
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            
                const reader = new FileReader();
            reader.onload = function(e) {
                currentJsonData = e.target.result;
                convertPlan();
            };
            reader.onerror = function() {
                alert('Помилка читання файлу');
                };
                reader.readAsText(file);
            }
        
        function updateWallThickness(value) {
            // Convert pixels to meters (1 pixel = 0.01 meter)
            const meters = (parseFloat(value) / 100).toFixed(2);
            document.getElementById('wallThicknessValue').textContent = meters;
            if (currentJsonData) {
                convertPlan();
            }
        }
        
        function convertPlan() {
            if (!currentJsonData) {
                return;
            }
            
            const canvas = document.getElementById('canvas');
            canvas.innerHTML = '<div style="text-align: center; color: #999; font-size: 18px; padding: 50px;">⏳ Генерується план...</div>';
            
            // Get value in pixels (slider works in pixels, but we display in meters)
            const wallThickness = parseFloat(document.getElementById('wallThickness').value);
            
            fetch('/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    json_data: currentJsonData,
                    wall_line_width: wallThickness
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    canvas.innerHTML = '<img src="data:image/png;base64,' + data.image + '" class="canvas-image">';
                } else {
                    canvas.innerHTML = '<div style="text-align: center; color: #c62828; font-size: 18px; padding: 50px;">❌ Помилка: ' + data.error + '</div>';
                }
            })
            .catch(err => {
                canvas.innerHTML = '<div style="text-align: center; color: #c62828; font-size: 18px; padding: 50px;">❌ Помилка: ' + err.message + '</div>';
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/load-room-json')
def load_room_json():
    """Load Room.json file directly"""
    try:
        with open('Room.json', 'r', encoding='utf-8') as f:
            json_data = f.read()
        return jsonify({
            'success': True,
            'json_data': json_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        json_str = data.get('json_data', '')
        wall_line_width = data.get('wall_line_width', None)  # Get wall thickness from request
        
        # Create new converter instance for each request
        converter = RoomPlanWallExtractor()
        converter.parse_room_plan_api(json_str)
        converter.generate_floor_plan(wall_line_width=wall_line_width)
        image_base64 = converter.get_figure_as_base64()
        stats = converter.get_statistics()
        
        return jsonify({
            'success': True,
            'image': image_base64,
            'stats': stats
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    print(f"🚀 Server starting on http://{host}:{port}")
    app.run(debug=debug, host=host, port=port)
