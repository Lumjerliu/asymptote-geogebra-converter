# Asymptote ↔ GeoGebra Converter

A web application that converts between Asymptote code and interactive GeoGebra diagrams.

## Features

- **Asymptote → GeoGebra**: Convert Asymptote code to interactive GeoGebra diagrams
- **GeoGebra → Asymptote**: Create diagrams in GeoGebra and export to Asymptote code
- **Live Preview**: See your GeoGebra diagrams directly in the browser
- **Example Templates**: Pre-built examples for triangles, circles, functions, and polygons
- **Code Editor**: Syntax-highlighted code editor with line numbers

## Supported Elements

- Points with labels
- Lines and segments
- Circles (center + radius)
- Polygons
- Function plots (basic support)

## Installation

```bash
cd asymptote-geogebra-converter
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

Then open your browser to: http://localhost:5000

## Usage

### Asymptote to GeoGebra

1. Enter your Asymptote code in the editor (or load an example)
2. Click "Convert to GeoGebra"
3. View the generated GeoGebra commands and the interactive preview

### GeoGebra to Asymptote

1. Switch to "GeoGebra → Asymptote" mode
2. Create your diagram using the GeoGebra tools
3. Click "Convert to Asymptote"
4. Copy the generated Asymptote code

## Example Asymptote Code

```asy
// Triangle with labels
size(200);
pair A = (0, 0);
pair B = (4, 0);
pair C = (2, 3);

draw(A--B--C--cycle);
label("$A$", A, SW);
label("$B$", B, SE);
label("$C$", C, N);
```

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Code Editor**: CodeMirror
- **Diagrams**: GeoGebra API

## License

MIT License
