/*
 * 1mjobs — "Job Journey" 3D background animation
 * ------------------------------------------------------------------
 * A wordless looping vignette of the freelance lifecycle, told with props
 * (no cartoon human): get a job offer -> accept it -> submit the work ->
 * get paid. Built on three.js r128. Calm, premium, brand-themed; it sits
 * behind the results panel so it stays atmospheric, never busy.
 *
 * Public API (unchanged, drop-in):
 *   JobJourney.mount(containerEl)  -> instance { unmount() }
 *   JobJourney.unmount()
 */
(function (global) {
    'use strict';
    var THREE = global.THREE;

    var BG = 0x0B1020;
    var C = {
        card:   '#F4F6FF',
        brand:  0x2A41E8,
        indigo: 0x4F6BFF,
        blue:   '#2A41E8',
        blueL:  '#6C86FF',
        cyan:   '#58C4FF',
        green:  '#22C55E',
        gold:   '#F5A623',
        ink:    '#191919'
    };
    var LOOP = 22; // seconds

    // easeInOutCubic
    function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
    function smooth(t, a, b) { return ease(clamp01((t - a) / (b - a))); }
    // trapezoid envelope: 0 -> 1 over [a,b], hold, 1 -> 0 over [c,d]
    function env(t, a, b, c, d) {
        if (t <= a || t >= d) return 0;
        if (t < b) return ease((t - a) / (b - a));
        if (t < c) return 1;
        return ease(1 - (t - c) / (d - c));
    }

    function Instance(container) {
        this.container = container;
        this.destroyed = false;
        this.disposables = [];
        this.reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
        this._init();
    }

    // ---- small builders -------------------------------------------------
    Instance.prototype._canvasTex = function (w, h, draw) {
        var cv = document.createElement('canvas');
        cv.width = w; cv.height = h;
        var g = cv.getContext('2d');
        draw(g, w, h);
        var tx = new THREE.CanvasTexture(cv);
        tx.anisotropy = 4;
        this.disposables.push(tx);
        return { tex: tx, cv: cv, ctx: g };
    };

    Instance.prototype._track = function (obj) { this.disposables.push(obj); return obj; };

    Instance.prototype._roundedRectShape = function (w, h, r) {
        var s = new THREE.Shape(), x = -w / 2, y = -h / 2;
        s.moveTo(x + r, y);
        s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
        s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
        s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
        return s;
    };

    // A flat rounded card facing +Z, with a texture on its front face.
    Instance.prototype._card = function (w, h, surface, faceTex) {
        var grp = new THREE.Group();
        var geo = this._track(new THREE.ExtrudeGeometry(this._roundedRectShape(w, h, Math.min(w, h) * 0.09), { depth: 0.14, bevelEnabled: false }));
        var mat = this._track(new THREE.MeshStandardMaterial({ color: surface, roughness: 0.55, metalness: 0.05, transparent: true }));
        var body = new THREE.Mesh(geo, mat);
        grp.add(body);
        if (faceTex) {
            var pgeo = this._track(new THREE.PlaneGeometry(w * 0.98, h * 0.98));
            var pmat = this._track(new THREE.MeshBasicMaterial({ map: faceTex, transparent: true }));
            var face = new THREE.Mesh(pgeo, pmat);
            face.position.z = 0.145;
            grp.add(face);
        }
        grp.userData.mats = [mat].concat(faceTex ? [face.material] : []);
        return grp;
    };

    Instance.prototype._glow = function (rgba, scale) {
        var tex = this._canvasTex(128, 128, function (g, s) {
            var grd = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
            grd.addColorStop(0, rgba);
            grd.addColorStop(1, 'rgba(0,0,0,0)');
            g.fillStyle = grd; g.fillRect(0, 0, s, s);
        }).tex;
        var mat = this._track(new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, depthTest: false, opacity: 1 }));
        var sp = new THREE.Sprite(mat);
        sp.scale.set(scale, scale, 1);
        return sp;
    };

    function setOpacity(grp, o) {
        grp.traverse(function (n) {
            if (n.material) {
                if (Array.isArray(n.material)) n.material.forEach(function (m) { m.transparent = true; m.opacity = o; });
                else { n.material.transparent = true; n.material.opacity = o; }
            }
        });
    }

    // ---- scene ----------------------------------------------------------
    Instance.prototype._init = function () {
        var self = this;
        var rect = this.container.getBoundingClientRect();
        var w = Math.max(1, rect.width), h = Math.max(1, rect.height);

        var renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(w, h);
        renderer.setClearColor(BG, 1);
        renderer.domElement.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;';
        this.container.appendChild(renderer.domElement);
        this.renderer = renderer;

        var scene = new THREE.Scene();
        scene.background = new THREE.Color(BG);
        scene.fog = new THREE.Fog(BG, 13, 34);
        this.scene = scene;

        var cam = new THREE.PerspectiveCamera(35, w / h, 0.1, 100);
        cam.position.set(0, 0.4, 13.5);
        cam.lookAt(0, 0.2, 0);
        this.cam = cam;

        scene.add(new THREE.AmbientLight(0x3A4A80, 0.7));
        var key = new THREE.DirectionalLight(0xFFFFFF, 0.95);
        key.position.set(4, 8, 7); scene.add(key);
        var rim = new THREE.PointLight(0x2A41E8, 0.9, 60); rim.position.set(-6, 2, -6); scene.add(rim);
        this.warm = new THREE.PointLight(0xF5A623, 0.0, 40); this.warm.position.set(0, 0, 6); scene.add(this.warm);

        // central brand glow (background depth)
        var bgGlow = this._glow('rgba(42,65,232,0.55)', 22); bgGlow.position.set(0, 0.2, -6); scene.add(bgGlow);

        this._buildOffer();
        this._buildAccept();
        this._buildSubmit();
        this._buildPaid();

        this.clock = new THREE.Clock();

        this._onResize = function () { self._resize(); };
        window.addEventListener('resize', this._onResize);
        if (window.ResizeObserver) { this.ro = new ResizeObserver(function () { self._resize(); }); this.ro.observe(this.container); }

        var loop = function () {
            if (self.destroyed) return;
            self._frame();
            self.raf = requestAnimationFrame(loop);
        };
        this.raf = requestAnimationFrame(loop);
    };

    Instance.prototype._resize = function () {
        var r = this.container.getBoundingClientRect();
        var w = Math.max(1, r.width), h = Math.max(1, r.height);
        this.renderer.setSize(w, h);
        this.cam.aspect = w / h; this.cam.updateProjectionMatrix();
    };

    // ---- beat 1: the offer ---------------------------------------------
    Instance.prototype._buildOffer = function () {
        var self = this;
        var tex = this._canvasTex(320, 400, function (g, W, H) {
            g.clearRect(0, 0, W, H);
            // briefcase
            g.strokeStyle = C.blue; g.lineWidth = 12; g.lineJoin = 'round';
            var bx = W / 2 - 62, by = 96, bw = 124, bh = 92;
            g.strokeRect(bx, by, bw, bh);
            g.beginPath(); g.moveTo(W / 2 - 26, by); g.lineTo(W / 2 - 26, by - 22);
            g.lineTo(W / 2 + 26, by - 22); g.lineTo(W / 2 + 26, by); g.stroke();
            g.fillStyle = C.blueL; g.fillRect(bx, by + bh / 2 - 6, bw, 12);
            // title
            g.fillStyle = C.ink; g.font = '600 30px Inter, sans-serif'; g.textAlign = 'center';
            g.fillText('New Job Offer', W / 2, 250);
            // doc lines
            g.fillStyle = 'rgba(25,25,25,0.18)';
            g.fillRect(W / 2 - 96, 286, 192, 10);
            g.fillRect(W / 2 - 96, 310, 150, 10);
            // pill
            g.fillStyle = C.blue; g.beginPath();
            var px = W / 2 - 62, py = 340, pw = 124, ph = 34, pr = 17;
            g.moveTo(px + pr, py); g.arcTo(px + pw, py, px + pw, py + ph, pr);
            g.arcTo(px + pw, py + ph, px, py + ph, pr); g.arcTo(px, py + ph, px, py, pr);
            g.arcTo(px, py, px + pw, py, pr); g.fill();
            g.fillStyle = '#fff'; g.font = '600 16px Inter, sans-serif'; g.fillText('REVIEW', W / 2, py + 23);
        }).tex;

        var g = new THREE.Group();
        g.add(this._glow('rgba(42,65,232,0.85)', 8.5));
        var card = this._card(3.1, 3.9, C.card, tex);
        g.add(card);
        // notification ring
        var rg = this._track(new THREE.RingGeometry(0.9, 1.02, 48));
        var rm = this._track(new THREE.MeshBasicMaterial({ color: 0x6C86FF, transparent: true, side: THREE.DoubleSide }));
        this.offerRing = new THREE.Mesh(rg, rm); this.offerRing.position.set(1.1, 1.5, 0.2); g.add(this.offerRing);
        this.offer = g; g.visible = false; this.scene.add(g);
    };

    // ---- beat 2: accept -------------------------------------------------
    Instance.prototype._buildAccept = function () {
        var g = new THREE.Group();
        g.add(this._glow('rgba(34,197,94,0.8)', 7));
        var cgeo = this._track(new THREE.CircleGeometry(1.15, 48));
        var cmat = this._track(new THREE.MeshStandardMaterial({ color: 0x22C55E, roughness: 0.4, metalness: 0.1, transparent: true, emissive: 0x0c3a1c }));
        g.add(new THREE.Mesh(cgeo, cmat));
        var checkTex = this._canvasTex(128, 128, function (gg, s) {
            gg.clearRect(0, 0, s, s);
            gg.strokeStyle = '#fff'; gg.lineWidth = 12; gg.lineCap = 'round'; gg.lineJoin = 'round';
            gg.beginPath(); gg.moveTo(38, 66); gg.lineTo(56, 86); gg.lineTo(92, 44); gg.stroke();
        }).tex;
        var pmat = this._track(new THREE.MeshBasicMaterial({ map: checkTex, transparent: true }));
        var check = new THREE.Mesh(this._track(new THREE.PlaneGeometry(1.7, 1.7)), pmat);
        check.position.z = 0.02; g.add(check);

        // confetti triangles (logo motif)
        this.confetti = [];
        var tshape = new THREE.Shape(); tshape.moveTo(0, 0.16); tshape.lineTo(-0.14, -0.1); tshape.lineTo(0.14, -0.1); tshape.closePath();
        for (var i = 0; i < 14; i++) {
            var tg = this._track(new THREE.ShapeGeometry(tshape));
            var tm = this._track(new THREE.MeshBasicMaterial({ color: (i % 3 ? 0x6C86FF : 0x2A41E8), transparent: true, side: THREE.DoubleSide }));
            var tri = new THREE.Mesh(tg, tm);
            var ang = (i / 14) * Math.PI * 2;
            tri.userData = { ang: ang, spin: (Math.random() * 2 - 1) * 3, rad: 1.4 + Math.random() * 1.2 };
            g.add(tri); this.confetti.push(tri);
        }
        this.accept = g; g.visible = false; this.scene.add(g);
    };

    // ---- beat 3: submit work -------------------------------------------
    Instance.prototype._buildSubmit = function () {
        var g = new THREE.Group();
        g.add(this._glow('rgba(88,196,255,0.7)', 7));
        // package
        var box = new THREE.Mesh(
            this._track(new THREE.BoxGeometry(1.9, 1.5, 1.9)),
            this._track(new THREE.MeshStandardMaterial({ color: 0x4F6BFF, roughness: 0.5, metalness: 0.1, transparent: true }))
        );
        box.rotation.y = 0.5; box.position.y = -0.1;
        // upload arrow on top face via small plane
        var arrowTex = this._canvasTex(128, 128, function (gg, s) {
            gg.clearRect(0, 0, s, s);
            gg.strokeStyle = '#fff'; gg.lineWidth = 12; gg.lineCap = 'round'; gg.lineJoin = 'round';
            gg.beginPath(); gg.moveTo(s / 2, 96); gg.lineTo(s / 2, 40); gg.stroke();
            gg.beginPath(); gg.moveTo(s / 2 - 22, 60); gg.lineTo(s / 2, 34); gg.lineTo(s / 2 + 22, 60); gg.stroke();
        }).tex;
        var arrow = new THREE.Mesh(this._track(new THREE.PlaneGeometry(1.1, 1.1)), this._track(new THREE.MeshBasicMaterial({ map: arrowTex, transparent: true })));
        arrow.position.set(0, 0.9, 0); arrow.rotation.x = 0; box.add(arrow);
        this.pkg = box; g.add(box);

        // progress ring (canvas, redrawn during beat)
        this.progress = this._canvasTex(256, 256, function () {});
        var pm = this._track(new THREE.MeshBasicMaterial({ map: this.progress.tex, transparent: true }));
        this.progressMesh = new THREE.Mesh(this._track(new THREE.PlaneGeometry(3.6, 3.6)), pm);
        this.progressMesh.position.z = 1.4; g.add(this.progressMesh);

        this.submit = g; g.visible = false; this.scene.add(g);
    };

    Instance.prototype._drawProgress = function (p) {
        var g = this.progress.ctx, s = 256;
        g.clearRect(0, 0, s, s);
        g.lineWidth = 12; g.lineCap = 'round';
        g.strokeStyle = 'rgba(255,255,255,0.12)';
        g.beginPath(); g.arc(s / 2, s / 2, 110, 0, Math.PI * 2); g.stroke();
        var grd = g.createLinearGradient(0, 0, s, s);
        grd.addColorStop(0, C.cyan); grd.addColorStop(1, C.gold);
        g.strokeStyle = grd;
        g.beginPath(); g.arc(s / 2, s / 2, 110, -Math.PI / 2, -Math.PI / 2 + p * Math.PI * 2); g.stroke();
        this.progress.tex.needsUpdate = true;
    };

    // ---- beat 4: get paid ----------------------------------------------
    Instance.prototype._buildPaid = function () {
        var g = new THREE.Group();
        g.add(this._glow('rgba(245,166,35,0.85)', 8.5));
        // wallet
        var wTex = this._canvasTex(320, 220, function (gg, W, H) {
            gg.clearRect(0, 0, W, H);
            gg.fillStyle = 'rgba(245,166,35,0.18)'; gg.fillRect(0, 0, W, 54);
            gg.fillStyle = C.gold; gg.font = '600 26px Inter, sans-serif'; gg.textAlign = 'left';
            gg.fillText('Wallet', 26, 36);
            gg.strokeStyle = 'rgba(245,166,35,0.9)'; gg.lineWidth = 8;
            gg.strokeRect(210, 96, 84, 60);
            gg.fillStyle = C.gold; gg.beginPath(); gg.arc(214, 126, 9, 0, Math.PI * 2); gg.fill();
        }).tex;
        var wallet = this._card(3.4, 2.35, 0x141a35, wTex);
        wallet.position.y = -0.3; g.add(wallet);
        this.wallet = wallet;

        // coin
        var coinTex = this._canvasTex(128, 128, function (gg, s) {
            gg.clearRect(0, 0, s, s);
            gg.fillStyle = '#F7B733'; gg.beginPath(); gg.arc(s / 2, s / 2, 58, 0, Math.PI * 2); gg.fill();
            gg.strokeStyle = '#E6820F'; gg.lineWidth = 7; gg.beginPath(); gg.arc(s / 2, s / 2, 54, 0, Math.PI * 2); gg.stroke();
            gg.fillStyle = '#7a4b06'; gg.font = '700 64px Inter, sans-serif'; gg.textAlign = 'center';
            gg.fillText('₦', s / 2, s / 2 + 24);
        }).tex;
        this.coin = new THREE.Mesh(this._track(new THREE.CircleGeometry(0.62, 40)), this._track(new THREE.MeshBasicMaterial({ map: coinTex, transparent: true })));
        this.coin.position.set(0, 2.6, 0.3); g.add(this.coin);
        this.coinGlow = this._glow('rgba(245,166,35,0.9)', 2.2); this.coinGlow.position.copy(this.coin.position); g.add(this.coinGlow);

        // balance chip
        this.balance = this._canvasTex(320, 96, function () {});
        this.balanceMesh = new THREE.Mesh(this._track(new THREE.PlaneGeometry(3.0, 0.9)), this._track(new THREE.MeshBasicMaterial({ map: this.balance.tex, transparent: true })));
        this.balanceMesh.position.set(0, 1.55, 0.4); g.add(this.balanceMesh);

        this.paid = g; g.visible = false; this.scene.add(g);
    };

    Instance.prototype._drawBalance = function (val) {
        var g = this.balance.ctx, W = 320, H = 96;
        g.clearRect(0, 0, W, H);
        g.fillStyle = 'rgba(34,197,94,0.16)';
        g.beginPath();
        var r = 24; g.moveTo(r, 6); g.arcTo(W - 6, 6, W - 6, H - 6, r); g.arcTo(W - 6, H - 6, 6, H - 6, r);
        g.arcTo(6, H - 6, 6, 6, r); g.arcTo(6, 6, W - 6, 6, r); g.fill();
        g.fillStyle = '#22C55E'; g.font = '600 40px Inter, sans-serif'; g.textAlign = 'center';
        g.fillText('+ ₦' + Math.round(val).toLocaleString('en-NG'), W / 2, H / 2 + 15);
        this.balance.tex.needsUpdate = true;
    };

    // ---- frame ----------------------------------------------------------
    Instance.prototype._frame = function () {
        var el = this.clock.getElapsedTime();
        var t = this.reduced ? 0.84 : (el % LOOP) / LOOP;
        var bob = Math.sin(el * 0.9);

        // camera gentle dolly + orbit
        var ph = t * Math.PI * 2;
        this.cam.position.set(Math.sin(ph) * 0.9, 0.4 + Math.sin(ph * 2) * 0.18, 13.5 + Math.cos(ph) * 0.6);
        this.cam.lookAt(0, 0.15, 0);

        // -- offer
        var eO = env(t, 0.02, 0.10, 0.24, 0.30) || (this.reduced ? 0 : 0);
        this.offer.visible = eO > 0.001;
        if (this.offer.visible) {
            setOpacity(this.offer, eO);
            this.offer.position.set(0, 0.2 + (1 - eO) * 1.2 + bob * 0.06, 0);
            this.offer.rotation.set(-0.05, (1 - eO) * -0.4 + Math.sin(el * 0.6) * 0.05, 0);
            this.offer.scale.setScalar(0.9 + eO * 0.1);
            var pr = (Math.sin(el * 2.2) * 0.5 + 0.5);
            this.offerRing.scale.setScalar(0.6 + pr * 1.1);
            this.offerRing.material.opacity = (1 - pr) * 0.7 * eO;
        }

        // -- accept
        var eA = env(t, 0.26, 0.33, 0.44, 0.50);
        this.accept.visible = eA > 0.001;
        if (this.accept.visible) {
            setOpacity(this.accept, eA);
            var pop = 0.8 + ease(clamp01((t - 0.26) / 0.09)) * 0.2 + Math.sin(el * 3) * 0.01;
            this.accept.position.set(0, 0.25 + bob * 0.05, 0);
            this.accept.scale.setScalar(pop);
            var spread = ease(clamp01((t - 0.30) / 0.12));
            for (var i = 0; i < this.confetti.length; i++) {
                var c = this.confetti[i], rad = c.userData.rad * spread;
                c.position.set(Math.cos(c.userData.ang) * rad, Math.sin(c.userData.ang) * rad + spread * 0.4, 0.3);
                c.rotation.z = el * c.userData.spin;
                c.material.opacity = eA * (1 - spread) * 0.9;
                c.scale.setScalar(0.8 + spread * 0.6);
            }
        }

        // -- submit
        var eS = env(t, 0.48, 0.55, 0.66, 0.72);
        this.submit.visible = eS > 0.001;
        if (this.submit.visible) {
            setOpacity(this.submit, eS);
            var local = clamp01((t - 0.50) / 0.16);
            this._drawProgress(local);
            var lift = ease(clamp01((t - 0.62) / 0.10)); // dissolve up near the end
            this.submit.position.set(0, 0.1 + bob * 0.06 + lift * 1.4, 0);
            this.pkg.rotation.y = 0.5 + el * 0.35;
            this.pkg.material.opacity = eS * (1 - lift);
            this.progressMesh.rotation.z = -el * 0.4;
        }

        // -- paid
        var eP = env(t, 0.70, 0.78, 0.92, 0.98) || (this.reduced ? 1 : 0);
        this.paid.visible = eP > 0.001;
        if (this.paid.visible) {
            setOpacity(this.paid, eP);
            this.paid.position.set(0, 0.05 + bob * 0.05, 0);
            var drop = this.reduced ? 1 : ease(clamp01((t - 0.76) / 0.10));
            this.coin.position.y = 2.6 - drop * 2.5;
            this.coin.rotation.y = el * 3.0;
            this.coin.scale.setScalar(1 - drop * 0.25);
            this.coinGlow.position.copy(this.coin.position);
            this.coinGlow.material.opacity = eP;
            var settle = this.reduced ? 1 : clamp01((t - 0.80) / 0.12);
            this._drawBalance(settle * 50000);
            this.balanceMesh.material.opacity = eP * settle;
            this.warm.intensity = eP * (0.6 + Math.max(0, Math.sin((t - 0.80) * 30)) * 0.8);
        } else {
            this.warm.intensity = 0;
        }

        this.renderer.render(this.scene, this.cam);
    };

    Instance.prototype.unmount = function () {
        this.destroyed = true;
        if (this.raf) cancelAnimationFrame(this.raf);
        window.removeEventListener('resize', this._onResize);
        if (this.ro) this.ro.disconnect();
        for (var i = 0; i < this.disposables.length; i++) {
            var d = this.disposables[i];
            if (d && d.dispose) { try { d.dispose(); } catch (e) {} }
        }
        if (this.renderer) {
            this.renderer.dispose();
            if (this.renderer.domElement && this.renderer.domElement.parentNode) {
                this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
            }
        }
    };

    var current = null;
    global.JobJourney = {
        mount: function (el) {
            if (!el || !global.THREE) return null;
            if (current) current.unmount();
            current = new Instance(el);
            return current;
        },
        unmount: function () { if (current) { current.unmount(); current = null; } }
    };

})(window);
