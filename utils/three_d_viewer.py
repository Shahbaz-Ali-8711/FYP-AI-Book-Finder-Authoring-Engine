import streamlit as st
import streamlit.components.v1 as components


def render_3d_book_viewer(height=520):
    """
    Renders an interactive, fully rotatable 3D book viewer powered by Three.js.
    Designed for the Warm Ivory (#FAFAF5), Emerald Green (#046A38), and Vermilion (#E34234) palette.
    Supports 360-degree mouse/touch drag, inertia physics, auto-spin,
    luxury book textures, and frosted clean-glass overlays with Pause & Reset controls.
    """
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>3D 360 Book Viewer - Warm Ivory & Emerald Studio</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                user-select: none;
                -webkit-user-select: none;
            }
            body, html {
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: #FAFAF5;
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            #canvas-container {
                width: 100%;
                height: 100%;
                position: relative;
                cursor: grab;
                background: radial-gradient(circle at 50% 40%, rgba(4, 106, 56, 0.06) 0%, rgba(245, 245, 237, 0.7) 50%, #FAFAF5 85%);
                border: 1.5px solid #E5E5DC;
                border-radius: 24px;
                box-shadow: 0 15px 35px -10px rgba(26, 26, 26, 0.06);
            }
            #canvas-container:active {
                cursor: grabbing;
            }
            canvas {
                display: block;
                width: 100%;
                height: 100%;
                border-radius: 24px;
            }

            /* Floating Warm Ivory UI Badges */
            .overlay-badge-top {
                position: absolute;
                top: 14px;
                left: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 14px;
                background: rgba(255, 255, 255, 0.94);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1.5px solid #E5E5DC;
                border-radius: 9999px;
                color: #046A38;
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                box-shadow: 0 4px 14px rgba(4, 106, 56, 0.08);
                pointer-events: none;
                z-index: 10;
            }
            .pulse-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #E34234;
                box-shadow: 0 0 10px #E34234;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.4; transform: scale(0.8); }
            }

            .overlay-controls {
                position: absolute;
                top: 14px;
                right: 16px;
                display: flex;
                gap: 8px;
                z-index: 10;
            }
            .control-btn {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
                border: 1.5px solid #D4D4CA;
                color: #1A1A1A;
                border-radius: 10px;
                padding: 6px 14px;
                font-size: 0.76rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 5px;
                box-shadow: 0 2px 8px rgba(26, 26, 26, 0.04);
            }
            .control-btn:hover {
                background: #F0F8F4;
                border-color: #046A38;
                color: #046A38;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(4, 106, 56, 0.15);
            }

            .overlay-badge-bottom {
                position: absolute;
                bottom: 16px;
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 20px;
                background: rgba(255, 255, 255, 0.96);
                backdrop-filter: blur(18px);
                -webkit-backdrop-filter: blur(18px);
                border: 1.5px solid #D4D4CA;
                border-radius: 9999px;
                color: #1A1A1A;
                font-size: 0.82rem;
                font-weight: 700;
                letter-spacing: 0.02em;
                box-shadow: 0 8px 25px -4px rgba(26, 26, 26, 0.08);
                pointer-events: none;
                z-index: 10;
                white-space: nowrap;
                animation: floatPrompt 3s ease-in-out infinite;
            }
            @keyframes floatPrompt {
                0%, 100% { transform: translateX(-50%) translateY(0); }
                50% { transform: translateX(-50%) translateY(-4px); }
            }
            .drag-icon {
                font-size: 1.05rem;
            }
            .highlight-text {
                color: #E34234;
                font-weight: 800;
            }
        </style>
        <!-- Load Three.js r128 -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div class="overlay-badge-top">
                <span class="pulse-dot"></span>
                <span>360° Drag View · Live 3D Model</span>
            </div>

            <div class="overlay-controls">
                <button class="control-btn" id="btn-toggle-spin">⏸ Pause</button>
                <button class="control-btn" id="btn-reset">↺ Reset</button>
            </div>

            <div class="overlay-badge-bottom">
                <span class="drag-icon">🖱️</span>
                <span>Click & Drag to Rotate · <span class="highlight-text">360° Interactive Spatial Canvas</span></span>
            </div>
        </div>

        <script>
            // --- 1. PROCEDURAL TEXTURE GENERATION ---
            function createFrontCoverTexture() {
                const canvas = document.createElement('canvas');
                canvas.width = 1024;
                canvas.height = 1440;
                const ctx = canvas.getContext('2d');

                // Rich Emerald Green gradient background
                const bgGrad = ctx.createLinearGradient(0, 0, 1024, 1440);
                bgGrad.addColorStop(0, '#046A38');
                bgGrad.addColorStop(0.4, '#0F5257');
                bgGrad.addColorStop(0.85, '#03522B');
                bgGrad.addColorStop(1, '#02381E');
                ctx.fillStyle = bgGrad;
                ctx.fillRect(0, 0, 1024, 1440);

                // Geometric background grid lines in warm ivory foil
                ctx.strokeStyle = 'rgba(250, 250, 245, 0.12)';
                ctx.lineWidth = 1.5;
                for (let x = 60; x < 1024; x += 90) {
                    ctx.beginPath();
                    ctx.moveTo(x, 0);
                    ctx.lineTo(x, 1440);
                    ctx.stroke();
                }
                for (let y = 60; y < 1440; y += 90) {
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(1024, y);
                    ctx.stroke();
                }

                // Geometric concentric rings
                const centerX = 512, centerY = 660;
                ctx.strokeStyle = 'rgba(250, 250, 245, 0.35)';
                ctx.lineWidth = 2.5;
                ctx.beginPath();
                ctx.arc(centerX, centerY, 240, 0, Math.PI * 2);
                ctx.stroke();

                ctx.strokeStyle = 'rgba(227, 66, 52, 0.65)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(centerX, centerY, 170, 0, Math.PI * 2);
                ctx.stroke();

                // Connecting glowing nodes in Vermilion
                const nodes = [
                    {x: 360, y: 560}, {x: 660, y: 560},
                    {x: 512, y: 460}, {x: 512, y: 840},
                    {x: 380, y: 760}, {x: 640, y: 760}
                ];
                ctx.fillStyle = '#E34234';
                nodes.forEach(n => {
                    ctx.beginPath();
                    ctx.arc(n.x, n.y, 8, 0, Math.PI * 2);
                    ctx.fill();
                    // Connect to center
                    ctx.strokeStyle = 'rgba(250, 250, 245, 0.3)';
                    ctx.beginPath();
                    ctx.moveTo(centerX, centerY);
                    ctx.lineTo(n.x, n.y);
                    ctx.stroke();
                });

                // Top Series Pill
                ctx.fillStyle = 'rgba(250, 250, 245, 0.16)';
                ctx.strokeStyle = 'rgba(250, 250, 245, 0.5)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.roundRect(312, 140, 400, 60, 30);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = '#FAFAF5';
                ctx.font = 'bold 24px "Plus Jakarta Sans", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('PEN2PUBLISH AI · EDITION 2026', 512, 178);

                // Book Title
                ctx.fillStyle = '#FAFAF5';
                ctx.font = '900 76px "Plus Jakarta Sans", sans-serif';
                ctx.fillText('THE AUTONOMOUS', 512, 310);
                ctx.fillText('AUTHOR', 512, 390);

                // Subtitle
                ctx.fillStyle = '#E34234';
                ctx.font = 'bold 30px "Plus Jakarta Sans", sans-serif';
                ctx.fillText('Autonomous Manuscript Synthesis & Discovery', 512, 980);

                // Author Byline
                ctx.fillStyle = '#FAFAF5';
                ctx.font = '600 28px "Plus Jakarta Sans", sans-serif';
                ctx.fillText('SHAHBAZ ALI · HUZAIFA TANVEER · ARSALAN ABBASI', 512, 1260);

                ctx.strokeStyle = '#E34234';
                ctx.lineWidth = 4;
                ctx.beginPath();
                ctx.moveTo(350, 1290);
                ctx.lineTo(674, 1290);
                ctx.stroke();

                return new THREE.CanvasTexture(canvas);
            }

            function createSpineTexture() {
                const canvas = document.createElement('canvas');
                canvas.width = 256;
                canvas.height = 1440;
                const ctx = canvas.getContext('2d');

                // Deep emerald spine gradient
                const grad = ctx.createLinearGradient(0, 0, 256, 0);
                grad.addColorStop(0, '#02381E');
                grad.addColorStop(0.5, '#046A38');
                grad.addColorStop(1, '#02381E');
                ctx.fillStyle = grad;
                ctx.fillRect(0, 0, 256, 1440);

                // Foil accents
                ctx.strokeStyle = 'rgba(227, 66, 52, 0.5)';
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(30, 80);
                ctx.lineTo(226, 80);
                ctx.moveTo(30, 1360);
                ctx.lineTo(226, 1360);
                ctx.stroke();

                // Spine text (Vertical)
                ctx.save();
                ctx.translate(128, 720);
                ctx.rotate(Math.PI / 2);
                ctx.textAlign = 'center';
                ctx.fillStyle = '#FAFAF5';
                ctx.font = 'bold 44px "Plus Jakarta Sans", sans-serif';
                ctx.fillText('PEN2PUBLISH AI  ·  THE AUTONOMOUS AUTHOR', 0, 15);
                ctx.restore();

                return new THREE.CanvasTexture(canvas);
            }

            function createBackCoverTexture() {
                const canvas = document.createElement('canvas');
                canvas.width = 1024;
                canvas.height = 1440;
                const ctx = canvas.getContext('2d');

                const bgGrad = ctx.createLinearGradient(0, 0, 1024, 1440);
                bgGrad.addColorStop(0, '#03522B');
                bgGrad.addColorStop(1, '#02381E');
                ctx.fillStyle = bgGrad;
                ctx.fillRect(0, 0, 1024, 1440);

                ctx.fillStyle = '#FAFAF5';
                ctx.font = 'bold 46px "Plus Jakarta Sans", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('ABOUT THIS PLATFORM', 512, 180);

                ctx.font = '24px "Plus Jakarta Sans", sans-serif';
                ctx.fillStyle = '#E5E5DC';
                const blurb = [
                    'Pen2Publish AI is the world’s foremost end-to-end',
                    'autonomous authoring, formatting, and reader suite.',
                    'Engineered by Shahbaz Ali, Huzaifa Tanveer, and',
                    'Arsalan Rasheed Abbasi, the platform bridges cognitive',
                    'narrative expansion with publication-ready compilation.'
                ];
                blurb.forEach((line, i) => {
                    ctx.fillText(line, 512, 280 + (i * 44));
                });

                // Barcode box in warm ivory
                ctx.fillStyle = '#FFFFFF';
                ctx.fillRect(362, 1140, 300, 140);
                ctx.fillStyle = '#1A1A1A';
                for (let i = 0; i < 46; i++) {
                    const bx = 382 + (i * 5.6);
                    const bw = (i % 3 === 0) ? 3.5 : 1.8;
                    ctx.fillRect(bx, 1160, bw, 75);
                }
                ctx.font = '16px monospace';
                ctx.fillText('978-0-262-14098-0', 512, 1260);

                return new THREE.CanvasTexture(canvas);
            }

            function createPagesTexture() {
                const canvas = document.createElement('canvas');
                canvas.width = 512;
                canvas.height = 512;
                const ctx = canvas.getContext('2d');

                // Warm Ivory paper edge texture
                ctx.fillStyle = '#F5F5ED';
                ctx.fillRect(0, 0, 512, 512);

                ctx.strokeStyle = 'rgba(212, 212, 202, 0.45)';
                ctx.lineWidth = 1;
                for (let y = 0; y < 512; y += 4) {
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(512, y);
                    ctx.stroke();
                }
                return new THREE.CanvasTexture(canvas);
            }

            // --- 2. THREE.JS INITIALIZATION ---
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xFAFAF5);

            const camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 0.3, 7.8);

            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            container.appendChild(renderer.domElement);

            // Lighting for Warm Ivory studio aesthetic
            const ambientLight = new THREE.AmbientLight(0xFFFFFF, 0.85);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xFFFFFF, 0.7);
            dirLight.position.set(5, 10, 7);
            dirLight.castShadow = true;
            scene.add(dirLight);

            const rimLight = new THREE.DirectionalLight(0x046A38, 0.35);
            rimLight.position.set(-8, -4, -5);
            scene.add(rimLight);

            const warmLight = new THREE.PointLight(0xE34234, 0.4, 15);
            warmLight.position.set(2, -2, 4);
            scene.add(warmLight);

            // Floor soft shadow plane
            const shadowPlaneGeo = new THREE.PlaneGeometry(12, 12);
            const shadowPlaneMat = new THREE.ShadowMaterial({ opacity: 0.12 });
            const shadowPlane = new THREE.Mesh(shadowPlaneGeo, shadowPlaneMat);
            shadowPlane.rotation.x = -Math.PI / 2;
            shadowPlane.position.y = -2.4;
            shadowPlane.receiveShadow = true;
            scene.add(shadowPlane);

            // --- 3. BOOK MESH CREATION ---
            // Width: 2.8, Height: 4.0, Depth: 0.55
            const bookGeo = new THREE.BoxGeometry(2.8, 4.0, 0.55);

            const frontTex = createFrontCoverTexture();
            const backTex = createBackCoverTexture();
            const spineTex = createSpineTexture();
            const pagesTex = createPagesTexture();

            const materials = [
                new THREE.MeshStandardMaterial({ map: pagesTex, roughness: 0.85 }),      // Right (Pages edge)
                new THREE.MeshStandardMaterial({ map: spineTex, roughness: 0.4 }),      // Left (Spine)
                new THREE.MeshStandardMaterial({ map: pagesTex, roughness: 0.85 }),      // Top
                new THREE.MeshStandardMaterial({ map: pagesTex, roughness: 0.85 }),      // Bottom
                new THREE.MeshStandardMaterial({ map: frontTex, roughness: 0.35, metalness: 0.1 }), // Front Cover
                new THREE.MeshStandardMaterial({ map: backTex, roughness: 0.4 })        // Back Cover
            ];

            const book = new THREE.Mesh(bookGeo, materials);
            book.castShadow = true;
            book.receiveShadow = true;
            scene.add(book);

            // Gentle initial isometric angle
            book.rotation.x = 0.15;
            book.rotation.y = -0.55;

            // --- 4. INTERACTIVE DRAG & ORBIT PHYSICS ---
            let isDragging = false;
            let previousMousePosition = { x: 0, y: 0 };
            let autoSpin = true;
            let angularVelocity = { x: 0, y: 0.005 };

            function onPointerDown(e) {
                isDragging = true;
                const clientX = e.clientX || (e.touches && e.touches[0].clientX);
                const clientY = e.clientY || (e.touches && e.touches[0].clientY);
                previousMousePosition = { x: clientX, y: clientY };
            }

            function onPointerMove(e) {
                if (!isDragging) return;
                const clientX = e.clientX || (e.touches && e.touches[0].clientX);
                const clientY = e.clientY || (e.touches && e.touches[0].clientY);

                const deltaX = clientX - previousMousePosition.x;
                const deltaY = clientY - previousMousePosition.y;

                book.rotation.y += deltaX * 0.009;
                book.rotation.x += deltaY * 0.009;

                // Clamp vertical tilt
                book.rotation.x = Math.max(-0.9, Math.min(0.9, book.rotation.x));

                angularVelocity = { x: deltaY * 0.0008, y: deltaX * 0.0008 };
                previousMousePosition = { x: clientX, y: clientY };
            }

            function onPointerUp() {
                isDragging = false;
            }

            container.addEventListener('mousedown', onPointerDown);
            window.addEventListener('mousemove', onPointerMove);
            window.addEventListener('mouseup', onPointerUp);

            container.addEventListener('touchstart', onPointerDown, { passive: true });
            window.addEventListener('touchmove', onPointerMove, { passive: true });
            window.addEventListener('touchend', onPointerUp);

            // Controls
            const btnSpin = document.getElementById('btn-toggle-spin');
            btnSpin.addEventListener('click', (e) => {
                e.stopPropagation();
                autoSpin = !autoSpin;
                btnSpin.innerText = autoSpin ? '⏸ Pause' : '▶ Spin';
            });

            const btnReset = document.getElementById('btn-reset');
            btnReset.addEventListener('click', (e) => {
                e.stopPropagation();
                book.rotation.x = 0.15;
                book.rotation.y = -0.55;
                angularVelocity = { x: 0, y: 0.005 };
                autoSpin = true;
                btnSpin.innerText = '⏸ Pause';
            });

            // Resize Observer
            window.addEventListener('resize', () => {
                const width = container.clientWidth;
                const height = container.clientHeight;
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            });

            // --- 5. ANIMATION LOOP ---
            let clock = new THREE.Clock();
            function animate() {
                requestAnimationFrame(animate);

                const delta = clock.getDelta();

                if (!isDragging) {
                    if (autoSpin) {
                        book.rotation.y += 0.008;
                    } else {
                        // Dampen inertia
                        book.rotation.y += angularVelocity.y;
                        book.rotation.x += angularVelocity.x;
                        angularVelocity.x *= 0.94;
                        angularVelocity.y *= 0.94;
                    }
                    // Gentle floating hover
                    book.position.y = Math.sin(clock.getElapsedTime() * 1.5) * 0.08;
                }

                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height)
