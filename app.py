"""
Asymptote <-> GeoGebra Converter Web Application
A tool to convert between Asymptote code and GeoGebra diagrams
"""

from flask import Flask, render_template, request, jsonify
from converter import AsymptoteToGeoGebra, GeoGebraToAsymptote
import os

app = Flask(__name__)

# Initialize converters
asy_to_ggb = AsymptoteToGeoGebra()
ggb_to_asy = GeoGebraToAsymptote()

@app.route('/')
def index():
    """Main page with the converter interface"""
    return render_template('index.html')

@app.route('/api/convert/asy-to-ggb', methods=['POST'])
def convert_asy_to_ggb():
    """Convert Asymptote code to GeoGebra format"""
    try:
        data = request.get_json()
        asy_code = data.get('code', '')
        
        if not asy_code.strip():
            return jsonify({'error': 'No Asymptote code provided'}), 400
        
        result = asy_to_ggb.convert(asy_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/ggb-to-asy', methods=['POST'])
def convert_ggb_to_asy():
    """Convert GeoGebra data to Asymptote code"""
    try:
        data = request.get_json()
        ggb_data = data.get('elements', [])
        
        if not ggb_data:
            return jsonify({'error': 'No GeoGebra elements provided'}), 400
        
        result = ggb_to_asy.convert(ggb_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/examples')
def get_examples():
    """Get example Asymptote code snippets"""
    examples = {
        'triangle': '''// Triangle with labels
size(200);
pair A = (0, 0);
pair B = (4, 0);
pair C = (2, 3);

draw(A--B--C--cycle);
label("$A$", A, SW);
label("$B$", B, SE);
label("$C$", C, N);''',
        'circle': '''// Circle with center and radius
size(200);
pair O = (2, 2);
real r = 1.5;

draw(circle(O, r));
dot(O);
label("$O$", O, S);''',
        'function': '''// Plot a function
size(200);
import graph;

real f(real x) { return sin(x); }

draw(graph(f, -pi, pi));
xaxis("$x$", BottomTop, LeftTicks);
yaxis("$y$", LeftRight, RightTicks);''',
        'polygon': '''// Regular pentagon
size(200);
int n = 5;
real r = 2;

for(int i = 0; i < n; ++i) {
    draw((r*cos(2*pi*i/n), r*sin(2*pi*i/n))--(r*cos(2*pi*(i+1)/n), r*sin(2*pi*(i+1)/n)));
}'''
    }
    return jsonify(examples)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
