/* =============================================================================
 * 1mjobs "Job Journey" animated hero  (Three.js, flat 2D vector style)
 *
 * A wordless, seamlessly-looping motivational story:
 *     Apply  ->  Accepted  ->  Paid  ->  Can now afford things
 *
 * Vanilla drop-in module. Requires global `THREE` (loaded before this file).
 * Mount:   JobJourney.mount(containerEl)   ->  returns an instance
 * Unmount: instance.unmount()  (or JobJourney.unmount())
 *
 * Everything is procedural geometry: no model files, no external textures.
 * The animation is fully DETERMINISTIC (a pure function of the loop clock),
 * which is what makes the loop perfectly seamless.
 * ============================================================================= */
(function (global) {
    "use strict";

    // ======================= TUNABLE CONSTANTS ===============================
    var COLORS = {
        primary:     "#4F46E5",   // brand blue
        primaryDark: "#4338CA",   // brand blue, depth
        white:       "#FFFFFF",
        navy:        "#0B1020",   // panel background
        yellow:      "#FBBF24",   // accent
        coral:       "#F97066",   // accent
        green:       "#34D399",   // success
        // supporting shades (derived, not brand-critical)
        skin:        "#F6C8A8",
        hair:        "#2B2140",
        deskTop:     "#3730A3",
        wallet:      "#4338CA",
        note:        "#34D399",
        coin:        "#FBBF24",
        shadow:      "#000000"
    };

    var SCENE_DURATION = 5.0;     // seconds each scene holds the stage
    var CROSSFADE      = 0.75;    // seconds of slide+fade between scenes
    var BALANCE_TARGET = 250000;  // the wallet balance the counter ticks up to
    var CURRENCY       = "₦";// Naira sign

    var NUM_SCENES = 4;
    var TOTAL      = SCENE_DURATION * NUM_SCENES;
    var REF        = 50;          // camera half-extent of the shorter axis
    var SLIDE      = REF * 1.9;   // how far scenes slide when transitioning

    // ======================= SMALL MATH HELPERS ==============================
    function clamp01(t) { return t < 0 ? 0 : (t > 1 ? 1 : t); }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
    function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
    function easeOutBack(t) { var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); }
    function commas(n) { return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

    // ======================= GEOMETRY HELPERS ================================
    function roundedRectShape(w, h, r) {
        var s = new THREE.Shape();
        var x = -w / 2, y = -h / 2;
        r = Math.min(r, w / 2, h / 2);
        s.moveTo(x + r, y);
        s.lineTo(x + w - r, y);
        s.quadraticCurveTo(x + w, y, x + w, y + r);
        s.lineTo(x + w, y + h - r);
        s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        s.lineTo(x + r, y + h);
        s.quadraticCurveTo(x, y + h, x, y + h - r);
        s.lineTo(x, y + r);
        s.quadraticCurveTo(x, y, x + r, y);
        return s;
    }

    // A flat mesh with a MeshBasicMaterial (no lighting -> illustration look)
    function flat(geometry, color, opacity) {
        var mat = new THREE.MeshBasicMaterial({
            color: new THREE.Color(color),
            transparent: true,
            opacity: opacity == null ? 1 : opacity,
            depthWrite: false
        });
        var m = new THREE.Mesh(geometry, mat);
        m.userData.baseOpacity = opacity == null ? 1 : opacity;
        return m;
    }
    function rrect(w, h, r, color, opacity) { return flat(new THREE.ShapeGeometry(roundedRectShape(w, h, r)), color, opacity); }
    function circle(r, color, opacity) { return flat(new THREE.CircleGeometry(r, 40), color, opacity); }
    function ellipse(rx, ry, color, opacity) {
        var m = circle(1, color, opacity); m.scale.set(rx, ry, 1); return m;
    }
    function triangle(w, h, color) {
        var s = new THREE.Shape();
        s.moveTo(-w / 2, -h / 2); s.lineTo(w / 2, -h / 2); s.lineTo(0, h / 2); s.closePath();
        return flat(new THREE.ShapeGeometry(s), color);
    }

    // Soft faked ground shadow
    function shadow(rx) {
        var e = ellipse(rx, rx * 0.28, COLORS.shadow, 0.18);
        return e;
    }

    // ------- Text / chip / card labels drawn on a canvas ---------------------
    function makeLabel(text, o) {
        o = o || {};
        var fontPx = 72;
        var weight = o.weight || "bold";
        var family = "Arial, Helvetica, sans-serif";
        var meas = document.createElement("canvas").getContext("2d");
        meas.font = weight + " " + fontPx + "px " + family;
        var checkW = o.check ? fontPx * 1.2 : 0;
        var textW = Math.ceil(meas.measureText(text).width) + checkW;
        var chip = !!o.bg;
        var padX = o.padX != null ? o.padX : (chip ? 46 : 6);
        var padY = o.padY != null ? o.padY : (chip ? 30 : 6);
        var cw = textW + padX * 2, ch = fontPx + padY * 2;
        var cv = document.createElement("canvas"); cv.width = cw; cv.height = ch;
        var ctx = cv.getContext("2d");

        var worldH = o.worldHeight || 8;
        var worldW = worldH * cw / ch;
        var tex = new THREE.CanvasTexture(cv);
        var mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false });
        var mesh = new THREE.Mesh(new THREE.PlaneGeometry(worldW, worldH), mat);
        mesh.userData.baseOpacity = 1;

        function draw(str) {
            ctx.clearRect(0, 0, cw, ch);
            if (chip) {
                ctx.fillStyle = o.bg;
                var r = o.radius != null ? o.radius : ch / 2;
                roundRectPath(ctx, 2, 2, cw - 4, ch - 4, r);
                ctx.fill();
            }
            var tx = padX;
            ctx.textBaseline = "middle";
            if (o.check) {
                var cy = ch / 2, cr = fontPx * 0.42, ccx = padX + cr;
                ctx.fillStyle = o.checkBg || COLORS.green;
                ctx.beginPath(); ctx.arc(ccx, cy, cr, 0, Math.PI * 2); ctx.fill();
                ctx.strokeStyle = COLORS.white; ctx.lineWidth = fontPx * 0.12;
                ctx.lineCap = "round"; ctx.beginPath();
                ctx.moveTo(ccx - cr * 0.45, cy + cr * 0.02);
                ctx.lineTo(ccx - cr * 0.08, cy + cr * 0.42);
                ctx.lineTo(ccx + cr * 0.52, cy - cr * 0.42);
                ctx.stroke();
                tx = ccx + cr + fontPx * 0.22;
            }
            ctx.font = weight + " " + fontPx + "px " + family;
            ctx.fillStyle = o.color || COLORS.white;
            ctx.textAlign = "left";
            ctx.fillText(str, tx, ch / 2 + 2);
            tex.needsUpdate = true;
        }
        draw(text);
        mesh.userData.setText = draw;   // for dynamic labels (balance counter)
        return mesh;
    }
    function roundRectPath(ctx, x, y, w, h, r) {
        r = Math.min(r, w / 2, h / 2);
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }

    // ------- A simple flat character ----------------------------------------
    // Returns a group with `.armL` / `.armR` pivots and a `.setArms(angleL,angleR)`.
    function makeCharacter(shirt) {
        var g = new THREE.Group();
        g.add(withPos(shadow(13), 0, -20, -1));

        // legs
        g.add(withPos(rrect(6, 12, 3, COLORS.primaryDark), -4, -14, 0));
        g.add(withPos(rrect(6, 12, 3, COLORS.primaryDark), 4, -14, 0));
        // body
        g.add(withPos(rrect(18, 20, 7, shirt || COLORS.primary), 0, -2, 1));
        // arm pivots (rotate about shoulder)
        var armL = new THREE.Group(); armL.position.set(-8.5, 4, 2);
        armL.add(withPos(rrect(4.5, 15, 2.2, shirt || COLORS.primary), 0, -6, 0));
        var armR = new THREE.Group(); armR.position.set(8.5, 4, 2);
        armR.add(withPos(rrect(4.5, 15, 2.2, shirt || COLORS.primary), 0, -6, 0));
        g.add(armL); g.add(armR);
        // head
        g.add(withPos(circle(8, COLORS.skin), 0, 14, 3));
        // hair
        var hair = circle(8, COLORS.hair); hair.scale.set(1, 0.55, 1);
        g.add(withPos(hair, 0, 18.5, 3.1));
        // eyes
        g.add(withPos(circle(0.9, COLORS.hair), -2.6, 13.5, 4));
        g.add(withPos(circle(0.9, COLORS.hair), 2.6, 13.5, 4));

        g.armL = armL; g.armR = armR;
        g.setArms = function (aL, aR) { armL.rotation.z = aL; armR.rotation.z = aR; };
        g.setArms(0.15, -0.15);
        return g;
    }

    function withPos(obj, x, y, z) { obj.position.set(x, y, z || 0); return obj; }

    // ------- Flat vector icons for scene 4 ----------------------------------
    function iconHouse() {
        var g = new THREE.Group();
        g.add(withPos(rrect(14, 11, 1.5, COLORS.white), 0, -2, 0));
        g.add(withPos(triangle(18, 8, COLORS.coral), 0, 6.5, 1));
        g.add(withPos(rrect(4, 6, 1, COLORS.primary), 0, -4, 2));
        return g;
    }
    function iconCar() {
        var g = new THREE.Group();
        g.add(withPos(rrect(20, 7, 3, COLORS.primary), 0, 0, 0));
        g.add(withPos(rrect(11, 6, 3, COLORS.primaryDark), -1, 4.5, 1));
        g.add(withPos(circle(3.2, COLORS.navy), -6, -4, 2));
        g.add(withPos(circle(3.2, COLORS.navy), 6, -4, 2));
        g.add(withPos(circle(1.3, COLORS.white), -6, -4, 3));
        g.add(withPos(circle(1.3, COLORS.white), 6, -4, 3));
        return g;
    }
    function iconCart() {
        var g = new THREE.Group();
        g.add(withPos(rrect(15, 9, 2, COLORS.yellow), 1, 1, 0));
        // handle
        g.add(withPos(rrect(3, 2, 1, COLORS.white), -8.5, 6, 1));
        g.add(withPos(rrect(2, 10, 1, COLORS.white), -8.5, 1.5, 1));
        g.add(withPos(circle(2, COLORS.navy), -3, -6, 1));
        g.add(withPos(circle(2, COLORS.navy), 6, -6, 1));
        return g;
    }
    function iconCap() {
        var g = new THREE.Group();
        var d = rrect(13, 13, 1.5, COLORS.navy); d.rotation.z = Math.PI / 4; d.scale.set(1, 1, 1);
        g.add(withPos(d, 0, 3, 1));
        g.add(withPos(rrect(9, 5, 1, COLORS.primaryDark), 0, -1.5, 0));
        g.add(withPos(rrect(1, 6, 0.5, COLORS.yellow), 7, 1, 2));
        g.add(withPos(circle(1.3, COLORS.yellow), 7, -2.2, 2));
        return g;
    }

    // ======================= SCENE BUILDERS =================================
    // Each returns { group, update(localT) }. localT runs 0..SCENE_DURATION.

    // ---- Scene 1: APPLY ----------------------------------------------------
    function buildApply() {
        var group = new THREE.Group();
        var char = makeCharacter();
        char.position.set(-16, 2, 0); char.scale.setScalar(0.85);
        group.add(char);

        // desk + laptop
        group.add(withPos(rrect(40, 4, 1.5, COLORS.deskTop), -6, -22, 2));
        var laptopBase = rrect(20, 3, 1, COLORS.primaryDark); laptopBase.position.set(-2, -18, 3);
        var screen = rrect(18, 12, 1.5, COLORS.white); screen.position.set(-2, -10, 3);
        group.add(laptopBase); group.add(screen);
        var applyCard = makeLabel("Apply", { bg: COLORS.primary, color: COLORS.white, worldHeight: 4.2, radius: 8 });
        applyCard.position.set(-2, -10, 4);
        group.add(applyCard);

        // paper plane (a triangle) that launches off
        var plane = triangle(7, 5, COLORS.white); plane.rotation.z = -0.5;
        plane.position.set(-2, -8, 6);
        group.add(plane);

        // "Applied" chip that pops
        var chip = makeLabel("Applied", { bg: COLORS.green, color: COLORS.white, check: true, worldHeight: 6, radius: 12 });
        chip.position.set(12, 20, 7);
        group.add(chip);

        return {
            group: group,
            update: function (t) {
                // idle handled globally; small tap with right arm at ~1.0s
                var tap = Math.max(0, Math.min(1, (t - 0.7) / 0.4));
                char.setArms(0.15, -0.15 - easeInOut(tap) * 0.5);

                // plane launch 1.1s -> 2.6s, flies up-right and fades
                var pl = clamp01((t - 1.1) / 1.5);
                var e = easeIn(pl);
                plane.visible = pl > 0 && pl < 1;
                plane.position.set(-2 + e * 46, -8 + e * 44, 6);
                plane.rotation.z = -0.5 + e * 0.9;
                setOpacity(plane, 1 - pl);

                // applied chip pops at 2.4s
                var cp = clamp01((t - 2.4) / 0.5);
                chip.visible = cp > 0;
                chip.scale.setScalar(easeOutBack(cp) * 1.0 + 0.0001);
                setOpacity(chip, cp);
            }
        };
    }
    function easeIn(t) { return t * t; }

    // ---- Scene 2: ACCEPTED -------------------------------------------------
    function buildAccepted() {
        var group = new THREE.Group();
        var char = makeCharacter();
        char.position.set(-14, -2, 0); char.scale.setScalar(0.9);
        group.add(char);

        // phone that wiggles
        var phone = new THREE.Group();
        phone.add(rrect(12, 22, 3, COLORS.primaryDark));
        phone.add(withPos(rrect(10, 16, 1.5, COLORS.white), 0, 1, 1));
        phone.add(withPos(circle(2.2, COLORS.green), 0, -7, 2));
        phone.position.set(-30, 6, 4);
        group.add(phone);

        // "You're Hired!" card slides in from top
        var card = makeLabel("You're Hired!", { bg: COLORS.white, color: COLORS.primary, check: true, checkBg: COLORS.green, worldHeight: 9, radius: 14 });
        card.position.set(6, 26, 6);
        group.add(card);

        // confetti (deterministic burst)
        var confetti = new THREE.Group();
        var palette = [COLORS.yellow, COLORS.coral, COLORS.green, COLORS.primary, COLORS.white];
        var N = 34, parts = [];
        for (var i = 0; i < N; i++) {
            var p = rrect(2.2, 2.2, 0.6, palette[i % palette.length]);
            confetti.add(p);
            parts.push({
                mesh: p,
                ang: Math.random() * Math.PI * 2,
                spd: 26 + Math.random() * 34,
                spin: (Math.random() - 0.5) * 12,
                size: 0.7 + Math.random() * 0.8
            });
        }
        confetti.position.set(6, 20, 7);
        group.add(confetti);

        return {
            group: group,
            update: function (t) {
                // phone wiggle 0.2..1.4s
                var w = clamp01((t - 0.2) / 1.2);
                phone.rotation.z = Math.sin(t * 22) * 0.18 * (1 - w) * (w > 0 ? 1 : 0);

                // card slide-in with overshoot, 0.5s -> 1.3s
                var cs = clamp01((t - 0.5) / 0.8);
                card.position.y = lerp(40, 22, easeOutBack(cs));
                setOpacity(card, cs);
                card.visible = cs > 0;

                // happy jump at ~1.3s (squash + up + arms up)
                var j = clamp01((t - 1.3) / 0.9);
                var jump = Math.sin(clamp01(j) * Math.PI) * 10;
                char.position.y = -2 + jump;
                var arm = Math.sin(clamp01(j) * Math.PI);
                char.setArms(0.15 + arm * 1.3, -0.15 - arm * 1.3);

                // confetti burst starting 1.2s
                var tau = Math.max(0, t - 1.2);
                var vis = tau > 0 && tau < 2.6;
                confetti.visible = vis;
                for (var i = 0; i < parts.length; i++) {
                    var pt = parts[i], m = pt.mesh;
                    var x = Math.cos(pt.ang) * pt.spd * tau;
                    var y = Math.sin(pt.ang) * pt.spd * tau - 20 * tau * tau;
                    m.position.set(x, y, 0);
                    m.rotation.z = pt.spin * tau;
                    m.scale.setScalar(pt.size);
                    setOpacity(m, clamp01(1 - tau / 2.6));
                }
            }
        };
    }

    // ---- Scene 3: PAID -----------------------------------------------------
    function buildPaid() {
        var group = new THREE.Group();

        // wallet
        var wallet = new THREE.Group();
        wallet.add(withPos(shadow(20), 0, -18, -1));
        wallet.add(rrect(40, 26, 4, COLORS.wallet));
        wallet.add(withPos(rrect(40, 12, 4, COLORS.primaryDark), 0, -7, 1));
        wallet.add(withPos(rrect(9, 7, 2, COLORS.yellow), 13, -6, 2)); // clasp
        wallet.position.set(0, -8, 3);
        group.add(wallet);

        // falling money (notes + coins), continuous deterministic stream
        var money = new THREE.Group();
        var items = [], M = 12;
        for (var i = 0; i < M; i++) {
            var isCoin = i % 3 === 0;
            var m;
            if (isCoin) {
                m = new THREE.Group();
                m.add(circle(3, COLORS.coin));
                m.add(withPos(circle(2, COLORS.yellow), 0, 0, 1));
            } else {
                m = makeLabel(CURRENCY, { color: COLORS.white, worldHeight: 5, weight: "bold", padX: 12, padY: 6, bg: COLORS.note, radius: 3 });
            }
            money.add(m);
            items.push({ mesh: m, x0: (Math.random() * 2 - 1) * 26, off: Math.random(), spin: (Math.random() - 0.5) * 3, coin: isCoin });
        }
        group.add(money);

        // balance counter
        var balance = makeLabel(CURRENCY + "0", { bg: COLORS.white, color: COLORS.primary, worldHeight: 9, radius: 12, padX: 40 });
        balance.position.set(0, 26, 6);
        group.add(balance);

        return {
            group: group,
            update: function (t) {
                // wallet grows in 0..0.5, satisfied bounce ~3.4
                var win = easeOutBack(clamp01(t / 0.5));
                var bounce = 1 + Math.sin(clamp01((t - 3.3) / 0.5) * Math.PI) * 0.12;
                wallet.scale.setScalar(win * bounce);

                // money stream falls into wallet
                for (var i = 0; i < items.length; i++) {
                    var it = items[i], m = it.mesh;
                    var period = 2.4;
                    var ph = ((t / period) + it.off) % 1;         // 0..1 loop
                    var e = easeIn(ph);
                    m.position.set(lerp(it.x0, 0, e), lerp(40, -6, e), 4);
                    m.rotation.z = it.spin * ph;
                    var s = lerp(1, 0.2, ph);
                    m.scale.setScalar(s);
                    setOpacity(m, ph < 0.85 ? 1 : (1 - (ph - 0.85) / 0.15));
                    m.visible = t > 0.4;
                }

                // counter ticks up 0.6s -> 3.2s
                var cv = easeOut(clamp01((t - 0.6) / 2.6));
                balance.userData.setText(CURRENCY + commas(BALANCE_TARGET * cv));
            }
        };
    }

    // ---- Scene 4: AFFORD ---------------------------------------------------
    function buildAfford() {
        var group = new THREE.Group();
        var char = makeCharacter();
        char.position.set(-30, -2, 0); char.scale.setScalar(0.95);
        char.setArms(1.25, -1.25);   // arms up, proud
        group.add(char);

        var makers = [iconHouse, iconCar, iconCart, iconCap];
        var icons = [];
        var startX = -6, gap = 20;
        for (var i = 0; i < makers.length; i++) {
            var wrap = new THREE.Group();
            wrap.add(withPos(circle(11, COLORS.white, 0.10), 0, 0, -1));
            wrap.add(makers[i]());
            wrap.position.set(startX + i * gap, 4, 2);
            group.add(wrap);
            icons.push(wrap);
        }

        return {
            group: group,
            update: function (t) {
                // proud little bob
                char.position.y = -2 + Math.sin(t * 2) * 0.6;
                // icons pop in sequence
                for (var i = 0; i < icons.length; i++) {
                    var start = 0.4 + i * 0.5;
                    var p = clamp01((t - start) / 0.5);
                    icons[i].visible = p > 0;
                    icons[i].scale.setScalar(p > 0 ? easeOutBack(p) : 0.0001);
                    setOpacity(icons[i], p);
                }
            }
        };
    }

    // ======================= OPACITY / DISPOSE UTILS =========================
    function setOpacity(obj, o) {
        obj.traverse(function (n) {
            if (n.material) {
                var base = n.userData.baseOpacity != null ? n.userData.baseOpacity : 1;
                n.material.opacity = base * o;
            }
        });
    }
    function disposeObject(root) {
        root.traverse(function (n) {
            if (n.geometry) n.geometry.dispose();
            if (n.material) {
                if (n.material.map) n.material.map.dispose();
                n.material.dispose();
            }
        });
    }

    // ============================= INSTANCE ==================================
    function mount(container) {
        if (!container || typeof THREE === "undefined") return null;

        var reduce = global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;

        var W = container.clientWidth || 1, H = container.clientHeight || 1;
        var scene = new THREE.Scene();
        scene.background = new THREE.Color(COLORS.navy);

        var camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -100, 100);

        var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
        renderer.setSize(W, H);
        container.appendChild(renderer.domElement);
        renderer.domElement.setAttribute("aria-hidden", "true");
        renderer.domElement.style.display = "block";

        // Accessible text alternative
        var sr = document.createElement("span");
        sr.textContent = "Animated illustration: apply for a job, get accepted, get paid, and afford a better life with 1mjobs.";
        sr.style.cssText = "position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);";
        container.appendChild(sr);

        var root = new THREE.Group();
        scene.add(root);
        var scenes = [buildApply(), buildAccepted(), buildPaid(), buildAfford()];
        for (var i = 0; i < scenes.length; i++) { scene.add(scenes[i].group); scenes[i].group.visible = false; }

        function resize() {
            W = container.clientWidth || 1; H = container.clientHeight || 1;
            var aspect = W / H;
            var halfW, halfH;
            if (aspect >= 1) { halfH = REF; halfW = REF * aspect; }
            else { halfW = REF; halfH = REF / aspect; }
            camera.left = -halfW; camera.right = halfW;
            camera.top = halfH; camera.bottom = -halfH;
            camera.updateProjectionMatrix();
            renderer.setSize(W, H);
        }
        resize();

        var cfFrac = CROSSFADE / SCENE_DURATION;

        function renderFrame(animTime) {
            // hide all first
            for (var s = 0; s < scenes.length; s++) scenes[s].group.visible = false;

            var t = ((animTime % TOTAL) + TOTAL) % TOTAL;
            var phase = t / SCENE_DURATION;          // 0..NUM_SCENES
            var si = Math.floor(phase) % NUM_SCENES;
            var f = phase - Math.floor(phase);       // 0..1 within scene
            var e = f > (1 - cfFrac) ? easeInOut((f - (1 - cfFrac)) / cfFrac) : 0;

            // current scene
            var cur = scenes[si];
            cur.group.visible = true;
            cur.group.position.x = -e * SLIDE;
            setOpacity(cur.group, 1 - e);
            cur.update(f * SCENE_DURATION);

            // incoming scene during crossfade (rendered at its opening frame)
            if (e > 0) {
                var ni = (si + 1) % NUM_SCENES;
                var nxt = scenes[ni];
                nxt.group.visible = true;
                nxt.group.position.x = (1 - e) * SLIDE;
                setOpacity(nxt.group, e);
                nxt.update(0);
            }

            // gentle idle float on the whole stage for life
            root.position.y = 0;
            scene.position.y = Math.sin(animTime * 1.1) * 0.8;

            renderer.render(scene, camera);
        }

        function teardownGL() {
            disposeObject(scene);
            renderer.dispose();
            if (renderer.domElement && renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
            if (sr.parentNode) sr.parentNode.removeChild(sr);
        }

        // ---- reduced motion: one static "final happy" frame, no loop -------
        if (reduce) {
            var s4 = scenes[3];
            s4.group.visible = true; s4.group.position.x = 0; setOpacity(s4.group, 1);
            s4.update(SCENE_DURATION);
            var drawStatic = function () { resize(); s4.update(SCENE_DURATION); renderer.render(scene, camera); };
            drawStatic();
            global.addEventListener("resize", drawStatic);
            return {
                unmount: function () {
                    global.removeEventListener("resize", drawStatic);
                    teardownGL();
                }
            };
        }

        // ---- animation loop with pause on hidden / off-screen --------------
        var rafId = null, running = false, animTime = 0, last = 0;

        function loop(now) {
            if (!running) return;
            var dt = (now - last) / 1000; last = now;
            if (dt > 0.1) dt = 0.1;          // clamp big gaps (tab refocus)
            animTime += dt;
            renderFrame(animTime);
            rafId = global.requestAnimationFrame(loop);
        }
        function start() {
            if (running) return;
            running = true; last = performance.now();
            rafId = global.requestAnimationFrame(loop);
        }
        function stop() {
            running = false;
            if (rafId) { global.cancelAnimationFrame(rafId); rafId = null; }
        }

        function onVisibility() { if (document.hidden) stop(); else if (onScreen) start(); }
        var onScreen = true;
        var io = null;
        if (global.IntersectionObserver) {
            io = new IntersectionObserver(function (entries) {
                onScreen = entries[0].isIntersecting;
                if (onScreen && !document.hidden) start(); else stop();
            }, { threshold: 0.05 });
            io.observe(container);
        }
        document.addEventListener("visibilitychange", onVisibility);

        var resizeBound = function () { resize(); if (!running) renderFrame(animTime); };
        function attachResize() { global.addEventListener("resize", resizeBound); }
        attachResize();

        start();

        return {
            unmount: function () {
                stop();
                document.removeEventListener("visibilitychange", onVisibility);
                global.removeEventListener("resize", resizeBound);
                if (io) io.disconnect();
                teardownGL();
            }
        };
    }

    var current = null;
    global.JobJourney = {
        mount: function (container) {
            if (current) { current.unmount(); current = null; }
            current = mount(container);
            return current;
        },
        unmount: function () { if (current) { current.unmount(); current = null; } }
    };

})(window);
