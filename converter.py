"""
Converter module for Asymptote <-> GeoGebra conversion
"""

import re
import math
from typing import List, Dict, Any, Tuple, Optional


class AsymptoteToGeoGebra:
    """Converts Asymptote code to GeoGebra format"""
    
    def __init__(self):
        self.points = {}  # Store named points
        self.elements = []  # GeoGebra elements
        self.labels = {}  # Store labels for points
        
    def convert(self, asy_code: str) -> Dict[str, Any]:
        """
        Convert Asymptote code to GeoGebra format
        
        Returns a dictionary with:
        - ggb_commands: List of GeoGebra commands to execute
        - elements: List of element definitions for GeoGebra API
        """
        self.points = {}
        self.elements = []
        self.labels = {}
        
        lines = asy_code.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            self._parse_line(line)
        
        return {
            'ggb_commands': self._generate_ggb_commands(),
            'elements': self.elements,
            'points': self.points
        }
    
    def _parse_line(self, line: str):
        """Parse a single line of Asymptote code"""
        
        # Parse point definitions: pair A = (x, y);
        point_match = re.match(r'pair\s+(\w+)\s*=\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', line)
        if point_match:
            name, x, y = point_match.groups()
            self.points[name] = (float(x), float(y))
            return
        
        # Parse real variable: real r = value;
        real_match = re.match(r'real\s+(\w+)\s*=\s*([-\d.]+)', line)
        if real_match:
            name, value = real_match.groups()
            self.points[name] = float(value)
            return
        
        # Parse draw commands: draw(A--B--C--cycle);
        draw_match = re.match(r'draw\s*\((.+)\)', line)
        if draw_match:
            content = draw_match.group(1)
            self._parse_draw(content)
            return
        
        # Parse circle: draw(circle(O, r));
        circle_match = re.search(r'circle\s*\(\s*(\w+)\s*,\s*(\w+|\d+\.?\d*)\s*\)', line)
        if circle_match:
            center, radius = circle_match.groups()
            if center in self.points:
                cx, cy = self.points[center]
                if radius in self.points:
                    r = self.points[radius]
                else:
                    r = float(radius)
                self.elements.append({
                    'type': 'circle',
                    'center': [cx, cy],
                    'radius': r,
                    'name': f'c_{len(self.elements)}'
                })
            return
        
        # Parse dot: dot(O);
        dot_match = re.match(r'dot\s*\(\s*(\w+)\s*\)', line)
        if dot_match:
            name = dot_match.group(1)
            if name in self.points:
                x, y = self.points[name]
                self.elements.append({
                    'type': 'point',
                    'coords': [x, y],
                    'name': name
                })
            return
        
        # Parse label: label("$A$", A, SW);
        label_match = re.match(r'label\s*\(\s*"([^"]+)"\s*,\s*(\w+)\s*(?:,\s*(\w+))?\s*\)', line)
        if label_match:
            text, point_name, position = label_match.groups()
            self.labels[point_name] = text.replace('$', '')
            return
        
        # Parse graph: draw(graph(f, a, b));
        graph_match = re.search(r'graph\s*\(\s*(\w+)\s*,\s*([-\d.pi]+)\s*,\s*([-\d.pi]+)\s*\)', line)
        if graph_match:
            func_name, start, end = graph_match.groups()
            # Convert pi to actual value
            start_val = self._eval_expr(start)
            end_val = self._eval_expr(end)
            self.elements.append({
                'type': 'function',
                'function': func_name,
                'range': [start_val, end_val],
                'name': f'f_{len(self.elements)}'
            })
            return
        
        # Parse function definition: real f(real x) { return sin(x); }
        func_def_match = re.match(r'real\s+(\w+)\s*\(\s*real\s+\w+\s*\)\s*\{\s*return\s+(.+);\s*\}', line)
        if func_def_match:
            func_name, expr = func_def_match.groups()
            self.points[f'func_{func_name}'] = expr.strip()
            return
    
    def _parse_draw(self, content: str):
        """Parse draw content like A--B--C--cycle"""
        # Handle cycle keyword
        content = content.replace('--cycle', '')
        
        # Split by --
        parts = re.split(r'--', content)
        
        if len(parts) >= 2:
            # This is a path/polygon
            path_points = []
            for part in parts:
                part = part.strip()
                if part in self.points:
                    path_points.append(self.points[part])
                elif part.startswith('(') and part.endswith(')'):
                    # Inline coordinate
                    coord_match = re.match(r'\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', part)
                    if coord_match:
                        path_points.append((float(coord_match.group(1)), float(coord_match.group(2))))
            
            if len(path_points) >= 2:
                # Create line segments
                for i in range(len(path_points)):
                    p1 = path_points[i]
                    p2 = path_points[(i + 1) % len(path_points)]
                    self.elements.append({
                        'type': 'segment',
                        'start': list(p1),
                        'end': list(p2),
                        'name': f's_{len(self.elements)}'
                    })
    
    def _eval_expr(self, expr: str) -> float:
        """Evaluate simple mathematical expressions"""
        expr = expr.replace('pi', str(math.pi))
        try:
            return float(eval(expr))
        except:
            return 0.0
    
    def _generate_ggb_commands(self) -> List[str]:
        """Generate GeoGebra commands from parsed elements"""
        commands = []
        
        # First create all points
        for name, coords in self.points.items():
            if isinstance(coords, tuple):
                x, y = coords
                label = self.labels.get(name, name)
                commands.append(f'{name} = ({x}, {y})')
        
        # Then create other elements
        for elem in self.elements:
            if elem['type'] == 'circle':
                cx, cy = elem['center']
                r = elem['radius']
                commands.append(f'{elem["name"]} = Circle(({cx}, {cy}), {r})')
            elif elem['type'] == 'point':
                x, y = elem['coords']
                commands.append(f'{elem["name"]} = ({x}, {y})')
            elif elem['type'] == 'segment':
                x1, y1 = elem['start']
                x2, y2 = elem['end']
                commands.append(f'{elem["name"]} = Segment(({x1}, {y1}), ({x2}, {y2}))')
            elif elem['type'] == 'function':
                # For functions, we'd need to parse the function expression
                # This is simplified
                pass
        
        return commands


class GeoGebraToAsymptote:
    """Converts GeoGebra elements to Asymptote code"""
    
    def __init__(self):
        self.indent = "    "
        self.points_defined = set()  # Track which points have been defined
        
    def convert(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert GeoGebra elements to Asymptote code
        
        Args:
            elements: List of GeoGebra element definitions
        
        Returns a dictionary with:
        - asy_code: The generated Asymptote code
        """
        self.points_defined = set()
        
        code_lines = [
            "// Generated Asymptote code from GeoGebra",
            "size(300);",
            ""
        ]
        
        # Collect all points first
        points = {}
        point_counter = 1
        
        for elem in elements:
            if elem.get('type') == 'point':
                name = elem.get('name', f'P{point_counter}')
                coords = elem.get('coords', [0, 0])
                points[name] = coords
                point_counter += 1
        
        # Generate point definitions
        for name, coords in points.items():
            x, y = coords
            code_lines.append(f"pair {name} = ({self._format_num(x)}, {self._format_num(y)});")
            self.points_defined.add(name)
        
        if points:
            code_lines.append("")
        
        # Generate elements
        for elem in elements:
            elem_type = elem.get('type', '')
            elem_lines = self._convert_element(elem)
            code_lines.extend(elem_lines)
        
        code_lines.append("")
        
        return {
            'asy_code': '\n'.join(code_lines)
        }
    
    def _convert_element(self, elem: Dict[str, Any]) -> List[str]:
        """Convert a single element to Asymptote code"""
        lines = []
        elem_type = elem.get('type', '')
        name = elem.get('name', '')
        
        if elem_type == 'point':
            coords = elem.get('coords', [0, 0])
            label = elem.get('label', name)
            
            if name not in self.points_defined:
                lines.append(f"pair {name} = ({self._format_num(coords[0])}, {self._format_num(coords[1])});")
                self.points_defined.add(name)
            
            lines.append(f'dot({name});')
            if label and label != name:
                lines.append(f'label("${label}$", {name}, S);')
        
        elif elem_type == 'line':
            # Handle line - can be from start/end or from command
            if 'start' in elem and 'end' in elem:
                p1, p2 = elem['start'], elem['end']
                lines.append(f'draw(({self._format_num(p1[0])}, {self._format_num(p1[1])})--({self._format_num(p2[0])}, {self._format_num(p2[1])}));')
            elif 'command' in elem:
                # Parse GeoGebra command like "Line(A, B)"
                parsed = self._parse_ggb_command(elem['command'])
                if parsed:
                    lines.extend(parsed)
        
        elif elem_type == 'segment':
            if 'start' in elem and 'end' in elem:
                p1, p2 = elem['start'], elem['end']
                lines.append(f'draw(({self._format_num(p1[0])}, {self._format_num(p1[1])})--({self._format_num(p2[0])}, {self._format_num(p2[1])}));')
            elif 'command' in elem:
                parsed = self._parse_ggb_command(elem['command'])
                if parsed:
                    lines.extend(parsed)
        
        elif elem_type == 'circle':
            if 'center' in elem and 'radius' in elem:
                center = elem['center']
                radius = elem['radius']
                lines.append(f'draw(circle(({self._format_num(center[0])}, {self._format_num(center[1])}), {self._format_num(radius)}));')
            elif 'command' in elem:
                parsed = self._parse_ggb_command(elem['command'])
                if parsed:
                    lines.extend(parsed)
        
        elif elem_type == 'polygon':
            if 'vertices' in elem:
                vertices = elem['vertices']
                if len(vertices) >= 3:
                    vertex_str = '--'.join([f'({self._format_num(v[0])}, {self._format_num(v[1])})' for v in vertices])
                    lines.append(f'draw({vertex_str}--cycle);')
            elif 'command' in elem:
                parsed = self._parse_ggb_command(elem['command'])
                if parsed:
                    lines.extend(parsed)
        
        elif elem_type == 'conic' or elem_type in ['ellipse', 'hyperbola', 'parabola']:
            if 'expression' in elem:
                parsed = self._parse_ggb_command(elem['expression'])
                if parsed:
                    lines.extend(parsed)
        
        elif elem_type == 'function':
            expr = elem.get('expression', elem.get('definition', 'x'))
            # Try to convert GeoGebra function syntax to Asymptote
            asy_expr = self._convert_function_expr(expr)
            lines.append('import graph;')
            lines.append(f'real f(real x) {{ return {asy_expr}; }}')
            lines.append('draw(graph(f, -5, 5));')
        
        elif elem_type == 'vector':
            if 'vector' in elem:
                v = elem['vector']
                lines.append(f'draw((0, 0)--({self._format_num(v[0])}, {self._format_num(v[1])}), Arrow);')
        
        else:
            # Try to parse from command string
            if 'command' in elem:
                parsed = self._parse_ggb_command(elem['command'])
                if parsed:
                    lines.extend(parsed)
        
        return lines
    
    def _parse_ggb_command(self, command: str) -> List[str]:
        """Parse a GeoGebra command string and convert to Asymptote"""
        lines = []
        
        if not command:
            return lines
        
        # Extract coordinates from command patterns
        # Pattern: Point((x, y)) or (x, y)
        point_match = re.search(r'\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', command)
        
        # Pattern: Circle((cx, cy), r)
        circle_match = re.search(r'Circle\s*\(\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*,\s*([-\d.]+)\s*\)', command, re.IGNORECASE)
        if circle_match:
            cx, cy, r = circle_match.groups()
            lines.append(f'draw(circle(({self._format_num(float(cx))}, {self._format_num(float(cy))}), {self._format_num(float(r))}));')
            return lines
        
        # Pattern: Segment((x1, y1), (x2, y2))
        segment_match = re.search(r'Segment\s*\(\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*,\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*\)', command, re.IGNORECASE)
        if segment_match:
            x1, y1, x2, y2 = segment_match.groups()
            lines.append(f'draw(({self._format_num(float(x1))}, {self._format_num(float(y1))})--({self._format_num(float(x2))}, {self._format_num(float(y2))}));')
            return lines
        
        # Pattern: Line((x1, y1), (x2, y2))
        line_match = re.search(r'Line\s*\(\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*,\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)\s*\)', command, re.IGNORECASE)
        if line_match:
            x1, y1, x2, y2 = line_match.groups()
            # Extend line beyond the two points
            dx = float(x2) - float(x1)
            dy = float(y2) - float(y1)
            scale = 10
            lines.append(f'draw(({self._format_num(float(x1) - dx*scale)}, {self._format_num(float(y1) - dy*scale)})--({self._format_num(float(x2) + dx*scale)}, {self._format_num(float(y2) + dy*scale)}));')
            return lines
        
        # Pattern: Polygon((x1, y1), (x2, y2), (x3, y3), ...)
        polygon_match = re.search(r'Polygon\s*\((.+)\)', command, re.IGNORECASE)
        if polygon_match:
            coords_str = polygon_match.group(1)
            # Extract all coordinate pairs
            coords = re.findall(r'\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', coords_str)
            if len(coords) >= 3:
                vertex_str = '--'.join([f'({self._format_num(float(x))}, {self._format_num(float(y))})' for x, y in coords])
                lines.append(f'draw({vertex_str}--cycle);')
            return lines
        
        # Pattern: Function expression like f(x) = sin(x)
        func_match = re.search(r'(\w+)\s*\(\s*(\w+)\s*\)\s*=\s*(.+)', command)
        if func_match:
            func_name, var, expr = func_match.groups()
            asy_expr = self._convert_function_expr(expr)
            lines.append('import graph;')
            lines.append(f'real {func_name}(real {var}) {{ return {asy_expr}; }}')
            lines.append(f'draw(graph({func_name}, -5, 5));')
            return lines
        
        return lines
    
    def _convert_function_expr(self, expr: str) -> str:
        """Convert GeoGebra function expression to Asymptote syntax"""
        if not expr:
            return 'x'
        
        # GeoGebra uses ^ for exponentiation, Asymptote does too
        # But we need to handle implicit multiplication
        result = expr
        
        # Replace common functions (they're mostly the same)
        # sin, cos, tan, sqrt, abs, ln, log, exp are the same
        # pi -> pi (same)
        # e -> E in Asymptote
        result = re.sub(r'\be\b', 'E', result)
        
        # Handle implicit multiplication like 2x -> 2*x
        result = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', result)
        result = re.sub(r'(\d)\(', r'\1*(', result)
        
        return result
    
    def _format_num(self, num: float) -> str:
        """Format a number for output, avoiding unnecessary decimals"""
        if isinstance(num, (int, float)):
            # Round to reasonable precision
            rounded = round(num, 6)
            if rounded == int(rounded):
                return str(int(rounded))
            return str(rounded)
        return str(num)
