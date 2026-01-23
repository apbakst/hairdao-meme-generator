#!/usr/bin/env python3
"""
Web-based meme editor for HairDAO memes with canvas text editing.
"""
import json
import base64
import os
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from config import OUTPUT_DIR, DATA_DIR, MEME_STYLES
from scraper import load_website_content
from discord_scanner import load_discord_content
from meme_generator import generate_meme_concept
from image_creator import (
    create_meme_from_concept,
    MEME_TEMPLATES,
    download_template
)
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

PENDING_DIR = DATA_DIR / "pending"
PENDING_DIR.mkdir(exist_ok=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HairDAO Meme Generator</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #00d4aa; text-align: center; margin-bottom: 10px; }
        h2 { color: #00d4aa; margin-top: 0; border-bottom: 1px solid #0f3460; padding-bottom: 10px; }
        .tabs { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        .tab {
            padding: 10px 30px;
            background: #0f3460;
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            font-size: 16px;
        }
        .tab.active { background: #00d4aa; color: #1a1a2e; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .panel {
            background: #16213e;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #0f3460;
            margin-bottom: 20px;
        }
        label { display: block; margin: 10px 0 5px; color: #aaa; font-size: 14px; }
        input, select, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #0f3460;
            border-radius: 6px;
            background: #1a1a2e;
            color: #fff;
            font-size: 14px;
        }
        button {
            background: #00d4aa;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            margin: 3px;
        }
        button:hover { background: #00b894; }
        button.secondary { background: #0f3460; color: #fff; }
        button.danger { background: #e74c3c; color: #fff; }
        .container { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }

        /* Canvas editor styles */
        .canvas-container {
            position: relative;
            background: #0d1525;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 500px;
        }
        #meme-canvas {
            max-width: 100%;
            cursor: crosshair;
        }
        #inline-editor-wrapper {
            position: absolute;
            z-index: 100;
        }
        #inline-editor {
            background: transparent;
            border: 2px dashed rgba(0, 212, 170, 0.6);
            border-radius: 0;
            color: white;
            text-align: center;
            resize: none;
            overflow: hidden;
            outline: none;
            text-transform: uppercase;
            padding: 0;
            margin: 0;
            box-sizing: border-box;
            line-height: 1.2;
            width: 100%;
            height: 100%;
        }
        #inline-editor:focus {
            border-color: #00d4aa;
        }
        #inline-editor-done {
            position: absolute;
            bottom: -35px;
            left: 50%;
            transform: translateX(-50%);
            background: #00d4aa;
            color: #1a1a2e;
            border: none;
            padding: 6px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            white-space: nowrap;
        }
        #inline-editor-done:hover {
            background: #00ffcc;
        }
        .text-controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .text-controls.full { grid-template-columns: 1fr; }
        .color-input {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .color-input input[type="color"] {
            width: 40px;
            height: 30px;
            padding: 0;
            border: none;
            cursor: pointer;
        }
        .text-layer-item {
            background: #0f3460;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .text-layer-item.selected {
            border: 2px solid #00d4aa;
        }
        .text-layer-item:hover {
            background: #1a4a7a;
        }
        .templates-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            max-height: 150px;
            overflow-y: auto;
        }
        .template-btn {
            padding: 6px;
            font-size: 10px;
            background: #0f3460;
            color: #fff;
        }
        .template-btn:hover, .template-btn.active {
            background: #00d4aa;
            color: #1a1a2e;
        }

        /* Discord info panel */
        .discord-info {
            background: #0f3460;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .discord-info h4 {
            margin: 0 0 10px 0;
            color: #00d4aa;
        }
        .discord-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .discord-tag {
            background: #1a1a2e;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
        }
        .discord-tag:hover {
            background: #00d4aa;
            color: #1a1a2e;
        }

        /* Gallery styles */
        .gallery-controls {
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .gallery-item {
            background: #16213e;
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid transparent;
        }
        .gallery-item:hover { border-color: #00d4aa; }
        .gallery-item img {
            width: 100%;
            height: 180px;
            object-fit: contain;
            background: #0d1525;
            cursor: pointer;
        }
        .gallery-item-actions {
            padding: 8px;
            display: flex;
            gap: 5px;
            justify-content: center;
        }
        .gallery-item-actions button {
            padding: 6px 12px;
            font-size: 11px;
            margin: 0;
        }
        .batch-progress {
            background: #0f3460;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .progress-bar {
            background: #1a1a2e;
            border-radius: 4px;
            height: 15px;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-fill {
            background: #00d4aa;
            height: 100%;
            transition: width 0.3s;
        }
        .status {
            padding: 8px;
            border-radius: 6px;
            margin: 10px 0;
            text-align: center;
            font-size: 13px;
        }
        .status.loading { background: #0f3460; color: #00d4aa; }
        .status.success { background: #00d4aa22; color: #00d4aa; }
        .status.error { background: #e74c3c22; color: #e74c3c; }
    </style>
</head>
<body>
    <h1>HairDAO Meme Generator</h1>

    <div class="tabs">
        <button class="tab active" onclick="showTab('editor')">Canvas Editor</button>
        <button class="tab" onclick="showTab('gallery')">Batch Review</button>
        <button class="tab" onclick="showTab('discord')">Discord Data</button>
    </div>

    <!-- EDITOR TAB -->
    <div id="editor-tab" class="tab-content active">
        <div class="container">
            <div class="sidebar">
                <div class="panel">
                    <h2>Template</h2>
                    <div class="templates-grid">
                        {% for template in templates %}
                        <button class="template-btn" onclick="loadTemplate('{{ template }}')" id="tpl-{{ template }}">{{ template.replace('_', ' ').title()[:12] }}</button>
                        {% endfor %}
                    </div>
                    <button onclick="generateAIConcept()" style="width:100%; margin-top:10px;">Generate AI Meme Idea</button>
                </div>

                <div class="panel">
                    <h2>Text Layers</h2>
                    <div id="text-layers"></div>
                    <button onclick="addTextLayer()" style="width:100%;">+ Add Text</button>
                </div>

                <div class="panel" id="text-editor-panel" style="display:none;">
                    <h2>Edit Text</h2>
                    <div class="text-controls full">
                        <div>
                            <label>Text Content</label>
                            <textarea id="text-content" rows="2" oninput="updateSelectedText()"></textarea>
                        </div>
                    </div>
                    <div class="text-controls">
                        <div>
                            <label>Font</label>
                            <select id="text-font" onchange="updateSelectedText()">
                                <option value="Impact">Impact</option>
                                <option value="Arial Black">Arial Black</option>
                                <option value="Comic Sans MS">Comic Sans</option>
                                <option value="Helvetica">Helvetica</option>
                                <option value="Georgia">Georgia</option>
                                <option value="Verdana">Verdana</option>
                            </select>
                        </div>
                        <div>
                            <label>Size</label>
                            <input type="number" id="text-size" value="48" min="12" max="120" onchange="updateSelectedText()">
                        </div>
                    </div>
                    <div class="text-controls">
                        <div class="color-input">
                            <label>Fill</label>
                            <input type="color" id="text-color" value="#ffffff" onchange="updateSelectedText()">
                        </div>
                        <div class="color-input">
                            <label>Outline</label>
                            <input type="color" id="text-outline" value="#000000" onchange="updateSelectedText()">
                        </div>
                    </div>
                    <div class="text-controls">
                        <div>
                            <label>Outline Width</label>
                            <input type="number" id="outline-width" value="3" min="0" max="10" onchange="updateSelectedText()">
                        </div>
                        <div>
                            <label>Style</label>
                            <select id="text-style" onchange="updateSelectedText()">
                                <option value="normal">Normal</option>
                                <option value="bold">Bold</option>
                                <option value="italic">Italic</option>
                            </select>
                        </div>
                    </div>
                    <div class="text-controls">
                        <div>
                            <label>X Position</label>
                            <input type="number" id="text-x" value="0" onchange="updateSelectedText()">
                        </div>
                        <div>
                            <label>Y Position</label>
                            <input type="number" id="text-y" value="0" onchange="updateSelectedText()">
                        </div>
                    </div>
                    <div class="text-controls">
                        <div>
                            <label>Max Width (0 = no limit)</label>
                            <input type="number" id="text-maxwidth" value="0" min="0" max="1000" onchange="updateSelectedText()">
                        </div>
                        <div>
                            <label>Align</label>
                            <select id="text-align" onchange="updateSelectedText()">
                                <option value="center">Center</option>
                                <option value="left">Left</option>
                                <option value="right">Right</option>
                            </select>
                        </div>
                    </div>
                    <button onclick="deleteSelectedText()" class="danger" style="width:100%; margin-top:10px;">Delete Text</button>
                </div>

                <div class="discord-info">
                    <h4>Discord References (click to use)</h4>
                    <div class="discord-tags" id="discord-users"></div>
                </div>
            </div>

            <div class="main-area">
                <div class="panel">
                    <div class="canvas-container" id="canvas-container">
                        <canvas id="meme-canvas" width="800" height="600"></canvas>
                        <div id="inline-editor-wrapper" style="display:none;">
                            <textarea id="inline-editor"></textarea>
                            <button id="inline-editor-done" onclick="finishInlineEdit()">Done</button>
                        </div>
                    </div>
                    <div style="margin-top:15px; display:flex; gap:10px; flex-wrap:wrap;">
                        <button onclick="saveMeme()">Save to Output</button>
                        <button onclick="downloadMeme()" class="secondary">Download</button>
                        <button onclick="copyMeme()" class="secondary">Copy to Clipboard</button>
                        <button onclick="addToPending()" class="secondary">Add to Review Queue</button>
                    </div>
                    <div id="status"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- GALLERY TAB -->
    <div id="gallery-tab" class="tab-content">
        <div class="panel">
            <h2>Batch Generate & Review</h2>
            <div class="gallery-controls">
                <label style="display:flex;align-items:center;gap:8px;">
                    Generate
                    <input type="number" id="batch-count" value="5" min="1" max="20" style="width:60px;">
                    memes
                </label>
                <button onclick="generateBatch()">Generate Batch</button>
                <button class="secondary" onclick="loadPending()">Refresh</button>
                <button class="danger" onclick="clearPending()">Clear All</button>
            </div>
            <div id="batch-progress" class="batch-progress" style="display:none;">
                <div>Generating... <span id="progress-text">0/0</span></div>
                <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
            </div>
            <div id="gallery-grid" class="gallery-grid"></div>
        </div>
    </div>

    <!-- DISCORD DATA TAB -->
    <div id="discord-tab" class="tab-content">
        <div class="panel">
            <h2>Discord Community Data</h2>
            <p style="color:#888;">This data is automatically used when generating AI meme concepts. Click any item to copy it.</p>

            <h3 style="color:#00d4aa; margin-top:20px;">Active Users ({{ discord_data.active_users|length }})</h3>
            <div class="discord-tags">
                {% for user in discord_data.active_users %}
                <span class="discord-tag" onclick="copyText('{{ user }}')">{{ user }}</span>
                {% endfor %}
            </div>

            <h3 style="color:#00d4aa; margin-top:20px;">Frequent Words</h3>
            <div class="discord-tags">
                {% for word in discord_data.frequent_words[:30] %}
                <span class="discord-tag" onclick="copyText('{{ word }}')">{{ word }}</span>
                {% endfor %}
            </div>

            <h3 style="color:#00d4aa; margin-top:20px;">Memorable Messages</h3>
            {% for msg in discord_data.memorable_messages[:10] %}
            <div style="background:#0f3460; padding:10px; border-radius:6px; margin:8px 0; cursor:pointer;" onclick="copyText(`{{ msg.content|e }}`)">
                <strong style="color:#00d4aa;">{{ msg.author }}</strong>: {{ msg.content[:150] }}{% if msg.content|length > 150 %}...{% endif %}
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        // State
        let canvas, ctx;
        let baseImage = null;
        let textLayers = [];
        let selectedLayerIndex = -1;
        let isDragging = false;
        let dragOffsetX = 0, dragOffsetY = 0;
        let pendingMemes = [];

        // Inline editor
        let inlineEditor = null;
        let inlineEditorWrapper = null;
        let isInlineEditing = false;

        // Initialize
        window.onload = function() {
            canvas = document.getElementById('meme-canvas');
            ctx = canvas.getContext('2d');
            inlineEditor = document.getElementById('inline-editor');
            inlineEditorWrapper = document.getElementById('inline-editor-wrapper');

            canvas.addEventListener('mousedown', onCanvasMouseDown);
            canvas.addEventListener('mousemove', onCanvasMouseMove);
            canvas.addEventListener('mouseup', onCanvasMouseUp);
            canvas.addEventListener('dblclick', onCanvasDoubleClick);
            canvas.addEventListener('contextmenu', onCanvasRightClick);

            // Keyboard events for delete
            document.addEventListener('keydown', onKeyDown);

            // Inline editor events
            inlineEditor.addEventListener('input', onInlineEditorInput);
            inlineEditor.addEventListener('keydown', onInlineEditorKeydown);
            inlineEditorWrapper.addEventListener('mousedown', (e) => e.stopPropagation());
            inlineEditorWrapper.addEventListener('click', (e) => e.stopPropagation());

            loadTemplate('drake');
            loadDiscordUsers();
        };

        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelector(`[onclick="showTab('${tab}')"]`).classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
            if (tab === 'gallery') loadPending();
        }

        function showStatus(msg, type) {
            const el = document.getElementById('status');
            el.className = 'status ' + type;
            el.textContent = msg;
            if (type === 'success') setTimeout(() => el.textContent = '', 3000);
        }

        // Template loading
        async function loadTemplate(name) {
            document.querySelectorAll('.template-btn').forEach(b => b.classList.remove('active'));
            const btn = document.getElementById('tpl-' + name);
            if (btn) btn.classList.add('active');

            showStatus('Loading template...', 'loading');
            try {
                const response = await fetch('/get-template', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({template: name})
                });
                const data = await response.json();

                baseImage = new Image();
                baseImage.onload = function() {
                    canvas.width = baseImage.width;
                    canvas.height = baseImage.height;
                    redrawCanvas();
                    showStatus('Template loaded!', 'success');
                };
                baseImage.src = 'data:image/png;base64,' + data.image;
            } catch (e) {
                showStatus('Error loading template', 'error');
            }
        }

        // Canvas drawing
        function redrawCanvas() {
            if (!baseImage) return;

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(baseImage, 0, 0);

            textLayers.forEach((layer, index) => {
                // Skip drawing the layer being inline edited (it's shown in the textarea)
                if (isInlineEditing && index === selectedLayerIndex) {
                    return;
                }
                drawTextLayer(layer, index === selectedLayerIndex);
            });
        }

        // Wrap text to fit within maxWidth
        function wrapText(text, maxWidth) {
            if (!maxWidth || maxWidth <= 0) return [text];

            const words = text.split(' ');
            const lines = [];
            let currentLine = '';

            words.forEach(word => {
                const testLine = currentLine ? currentLine + ' ' + word : word;
                const metrics = ctx.measureText(testLine.toUpperCase());

                if (metrics.width > maxWidth && currentLine) {
                    lines.push(currentLine);
                    currentLine = word;
                } else {
                    currentLine = testLine;
                }
            });

            if (currentLine) lines.push(currentLine);
            return lines.length > 0 ? lines : [text];
        }

        function drawTextLayer(layer, isSelected) {
            ctx.save();

            const fontStyle = layer.style === 'italic' ? 'italic ' : '';
            const fontWeight = layer.style === 'bold' ? 'bold ' : '';
            ctx.font = `${fontStyle}${fontWeight}${layer.size}px "${layer.font}"`;
            ctx.textAlign = layer.align || 'center';
            ctx.textBaseline = 'middle';

            // Handle text wrapping
            const rawLines = layer.text.split('\\n');
            let allLines = [];
            rawLines.forEach(line => {
                const wrapped = wrapText(line, layer.maxWidth);
                allLines = allLines.concat(wrapped);
            });

            const lineHeight = layer.size * 1.2;
            let y = layer.y;

            // Calculate x offset based on alignment
            let xOffset = layer.x;
            if (layer.align === 'left' && layer.maxWidth > 0) {
                xOffset = layer.x - layer.maxWidth / 2;
            } else if (layer.align === 'right' && layer.maxWidth > 0) {
                xOffset = layer.x + layer.maxWidth / 2;
            }

            allLines.forEach(line => {
                // Draw outline
                if (layer.outlineWidth > 0) {
                    ctx.strokeStyle = layer.outlineColor;
                    ctx.lineWidth = layer.outlineWidth * 2;
                    ctx.lineJoin = 'round';
                    ctx.strokeText(line.toUpperCase(), xOffset, y);
                }

                // Draw fill
                ctx.fillStyle = layer.color;
                ctx.fillText(line.toUpperCase(), xOffset, y);

                y += lineHeight;
            });

            const lines = allLines;

            // Selection indicator with resize handles
            if (isSelected) {
                let boxWidth;
                if (layer.maxWidth && layer.maxWidth > 0) {
                    boxWidth = layer.maxWidth;
                } else {
                    const metrics = ctx.measureText(layer.text.toUpperCase());
                    boxWidth = metrics.width;
                }
                const boxHeight = lineHeight * lines.length;
                const boxX = layer.x - boxWidth/2;
                const boxY = layer.y - layer.size/2;

                // Draw dashed border
                ctx.strokeStyle = '#00d4aa';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.strokeRect(boxX, boxY, boxWidth, boxHeight);
                ctx.setLineDash([]);

                // Draw resize handles (small squares at edges)
                ctx.fillStyle = '#00d4aa';
                const handleSize = 8;

                // Left and right edge handles
                ctx.fillRect(boxX - handleSize/2, boxY + boxHeight/2 - handleSize/2, handleSize, handleSize);
                ctx.fillRect(boxX + boxWidth - handleSize/2, boxY + boxHeight/2 - handleSize/2, handleSize, handleSize);

                // Corner handles
                ctx.fillRect(boxX - handleSize/2, boxY - handleSize/2, handleSize, handleSize);
                ctx.fillRect(boxX + boxWidth - handleSize/2, boxY - handleSize/2, handleSize, handleSize);
                ctx.fillRect(boxX - handleSize/2, boxY + boxHeight - handleSize/2, handleSize, handleSize);
                ctx.fillRect(boxX + boxWidth - handleSize/2, boxY + boxHeight - handleSize/2, handleSize, handleSize);

                // Draw delete button (red X) at top-right outside the box
                const deleteX = boxX + boxWidth + 5;
                const deleteY = boxY - 5;
                const deleteSize = 20;

                // Red circle background
                ctx.fillStyle = '#e74c3c';
                ctx.beginPath();
                ctx.arc(deleteX + deleteSize/2, deleteY - deleteSize/2, deleteSize/2, 0, Math.PI * 2);
                ctx.fill();

                // White X
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(deleteX + 5, deleteY - deleteSize + 5);
                ctx.lineTo(deleteX + deleteSize - 5, deleteY - 5);
                ctx.moveTo(deleteX + deleteSize - 5, deleteY - deleteSize + 5);
                ctx.lineTo(deleteX + 5, deleteY - 5);
                ctx.stroke();
            }

            ctx.restore();
        }

        // Text layer management
        function addTextLayer(text = 'YOUR TEXT HERE') {
            const layer = {
                text: text,
                x: canvas.width / 2,
                y: textLayers.length === 0 ? 50 : canvas.height - 50,
                font: 'Impact',
                size: 48,
                color: '#ffffff',
                outlineColor: '#000000',
                outlineWidth: 3,
                style: 'normal',
                maxWidth: 300,
                align: 'center'
            };
            textLayers.push(layer);
            selectLayer(textLayers.length - 1);
            updateLayersList();
            redrawCanvas();
        }

        function selectLayer(index) {
            selectedLayerIndex = index;
            updateLayersList();

            const panel = document.getElementById('text-editor-panel');
            if (index >= 0 && index < textLayers.length) {
                const layer = textLayers[index];
                document.getElementById('text-content').value = layer.text;
                document.getElementById('text-font').value = layer.font;
                document.getElementById('text-size').value = layer.size;
                document.getElementById('text-color').value = layer.color;
                document.getElementById('text-outline').value = layer.outlineColor;
                document.getElementById('outline-width').value = layer.outlineWidth;
                document.getElementById('text-style').value = layer.style;
                document.getElementById('text-x').value = Math.round(layer.x);
                document.getElementById('text-y').value = Math.round(layer.y);
                document.getElementById('text-maxwidth').value = layer.maxWidth || 0;
                document.getElementById('text-align').value = layer.align || 'center';
                panel.style.display = 'block';
            } else {
                panel.style.display = 'none';
            }
            redrawCanvas();
        }

        function updateSelectedText() {
            if (selectedLayerIndex < 0) return;
            const layer = textLayers[selectedLayerIndex];
            layer.text = document.getElementById('text-content').value;
            layer.font = document.getElementById('text-font').value;
            layer.size = parseInt(document.getElementById('text-size').value);
            layer.color = document.getElementById('text-color').value;
            layer.outlineColor = document.getElementById('text-outline').value;
            layer.outlineWidth = parseInt(document.getElementById('outline-width').value);
            layer.style = document.getElementById('text-style').value;
            layer.x = parseInt(document.getElementById('text-x').value);
            layer.y = parseInt(document.getElementById('text-y').value);
            layer.maxWidth = parseInt(document.getElementById('text-maxwidth').value) || 0;
            layer.align = document.getElementById('text-align').value;
            updateLayersList();
            redrawCanvas();
        }

        function deleteSelectedText() {
            if (selectedLayerIndex >= 0) {
                textLayers.splice(selectedLayerIndex, 1);
                selectedLayerIndex = -1;
                document.getElementById('text-editor-panel').style.display = 'none';
                updateLayersList();
                redrawCanvas();
            }
        }

        function updateLayersList() {
            const container = document.getElementById('text-layers');
            container.innerHTML = textLayers.map((layer, i) => `
                <div class="text-layer-item ${i === selectedLayerIndex ? 'selected' : ''}" onclick="selectLayer(${i})">
                    <span>${layer.text.substring(0, 20)}${layer.text.length > 20 ? '...' : ''}</span>
                    <span style="color:#888; font-size:11px;">${layer.size}px</span>
                </div>
            `).join('');
        }

        // Mouse interactions for dragging and resizing
        let isResizing = false;
        let resizeHandle = null; // 'left', 'right', 'top', 'bottom', or corner combinations

        function getBoxBounds(layer) {
            const lineHeight = layer.size * 1.2;
            ctx.font = `${layer.size}px "${layer.font}"`;

            // Calculate wrapped lines to get height
            const rawLines = layer.text.split('\\n');
            let allLines = [];
            rawLines.forEach(line => {
                const wrapped = wrapText(line, layer.maxWidth);
                allLines = allLines.concat(wrapped);
            });

            const boxWidth = (layer.maxWidth && layer.maxWidth > 0) ? layer.maxWidth : ctx.measureText(layer.text.toUpperCase()).width;
            const boxHeight = lineHeight * allLines.length;

            return {
                left: layer.x - boxWidth / 2,
                right: layer.x + boxWidth / 2,
                top: layer.y - layer.size / 2,
                bottom: layer.y - layer.size / 2 + boxHeight,
                width: boxWidth,
                height: boxHeight
            };
        }

        function getResizeHandle(x, y, bounds) {
            const handleSize = 15;

            // Check corners first
            if (Math.abs(x - bounds.right) < handleSize && Math.abs(y - bounds.top) < handleSize) return 'top-right';
            if (Math.abs(x - bounds.left) < handleSize && Math.abs(y - bounds.top) < handleSize) return 'top-left';
            if (Math.abs(x - bounds.right) < handleSize && Math.abs(y - bounds.bottom) < handleSize) return 'bottom-right';
            if (Math.abs(x - bounds.left) < handleSize && Math.abs(y - bounds.bottom) < handleSize) return 'bottom-left';

            // Check edges
            if (Math.abs(x - bounds.right) < handleSize && y > bounds.top && y < bounds.bottom) return 'right';
            if (Math.abs(x - bounds.left) < handleSize && y > bounds.top && y < bounds.bottom) return 'left';

            return null;
        }

        function onCanvasMouseDown(e) {
            // Hide inline editor if clicking on canvas (not on the editor itself)
            if (isInlineEditing) {
                hideInlineEditor();
                redrawCanvas();
            }

            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            // If a layer is selected, check for delete button and resize handles first
            if (selectedLayerIndex >= 0) {
                const layer = textLayers[selectedLayerIndex];
                const bounds = getBoxBounds(layer);

                // Check for delete button click (top-right outside the box)
                const deleteX = bounds.right + 5;
                const deleteY = bounds.top - 5;
                const deleteSize = 20;
                const deleteCenterX = deleteX + deleteSize/2;
                const deleteCenterY = deleteY - deleteSize/2;
                const distToDelete = Math.sqrt(Math.pow(x - deleteCenterX, 2) + Math.pow(y - deleteCenterY, 2));

                if (distToDelete <= deleteSize/2 + 5) {
                    deleteSelectedLayer();
                    return;
                }

                // Check for resize handles
                const handle = getResizeHandle(x, y, bounds);
                if (handle) {
                    isResizing = true;
                    resizeHandle = handle;
                    return;
                }
            }

            // Check if clicked on a text layer
            for (let i = textLayers.length - 1; i >= 0; i--) {
                const layer = textLayers[i];
                const bounds = getBoxBounds(layer);

                if (x >= bounds.left - 10 && x <= bounds.right + 10 &&
                    y >= bounds.top - 10 && y <= bounds.bottom + 10) {
                    selectLayer(i);
                    isDragging = true;
                    dragOffsetX = x - layer.x;
                    dragOffsetY = y - layer.y;
                    return;
                }
            }

            // Clicked on empty space - just deselect
            selectLayer(-1);
        }

        function addTextAtPosition(x, y) {
            const layer = {
                text: 'YOUR TEXT',
                x: x,
                y: y,
                font: 'Impact',
                size: 48,
                color: '#ffffff',
                outlineColor: '#000000',
                outlineWidth: 3,
                style: 'normal',
                maxWidth: 300,
                align: 'center'
            };
            textLayers.push(layer);
            selectLayer(textLayers.length - 1);
            updateLayersList();
            redrawCanvas();

            // Immediately start editing
            showInlineEditor();
        }

        function onKeyDown(e) {
            // Don't handle if typing in inline editor or other input
            if (isInlineEditing || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            // Delete selected text with Delete or Backspace
            if ((e.key === 'Delete' || e.key === 'Backspace') && selectedLayerIndex >= 0) {
                e.preventDefault();
                deleteSelectedLayer();
            }
        }

        function deleteSelectedLayer() {
            if (selectedLayerIndex >= 0) {
                textLayers.splice(selectedLayerIndex, 1);
                selectedLayerIndex = -1;
                document.getElementById('text-editor-panel').style.display = 'none';
                updateLayersList();
                redrawCanvas();
                showStatus('Text deleted', 'success');
            }
        }

        function onCanvasMouseMove(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            // Update cursor based on hover
            if (!isDragging && !isResizing) {
                let cursorSet = false;

                // Check if hovering over selected layer's delete button or handles
                if (selectedLayerIndex >= 0) {
                    const layer = textLayers[selectedLayerIndex];
                    const bounds = getBoxBounds(layer);

                    // Check delete button hover
                    const deleteX = bounds.right + 5;
                    const deleteY = bounds.top - 5;
                    const deleteSize = 20;
                    const deleteCenterX = deleteX + deleteSize/2;
                    const deleteCenterY = deleteY - deleteSize/2;
                    const distToDelete = Math.sqrt(Math.pow(x - deleteCenterX, 2) + Math.pow(y - deleteCenterY, 2));

                    if (distToDelete <= deleteSize/2 + 5) {
                        canvas.style.cursor = 'pointer';
                        cursorSet = true;
                    } else {
                        const handle = getResizeHandle(x, y, bounds);
                        if (handle === 'left' || handle === 'right') {
                            canvas.style.cursor = 'ew-resize';
                            cursorSet = true;
                        } else if (handle && handle.includes('top')) {
                            canvas.style.cursor = 'nesw-resize';
                            cursorSet = true;
                        } else if (handle && handle.includes('bottom')) {
                            canvas.style.cursor = 'nwse-resize';
                            cursorSet = true;
                        }
                    }
                }

                // Check if hovering over any text layer (for drag)
                if (!cursorSet) {
                    for (let i = textLayers.length - 1; i >= 0; i--) {
                        const layer = textLayers[i];
                        const bounds = getBoxBounds(layer);
                        if (x >= bounds.left - 10 && x <= bounds.right + 10 &&
                            y >= bounds.top - 10 && y <= bounds.bottom + 10) {
                            canvas.style.cursor = 'move';
                            cursorSet = true;
                            break;
                        }
                    }
                }

                if (!cursorSet) {
                    canvas.style.cursor = 'crosshair';
                }
            }

            // Handle resizing
            if (isResizing && selectedLayerIndex >= 0) {
                const layer = textLayers[selectedLayerIndex];

                if (resizeHandle === 'right' || resizeHandle === 'top-right' || resizeHandle === 'bottom-right') {
                    const newWidth = Math.max(50, (x - layer.x) * 2);
                    layer.maxWidth = Math.round(newWidth);
                } else if (resizeHandle === 'left' || resizeHandle === 'top-left' || resizeHandle === 'bottom-left') {
                    const newWidth = Math.max(50, (layer.x - x) * 2);
                    layer.maxWidth = Math.round(newWidth);
                }

                document.getElementById('text-maxwidth').value = layer.maxWidth;
                redrawCanvas();
                return;
            }

            // Handle dragging
            if (isDragging && selectedLayerIndex >= 0) {
                textLayers[selectedLayerIndex].x = x - dragOffsetX;
                textLayers[selectedLayerIndex].y = y - dragOffsetY;

                document.getElementById('text-x').value = Math.round(textLayers[selectedLayerIndex].x);
                document.getElementById('text-y').value = Math.round(textLayers[selectedLayerIndex].y);

                redrawCanvas();
            }
        }

        function onCanvasMouseUp() {
            isDragging = false;
            isResizing = false;
            resizeHandle = null;
        }

        function onCanvasRightClick(e) {
            e.preventDefault();  // Prevent browser context menu

            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            // Add new text at right-click position
            addTextAtPosition(x, y);
        }

        function onCanvasDoubleClick(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            // Check if double-clicked on existing text - edit it
            for (let i = textLayers.length - 1; i >= 0; i--) {
                const layer = textLayers[i];
                const bounds = getBoxBounds(layer);

                if (x >= bounds.left - 10 && x <= bounds.right + 10 &&
                    y >= bounds.top - 10 && y <= bounds.bottom + 10) {
                    selectLayer(i);
                    showInlineEditor();
                    return;
                }
            }

            // Double-click on empty space - add new text
            addTextAtPosition(x, y);
        }

        // Inline editor functions
        function showInlineEditor() {
            if (selectedLayerIndex < 0) return;

            const layer = textLayers[selectedLayerIndex];
            const bounds = getBoxBounds(layer);

            // Get canvas bounding rect (actual displayed size/position)
            const canvasRect = canvas.getBoundingClientRect();
            const containerRect = document.getElementById('canvas-container').getBoundingClientRect();

            // Scale factors between canvas internal size and displayed size
            const scaleX = canvasRect.width / canvas.width;
            const scaleY = canvasRect.height / canvas.height;

            // Canvas position within container
            const canvasOffsetX = canvasRect.left - containerRect.left;
            const canvasOffsetY = canvasRect.top - containerRect.top;

            // Position exactly over the text bounds
            const editorLeft = canvasOffsetX + bounds.left * scaleX;
            const editorTop = canvasOffsetY + bounds.top * scaleY;
            const editorWidth = bounds.width * scaleX;
            const editorHeight = bounds.height * scaleY;

            // Position wrapper exactly over the text
            inlineEditorWrapper.style.display = 'block';
            inlineEditorWrapper.style.left = editorLeft + 'px';
            inlineEditorWrapper.style.top = editorTop + 'px';
            inlineEditorWrapper.style.width = Math.max(100, editorWidth) + 'px';
            inlineEditorWrapper.style.height = Math.max(50, editorHeight) + 'px';

            // Style textarea to exactly match text appearance
            const fontSize = layer.size * scaleY;
            inlineEditor.style.fontSize = fontSize + 'px';
            inlineEditor.style.fontFamily = layer.font;
            inlineEditor.style.color = layer.color;
            inlineEditor.style.textAlign = layer.align || 'center';
            inlineEditor.style.fontWeight = layer.style === 'bold' ? 'bold' : 'normal';
            inlineEditor.style.fontStyle = layer.style === 'italic' ? 'italic' : 'normal';
            inlineEditor.style.lineHeight = '1.2';

            // Text shadow for outline effect - match the canvas outline
            const ow = layer.outlineWidth * scaleY;
            inlineEditor.style.textShadow = `
                -${ow}px -${ow}px 0 ${layer.outlineColor},
                ${ow}px -${ow}px 0 ${layer.outlineColor},
                -${ow}px ${ow}px 0 ${layer.outlineColor},
                ${ow}px ${ow}px 0 ${layer.outlineColor},
                0 -${ow}px 0 ${layer.outlineColor},
                0 ${ow}px 0 ${layer.outlineColor},
                -${ow}px 0 0 ${layer.outlineColor},
                ${ow}px 0 0 ${layer.outlineColor}
            `;

            inlineEditor.value = layer.text;
            isInlineEditing = true;

            // Redraw canvas without the editing layer
            redrawCanvas();

            // Focus and select all text
            setTimeout(() => {
                inlineEditor.focus();
                inlineEditor.select();
            }, 50);
        }

        function finishInlineEdit() {
            hideInlineEditor();
            redrawCanvas();
        }

        function hideInlineEditor() {
            if (!isInlineEditing) return;

            inlineEditorWrapper.style.display = 'none';
            isInlineEditing = false;

            // Update the layer text
            if (selectedLayerIndex >= 0) {
                textLayers[selectedLayerIndex].text = inlineEditor.value;
                document.getElementById('text-content').value = inlineEditor.value;
                updateLayersList();
                redrawCanvas();
            }
        }

        function onInlineEditorInput() {
            if (selectedLayerIndex >= 0) {
                textLayers[selectedLayerIndex].text = inlineEditor.value;
                document.getElementById('text-content').value = inlineEditor.value;
                updateLayersList();
                // Don't redraw - the textarea IS the text while editing
            }
        }

        function onInlineEditorKeydown(e) {
            if (e.key === 'Escape') {
                hideInlineEditor();
                redrawCanvas();
            } else if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                hideInlineEditor();
                redrawCanvas();
            }
        }

        // AI concept generation
        async function generateAIConcept() {
            showStatus('Generating AI concept...', 'loading');
            try {
                const response = await fetch('/generate-concept', {method: 'POST'});
                const data = await response.json();

                // Clear existing text and add new
                textLayers = [];
                if (data.concept.top_text) {
                    addTextLayer(data.concept.top_text);
                    textLayers[textLayers.length-1].y = 60;
                }
                if (data.concept.bottom_text) {
                    addTextLayer(data.concept.bottom_text);
                    textLayers[textLayers.length-1].y = canvas.height - 60;
                }
                if (!data.concept.top_text && !data.concept.bottom_text && data.concept.caption) {
                    addTextLayer(data.concept.caption);
                }

                updateLayersList();
                redrawCanvas();
                showStatus('AI concept loaded! Edit the text as needed.', 'success');
            } catch (e) {
                showStatus('Error: ' + e.message, 'error');
            }
        }

        // Discord data
        function loadDiscordUsers() {
            const users = {{ discord_data.active_users | tojson }};
            const container = document.getElementById('discord-users');
            container.innerHTML = users.slice(0, 10).map(user =>
                `<span class="discord-tag" onclick="insertDiscordUser('${user}')">${user}</span>`
            ).join('');
        }

        function insertDiscordUser(user) {
            if (selectedLayerIndex >= 0) {
                const textarea = document.getElementById('text-content');
                textarea.value += ' @' + user;
                updateSelectedText();
            } else {
                addTextLayer('@' + user);
            }
        }

        function copyText(text) {
            navigator.clipboard.writeText(text);
            showStatus('Copied: ' + text.substring(0, 30), 'success');
        }

        // Save/export functions
        async function saveMeme() {
            showStatus('Saving...', 'loading');
            const dataUrl = canvas.toDataURL('image/png');
            const base64 = dataUrl.split(',')[1];

            try {
                const response = await fetch('/save-canvas', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({image: base64})
                });
                const data = await response.json();
                showStatus('Saved to: ' + data.path, 'success');
            } catch (e) {
                showStatus('Error saving', 'error');
            }
        }

        function downloadMeme() {
            const link = document.createElement('a');
            link.download = 'hairdao_meme.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }

        async function copyMeme() {
            try {
                canvas.toBlob(async (blob) => {
                    await navigator.clipboard.write([new ClipboardItem({'image/png': blob})]);
                    showStatus('Copied to clipboard!', 'success');
                });
            } catch (e) {
                showStatus('Copy failed', 'error');
            }
        }

        async function addToPending() {
            const dataUrl = canvas.toDataURL('image/png');
            const base64 = dataUrl.split(',')[1];

            try {
                await fetch('/add-pending', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({image: base64, layers: textLayers})
                });
                showStatus('Added to review queue!', 'success');
            } catch (e) {
                showStatus('Error', 'error');
            }
        }

        // Gallery functions
        async function generateBatch() {
            const count = parseInt(document.getElementById('batch-count').value);
            document.getElementById('batch-progress').style.display = 'block';

            for (let i = 0; i < count; i++) {
                document.getElementById('progress-text').textContent = `${i+1}/${count}`;
                document.getElementById('progress-fill').style.width = `${(i+1)/count*100}%`;

                try {
                    await fetch('/generate-pending', {method: 'POST'});
                } catch (e) {}
            }

            document.getElementById('batch-progress').style.display = 'none';
            loadPending();
        }

        async function loadPending() {
            const response = await fetch('/pending');
            const data = await response.json();
            pendingMemes = data.memes;

            const grid = document.getElementById('gallery-grid');
            if (pendingMemes.length === 0) {
                grid.innerHTML = '<p style="color:#888;">No memes to review. Click "Generate Batch" to create some.</p>';
                return;
            }

            grid.innerHTML = pendingMemes.map((meme, i) => `
                <div class="gallery-item">
                    <img src="data:image/png;base64,${meme.image}" onclick="editFromGallery(${i})">
                    <div class="gallery-item-actions">
                        <button onclick="approveMeme(${i})">Approve</button>
                        <button class="secondary" onclick="editFromGallery(${i})">Edit</button>
                        <button class="danger" onclick="rejectMeme(${i})">Reject</button>
                    </div>
                </div>
            `).join('');
        }

        async function approveMeme(index) {
            await fetch('/approve-pending', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: pendingMemes[index].id})
            });
            loadPending();
        }

        async function rejectMeme(index) {
            await fetch('/reject-pending', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: pendingMemes[index].id})
            });
            loadPending();
        }

        function editFromGallery(index) {
            const meme = pendingMemes[index];
            showTab('editor');

            // Load image
            baseImage = new Image();
            baseImage.onload = function() {
                canvas.width = baseImage.width;
                canvas.height = baseImage.height;

                // Load text layers if available
                if (meme.layers) {
                    textLayers = meme.layers;
                } else {
                    textLayers = [];
                }
                updateLayersList();
                redrawCanvas();
            };
            baseImage.src = 'data:image/png;base64,' + meme.image;
        }

        async function clearPending() {
            if (!confirm('Clear all pending memes?')) return;
            await fetch('/clear-pending', {method: 'POST'});
            loadPending();
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    discord_data = load_discord_content()
    return render_template_string(
        HTML_TEMPLATE,
        templates=list(MEME_TEMPLATES.keys()),
        discord_data=discord_data
    )


@app.route('/get-template', methods=['POST'])
def get_template():
    """Get a template image as base64."""
    try:
        data = request.json
        template_name = data.get('template', 'drake')

        img = download_template(template_name)
        img = img.convert('RGB')

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({'image': img_base64})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-concept', methods=['POST'])
def generate_concept():
    """Generate an AI meme concept."""
    try:
        website_data = load_website_content()
        discord_data = load_discord_content()
        concept = generate_meme_concept(website_data, discord_data, 'classic_top_bottom')
        return jsonify({'concept': concept})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/save-canvas', methods=['POST'])
def save_canvas():
    """Save canvas image to output."""
    try:
        data = request.json
        img_data = base64.b64decode(data['image'])

        img = Image.open(BytesIO(img_data))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"meme_{timestamp}.png"
        img.save(output_path, 'PNG')

        return jsonify({'path': str(output_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/add-pending', methods=['POST'])
def add_pending():
    """Add current canvas to pending queue."""
    try:
        data = request.json
        meme_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        pending_file = PENDING_DIR / f"{meme_id}.json"
        with open(pending_file, 'w') as f:
            json.dump({
                'id': meme_id,
                'image': data['image'],
                'layers': data.get('layers', [])
            }, f)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-pending', methods=['POST'])
def generate_pending():
    """Generate a meme and add to pending."""
    try:
        website_data = load_website_content()
        discord_data = load_discord_content()
        concept = generate_meme_concept(website_data, discord_data)

        img = create_meme_from_concept(concept)

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        meme_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        pending_file = PENDING_DIR / f"{meme_id}.json"

        with open(pending_file, 'w') as f:
            json.dump({
                'id': meme_id,
                'concept': concept,
                'image': img_base64
            }, f)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pending')
def get_pending():
    """Get all pending memes."""
    memes = []
    for file in sorted(PENDING_DIR.glob('*.json'), reverse=True):
        with open(file, 'r') as f:
            memes.append(json.load(f))
    return jsonify({'memes': memes})


@app.route('/approve-pending', methods=['POST'])
def approve_pending():
    """Approve a pending meme."""
    data = request.json
    pending_file = PENDING_DIR / f"{data['id']}.json"

    if pending_file.exists():
        with open(pending_file, 'r') as f:
            meme_data = json.load(f)

        img_data = base64.b64decode(meme_data['image'])
        img = Image.open(BytesIO(img_data))
        output_path = OUTPUT_DIR / f"approved_{data['id']}.png"
        img.save(output_path, 'PNG')

        pending_file.unlink()
        return jsonify({'success': True})

    return jsonify({'error': 'Not found'}), 404


@app.route('/reject-pending', methods=['POST'])
def reject_pending():
    """Reject a pending meme."""
    data = request.json
    pending_file = PENDING_DIR / f"{data['id']}.json"
    if pending_file.exists():
        pending_file.unlink()
    return jsonify({'success': True})


@app.route('/clear-pending', methods=['POST'])
def clear_pending():
    """Clear all pending."""
    for f in PENDING_DIR.glob('*.json'):
        f.unlink()
    return jsonify({'success': True})


if __name__ == '__main__':
    print("=" * 50)
    print("HairDAO Meme Editor")
    print("=" * 50)
    print("\nOpen http://localhost:5000 in your browser\n")
    app.run(debug=True, port=5000)
