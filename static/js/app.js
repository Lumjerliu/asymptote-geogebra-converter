/**
 * Asymptote ↔ GeoGebra Converter
 * Single unified interface
 */

let asyEditor = null;
let examples = {};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initCodeEditor();
    initGeoGebra();
    initEventListeners();
    loadExamples();
});

/**
 * Initialize CodeMirror editor
 */
function initCodeEditor() {
    asyEditor = CodeMirror.fromTextArea(document.getElementById('asy-output'), {
        mode: 'text/x-csrc',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true
    });
}

/**
 * Initialize GeoGebra applet
 */
function initGeoGebra() {
    // GeoGebra app types:
    // - "geometry" = geometry tools (points, lines, circles, polygons) - BEST for this use case
    // - "graphing" = graphing calculator (limited tools)
    // - "classic" = full suite but may load slower
    
    const params = {
        appName: "geometry",
        width: 900,
        height: 500,
        showToolBar: true,
        showAlgebraInput: true,
        showMenuBar: true,
        enableShiftDragZoom: true,
        enableRightClick: true,
        showResetIcon: true,
        language: "en",
        // Border and styling
        borderColor: null,
        appletOnLoad: function(api) {
            console.log("GeoGebra loaded successfully!");
            console.log("Available tools check - applet ready");
        }
    };
    
    const applet = new GGBApplet(params, true);
    applet.inject('ggb-editor');
}

/**
 * Initialize event listeners
 */
function initEventListeners() {
    document.getElementById('convert-to-asy').addEventListener('click', convertGgbToAsy);
    document.getElementById('convert-to-ggb').addEventListener('click', convertAsyToGgb);
    document.getElementById('copy-asy').addEventListener('click', copyAsyCode);
    document.getElementById('download-asy').addEventListener('click', downloadAsyFile);
    document.getElementById('clear-ggb').addEventListener('click', clearGeoGebra);
    document.getElementById('example-select').addEventListener('change', loadExample);
}

/**
 * Load examples
 */
async function loadExamples() {
    try {
        const response = await fetch('/api/examples');
        examples = await response.json();
    } catch (error) {
        console.error('Failed to load examples:', error);
    }
}

function loadExample(event) {
    const key = event.target.value;
    if (key && examples[key]) {
        asyEditor.setValue(examples[key]);
    }
    event.target.value = '';
}

/**
 * Clear GeoGebra
 */
function clearGeoGebra() {
    if (window.ggbApplet) {
        window.ggbApplet.evalCommand('DeleteAll()');
    }
    showMessage('Cleared!', 'success');
}

/**
 * Convert GeoGebra to Asymptote
 */
async function convertGgbToAsy() {
    const ggb = window.ggbApplet;
    
    if (!ggb) {
        showMessage('GeoGebra not ready. Please wait and try again.', 'error');
        return;
    }

    try {
        const objectNames = ggb.getAllObjectNames();
        
        if (!objectNames || objectNames.length === 0) {
            showMessage('No objects found. Draw something in GeoGebra first!', 'error');
            return;
        }

        const elements = [];

        objectNames.forEach(function(name) {
            const type = ggb.getObjectType(name);
            const elem = { name: name, type: type };

            if (type === 'point') {
                elem.coords = [ggb.getXcoord(name), ggb.getYcoord(name)];
            } 
            else if (type === 'segment' || type === 'line') {
                elem.command = ggb.getCommandString(name);
            }
            else if (type === 'circle') {
                try {
                    elem.center = [ggb.getXcoord(name, 0), ggb.getYcoord(name, 0)];
                    elem.radius = ggb.getValue(name + '.r');
                } catch(e) {
                    elem.command = ggb.getCommandString(name);
                }
            }
            else if (type === 'polygon' || type === 'conic') {
                elem.command = ggb.getCommandString(name);
            }
            else {
                elem.command = ggb.getCommandString(name);
            }

            elements.push(elem);
        });

        // Send to backend
        const response = await fetch('/api/convert/ggb-to-asy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ elements: elements })
        });

        const result = await response.json();

        if (result.error) {
            showMessage(result.error, 'error');
            return;
        }

        asyEditor.setValue(result.asy_code);
        showMessage('Converted ' + elements.length + ' objects!', 'success');

    } catch (error) {
        showMessage('Conversion failed: ' + error.message, 'error');
    }
}

/**
 * Convert Asymptote to GeoGebra
 */
async function convertAsyToGgb() {
    const code = asyEditor.getValue();
    
    if (!code.trim()) {
        showMessage('Please enter Asymptote code', 'error');
        return;
    }

    try {
        const response = await fetch('/api/convert/asy-to-ggb', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });

        const result = await response.json();

        if (result.error) {
            showMessage(result.error, 'error');
            return;
        }

        // Show commands
        document.getElementById('ggb-commands-list').textContent = result.ggb_commands.join('\n');

        // Execute in GeoGebra
        if (window.ggbApplet) {
            window.ggbApplet.evalCommand('DeleteAll()');
            result.ggb_commands.forEach(function(cmd) {
                try {
                    window.ggbApplet.evalCommand(cmd);
                } catch (e) {
                    console.warn('Command failed:', cmd);
                }
            });
        }

        showMessage('Converted to GeoGebra!', 'success');

    } catch (error) {
        showMessage('Conversion failed: ' + error.message, 'error');
    }
}

/**
 * Copy code
 */
async function copyAsyCode() {
    const code = asyEditor.getValue();
    if (!code.trim()) {
        showMessage('No code to copy', 'error');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(code);
        showMessage('Copied!', 'success');
    } catch (e) {
        showMessage('Failed to copy', 'error');
    }
}

/**
 * Download file
 */
function downloadAsyFile() {
    const code = asyEditor.getValue();
    if (!code.trim()) {
        showMessage('No code to download', 'error');
        return;
    }
    
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'diagram.asy';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showMessage('Downloaded!', 'success');
}

/**
 * Show message
 */
function showMessage(text, type) {
    const existing = document.querySelector('.toast-message');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.className = 'toast-message';
    div.textContent = text;
    div.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:6px;z-index:10000;font-weight:500;';
    
    if (type === 'error') {
        div.style.background = '#fde8e8';
        div.style.color = '#c53030';
        div.style.border = '1px solid #fc8181';
    } else {
        div.style.background = '#c6f6d5';
        div.style.color = '#276749';
        div.style.border = '1px solid #68d391';
    }
    
    document.body.appendChild(div);
    
    setTimeout(function() {
        div.remove();
    }, 2500);
}

