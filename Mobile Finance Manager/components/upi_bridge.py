import html
import json
from urllib.parse import parse_qs, urlencode, urlparse
import streamlit as st
import streamlit.components.v1 as components


UPI_APPS = {
    "None": {
        "label": "Disabled",
        "android_pkg": None,
        "ios_scheme": None,
    },
    "CRED": {
        "label": "CRED",
        "android_pkg": "com.dreamplug.androidapp",
        "ios_scheme": "cred://upi/pay",
        "ios_home": "cred://",
    },
    "Paytm": {
        "label": "Paytm",
        "android_pkg": "net.one97.paytm",
        "ios_scheme": "paytmmp://pay",
        "ios_home": "paytmmp://",
    },
    "Google Pay": {
        "label": "Google Pay",
        "android_pkg": "com.google.android.apps.nbu.paisa.user",
        "ios_scheme": "tez://upi/pay",
        "ios_home": "tez://",
    },
    "PhonePe": {
        "label": "PhonePe",
        "android_pkg": "com.phonepe.app",
        "ios_scheme": "phonepe://pay",
        "ios_home": "phonepe://",
    },
    "BHIM": {
        "label": "BHIM",
        "android_pkg": "in.org.npci.upiapp",
        "ios_scheme": "bhim://upi/pay",
        "ios_home": "bhim://",
    },
    "System UPI": {
        "label": "System UPI Chooser",
        "android_pkg": None,
        "ios_scheme": "upi://pay",
        "ios_home": "upi://",
    },
}

UPI_APP_OPTIONS = list(UPI_APPS.keys())
PAY_ACTIVE_APP_OPTIONS = [k for k in UPI_APP_OPTIONS if k != "None"]


def parse_upi_qr(raw_value: str) -> dict | None:
    """
    Parse an NPCI UPI QR URI (upi://pay?pa=...&pn=...) or bare UPI ID (name@bank).
    Returns normalized dict with pa, pn, am, tn, mc, tr, orgid, mode, or None if invalid.
    """
    if not raw_value or not isinstance(raw_value, str):
        return None
    text = raw_value.strip()
    if not text:
        return None

    # Allow bare VPA entry like "shop@okaxis"
    if "://" not in text and "@" in text and " " not in text and "?" not in text:
        return {
            "pa": text,
            "pn": "",
            "am": None,
            "tn": "",
            "mc": "",
            "tr": "",
            "orgid": "",
            "mode": "",
        }

    low = text.lower()
    if not (low.startswith("upi://") or low.startswith("upiglobal://")):
        return None

    parsed = urlparse(text)
    qs = parse_qs(parsed.query, keep_blank_values=False)

    def _first(key: str) -> str:
        vals = qs.get(key) or qs.get(key.upper()) or qs.get(key.lower())
        return vals[0].strip() if vals and vals[0] else ""

    pa = _first("pa")
    if not pa or "@" not in pa:
        return None

    raw_am = _first("am")
    am_val = None
    if raw_am:
        try:
            f = float(raw_am)
            if f > 0:
                am_val = f
        except ValueError:
            am_val = None

    return {
        "pa": pa,
        "pn": _first("pn"),
        "am": am_val,
        "tn": _first("tn"),
        "mc": _first("mc"),
        "tr": _first("tr"),
        "orgid": _first("orgid"),
        "mode": _first("mode"),
    }


def _format_amt_str(amount: float) -> str:
    val = round(float(amount), 2)
    if val.is_integer():
        return str(int(val))
    return f"{val:.2f}".rstrip("0").rstrip(".")


def build_upi_urls(app_name: str, parsed_qr: dict | None, amount: float, note: str = "") -> dict:
    """
    Build cross-platform launch URLs (iOS scheme + Android intent + generic upi:// fallback).
    """
    cfg = UPI_APPS.get(app_name) or UPI_APPS["System UPI"]
    amt_str = _format_amt_str(amount)

    params = {}
    if parsed_qr and parsed_qr.get("pa"):
        params["pa"] = parsed_qr["pa"]
        if parsed_qr.get("pn"):
            params["pn"] = parsed_qr["pn"]
        params["am"] = f"{float(amount):.2f}"
        params["cu"] = "INR"
        tx_note = (note or parsed_qr.get("tn") or "").strip()
        if tx_note:
            params["tn"] = tx_note[:80]
        for extra_k in ("mc", "tr", "orgid", "mode"):
            if parsed_qr.get(extra_k):
                params[extra_k] = parsed_qr[extra_k]

    qs = urlencode(params) if params else ""
    pkg = cfg.get("android_pkg")
    ios_scheme = cfg.get("ios_scheme") or "upi://pay"
    ios_home = cfg.get("ios_home") or "upi://"

    if qs:
        generic_upi = f"upi://pay?{qs}"
        ios_url = f"{ios_scheme}?{qs}"
        if pkg:
            android_url = f"intent://pay?{qs}#Intent;scheme=upi;package={pkg};end"
        else:
            android_url = generic_upi
    else:
        generic_upi = "upi://pay"
        ios_url = ios_home
        if pkg:
            android_url = f"intent://#Intent;package={pkg};end"
        else:
            android_url = generic_upi

    return {
        "app_label": cfg.get("label", app_name),
        "ios_url": ios_url,
        "android_url": android_url,
        "generic_upi_url": generic_upi,
        "has_pa": bool(qs),
        "amt_copy": amt_str,
    }


def render_qr_scanner_widget(
    target_input_key: str,
    button_label: str = "Press to Scan QR",
    auto_open: bool = False,
):
    """
    Cross-platform (iOS Safari PWA + Android Chrome) live QR scanner + native photo fallback.
    Fixes dense UPI QR detection via:
    - Multi-CDN jsQR loader (jsDelivr -> cdnjs -> unpkg) + local iframe fallback + native BarcodeDetector
    - HD rear camera constraints + continuous autofocus
    - Dual-pass high-res center reticle crop (900px) & full-frame alternating scan
    """
    key_json = json.dumps(target_input_key)
    lbl_json = json.dumps(button_label)
    auto_json = json.dumps(bool(auto_open))

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8" />
        <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js" async></script>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            html, body {{
                background: transparent;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                overflow: hidden;
            }}
            .wf-scan-btn {{
                width: 100%;
                height: 52px;
                border-radius: 14px;
                border: 1px solid rgba(79, 134, 247, 0.55);
                background: linear-gradient(135deg, #4F86F7 0%, #3B74EB 100%);
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                box-shadow: 0 4px 16px rgba(79, 134, 247, 0.35);
                -webkit-tap-highlight-color: transparent;
                transition: transform 90ms ease, opacity 140ms ease;
            }}
            .wf-scan-btn:active {{
                transform: scale(0.98);
                opacity: 0.92;
            }}
        </style>
        </head>
        <body>
        <button id="wfScanTrigger" type="button" class="wf-scan-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                <path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                <rect x="7" y="7" width="4" height="4" rx="0.5"/><rect x="13" y="7" width="4" height="4" rx="0.5"/>
                <rect x="7" y="13" width="4" height="4" rx="0.5"/><path d="M13 13h4v4h-4z"/>
            </svg>
            <span id="wfScanBtnLabel"></span>
        </button>

        <script>
        (function() {{
            const TARGET_KEY = {key_json};
            const BTN_LABEL = {lbl_json};
            const AUTO_OPEN = {auto_json};
            document.getElementById('wfScanBtnLabel').textContent = BTN_LABEL;

            const JSQR_URLS = [
                'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js',
                'https://cdnjs.cloudflare.com/ajax/libs/jsQR/1.4.0/jsQR.min.js',
                'https://unpkg.com/jsqr@1.4.0/dist/jsQR.min.js'
            ];

            function getHost() {{
                try {{
                    if (window.parent && window.parent.document) {{
                        return {{ win: window.parent, doc: window.parent.document }};
                    }}
                }} catch (e) {{}}
                return {{ win: window, doc: document }};
            }}

            function loadScript(targetDoc, url, id) {{
                return new Promise((resolve) => {{
                    const targetWin = targetDoc.defaultView || window;
                    if (typeof targetWin.jsQR === 'function') return resolve(targetWin.jsQR);
                    const sc = targetDoc.createElement('script');
                    if (id) sc.id = id;
                    sc.src = url;
                    sc.async = true;
                    const timer = setTimeout(() => resolve(targetWin.jsQR || null), 3500);
                    sc.onload = () => {{ clearTimeout(timer); resolve(targetWin.jsQR || null); }};
                    sc.onerror = () => {{ clearTimeout(timer); resolve(null); }};
                    targetDoc.head.appendChild(sc);
                }});
            }}

            async function getJsQR(hostDoc) {{
                const hostWin = hostDoc.defaultView || window.parent || window;
                if (typeof hostWin.jsQR === 'function') return hostWin.jsQR;
                if (typeof window.jsQR === 'function') return window.jsQR;

                for (let i = 0; i < JSQR_URLS.length; i++) {{
                    const fn = await loadScript(hostDoc, JSQR_URLS[i], 'wf-jsqr-host-' + i);
                    if (typeof fn === 'function') return fn;
                    const fnLocal = await loadScript(document, JSQR_URLS[i], 'wf-jsqr-local-' + i);
                    if (typeof fnLocal === 'function') return fnLocal;
                }}
                return hostWin.jsQR || window.jsQR || null;
            }}

            // Warm up decoder right away
            try {{
                const h = getHost();
                getJsQR(h.doc);
            }} catch (e) {{}}

            function syncToStreamlitInput(decodedText) {{
                const {{ win, doc }} = getHost();
                const container = doc.querySelector('.st-key-' + TARGET_KEY);
                const inp = container ? container.querySelector('input') : null;
                if (!inp) return false;
                const proto = (inp.ownerDocument.defaultView || win).HTMLInputElement.prototype;
                const desc = Object.getOwnPropertyDescriptor(proto, 'value');
                if (desc && desc.set) {{
                    desc.set.call(inp, decodedText);
                }} else {{
                    inp.value = decodedText;
                }}
                inp.focus();
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
                inp.dispatchEvent(new KeyboardEvent('keydown', {{
                    key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true
                }}));
                setTimeout(() => {{
                    try {{ inp.blur(); }} catch (e) {{}}
                }}, 80);
                return true;
            }}

            function openScannerOverlay() {{
                const {{ win, doc }} = getHost();
                const prev = doc.getElementById('wf-qr-overlay');
                if (prev) prev.remove();

                const overlay = doc.createElement('div');
                overlay.id = 'wf-qr-overlay';
                overlay.style.cssText = [
                    'position:fixed', 'inset:0', 'z-index:999999',
                    'background:rgba(9,13,22,0.98)',
                    'display:flex', 'flex-direction:column', 'align-items:center', 'justify-content:space-between',
                    'padding:calc(18px + env(safe-area-inset-top, 0px)) 16px calc(24px + env(safe-area-inset-bottom, 0px)) 16px',
                    'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif',
                    'color:#F3F5F8'
                ].join(';');

                overlay.innerHTML = `
                    <div style="width:100%;max-width:440px;display:flex;align-items:center;justify-content:space-between;">
                        <div>
                            <div style="font-size:17px;font-weight:700;color:#F3F5F8;">Scan UPI QR</div>
                            <div id="wf-qr-sub" style="font-size:12px;color:#9CA6B8;margin-top:2px;">Hold steady inside the frame</div>
                        </div>
                        <button id="wf-qr-close" type="button" style="
                            height:38px;padding:0 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.16);
                            background:#182132;color:#F3F5F8;font-size:13px;font-weight:600;cursor:pointer;">
                            Close
                        </button>
                    </div>
                    <div style="position:relative;width:100%;max-width:360px;aspect-ratio:1/1;border-radius:18px;overflow:hidden;
                                background:#111724;border:1px solid rgba(255,255,255,0.16);display:flex;align-items:center;justify-content:center;">
                        <video id="wf-qr-video" playsinline webkit-playsinline muted autoplay style="width:100%;height:100%;object-fit:cover;display:none;"></video>
                        <div style="position:absolute;inset:14%;border:2px solid rgba(79,134,247,0.9);border-radius:14px;pointer-events:none;box-shadow:0 0 0 999px rgba(9,13,22,0.36);"></div>
                        <div id="wf-qr-status" style="position:relative;z-index:2;padding:16px;text-align:center;font-size:13px;color:#9CA6B8;">
                            Starting camera...
                        </div>
                    </div>
                    <div style="width:100%;max-width:360px;display:flex;flex-direction:column;gap:10px;">
                        <label style="width:100%;height:46px;border-radius:12px;background:#182132;border:1px solid rgba(255,255,255,0.16);
                                      color:#F3F5F8;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;">
                            <span>Snap Photo / Upload QR Image</span>
                            <input id="wf-qr-file" type="file" accept="image/*" capture="environment" style="display:none;" />
                        </label>
                    </div>
                `;
                doc.body.appendChild(overlay);

                let stream = null;
                let rafId = null;
                let closed = false;
                const canvas = doc.createElement('canvas');
                const ctx = canvas.getContext('2d', {{ willReadFrequently: true }});
                const videoEl = overlay.querySelector('#wf-qr-video');
                videoEl.muted = true;
                videoEl.playsInline = true;
                const statusEl = overlay.querySelector('#wf-qr-status');
                const subEl = overlay.querySelector('#wf-qr-sub');
                const fileInput = overlay.querySelector('#wf-qr-file');

                function cleanup() {{
                    closed = true;
                    if (rafId) cancelAnimationFrame(rafId);
                    if (stream) {{
                        try {{ stream.getTracks().forEach(t => t.stop()); }} catch (e) {{}}
                    }}
                    overlay.remove();
                }}

                overlay.querySelector('#wf-qr-close').addEventListener('click', cleanup);

                function handleDecoded(rawText) {{
                    if (!rawText || closed) return;
                    try {{ if (win.navigator && win.navigator.vibrate) win.navigator.vibrate(60); }} catch (e) {{}}
                    cleanup();
                    syncToStreamlitInput(rawText);
                }}

                async function decodeCurrentCanvas(jsQRfn, barcodeDetector) {{
                    if (barcodeDetector) {{
                        try {{
                            const codes = await barcodeDetector.detect(canvas);
                            if (codes && codes.length && codes[0].rawValue) {{
                                return codes[0].rawValue;
                            }}
                        }} catch (e) {{}}
                    }}
                    if (typeof jsQRfn === 'function' && canvas.width > 0 && canvas.height > 0) {{
                        try {{
                            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                            const code = jsQRfn(imgData.data, imgData.width, imgData.height, {{ inversionAttempts: 'attemptBoth' }});
                            if (code && code.data) return code.data;
                        }} catch (e) {{}}
                    }}
                    return null;
                }}

                function makeBarcodeDetector() {{
                    try {{
                        const BD = win.BarcodeDetector || window.BarcodeDetector;
                        if (BD) return new BD({{ formats: ['qr_code'] }});
                    }} catch (e) {{}}
                    return null;
                }}

                fileInput.addEventListener('change', async (ev) => {{
                    const file = ev.target.files && ev.target.files[0];
                    if (!file) return;
                    statusEl.style.display = 'block';
                    statusEl.textContent = 'Reading QR from photo...';
                    const jsQRfn = await getJsQR(doc);
                    const detector = makeBarcodeDetector();
                    if (!jsQRfn && !detector) {{
                        statusEl.textContent = 'QR decoder unavailable offline. Please check internet connection or type UPI ID manually.';
                        return;
                    }}
                    const img = new Image();
                    const url = URL.createObjectURL(file);
                    img.onload = async () => {{
                        for (const maxDim of [1200, 800]) {{
                            const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
                            canvas.width = Math.max(1, Math.round(img.width * scale));
                            canvas.height = Math.max(1, Math.round(img.height * scale));
                            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                            const res = await decodeCurrentCanvas(jsQRfn, detector);
                            if (res) {{
                                URL.revokeObjectURL(url);
                                handleDecoded(res);
                                return;
                            }}
                        }}
                        URL.revokeObjectURL(url);
                        statusEl.textContent = 'No QR code detected in that photo. Move closer or try again.';
                    }};
                    img.onerror = () => {{
                        URL.revokeObjectURL(url);
                        statusEl.textContent = 'Could not load image.';
                    }};
                    img.src = url;
                }});

                (async () => {{
                    const jsQRPromise = getJsQR(doc);
                    const detector = makeBarcodeDetector();
                    if (!win.navigator || !win.navigator.mediaDevices || !win.navigator.mediaDevices.getUserMedia) {{
                        statusEl.textContent = 'Live camera unavailable here. Tap "Snap Photo / Upload QR Image" below.';
                        return;
                    }}
                    try {{
                        stream = await win.navigator.mediaDevices.getUserMedia({{
                            video: {{
                                facingMode: {{ ideal: 'environment' }},
                                width: {{ ideal: 1920 }},
                                height: {{ ideal: 1080 }}
                            }},
                            audio: false
                        }});
                        if (closed) {{
                            stream.getTracks().forEach(t => t.stop());
                            return;
                        }}

                        // Hint continuous autofocus if supported on rear camera
                        try {{
                            const track = stream.getVideoTracks()[0];
                            const caps = track && track.getCapabilities ? track.getCapabilities() : null;
                            if (caps && caps.focusMode && caps.focusMode.includes('continuous')) {{
                                await track.applyConstraints({{ advanced: [{{ focusMode: 'continuous' }}] }});
                            }}
                        }} catch (e) {{}}

                        videoEl.srcObject = stream;
                        await videoEl.play();
                        videoEl.style.display = 'block';
                        statusEl.style.display = 'none';

                        const jsQRfn = await jsQRPromise;
                        if (!jsQRfn && !detector) {{
                            subEl.textContent = 'QR library could not load — use Snap Photo below or check internet';
                            return;
                        }}
                        subEl.textContent = 'Scanning active · Align QR inside blue square';

                        let lastScan = 0;
                        let frameCount = 0;
                        async function tick(ts) {{
                            if (closed) return;
                            if (ts - lastScan > 110 && videoEl.readyState >= 2) {{
                                lastScan = ts;
                                frameCount++;
                                const vw = videoEl.videoWidth;
                                const vh = videoEl.videoHeight;
                                if (vw > 0 && vh > 0) {{
                                    // Alternate high-res center reticle crop (75% min dim) and full-frame scan
                                    if (frameCount % 2 === 1) {{
                                        const cropSize = Math.round(Math.min(vw, vh) * 0.78);
                                        const sx = Math.round((vw - cropSize) / 2);
                                        const sy = Math.round((vh - cropSize) / 2);
                                        const outSize = Math.min(900, cropSize);
                                        canvas.width = outSize;
                                        canvas.height = outSize;
                                        ctx.drawImage(videoEl, sx, sy, cropSize, cropSize, 0, 0, outSize, outSize);
                                    }} else {{
                                        const scale = Math.min(1, 960 / Math.max(vw, vh));
                                        canvas.width = Math.round(vw * scale);
                                        canvas.height = Math.round(vh * scale);
                                        ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                                    }}
                                    const res = await decodeCurrentCanvas(jsQRfn, detector);
                                    if (res) {{
                                        handleDecoded(res);
                                        return;
                                    }}
                                }}
                            }}
                            rafId = win.requestAnimationFrame(tick);
                        }}
                        rafId = win.requestAnimationFrame(tick);
                    }} catch (err) {{
                        statusEl.textContent = 'Camera permission blocked or unavailable. Use "Snap Photo / Upload QR Image" below.';
                    }}
                }})();
            }}

            document.getElementById('wfScanTrigger').addEventListener('click', openScannerOverlay);
            if (AUTO_OPEN) {{
                setTimeout(openScannerOverlay, 120);
            }}
        }})();
        </script>
        </body>
        </html>
        """,
        height=58,
    )


def render_pay_handoff_banner(app_name: str, amount: float, parsed_qr: dict | None, note: str = "", paid_by_cc: bool = False):
    """
    Renders the post-log UPI handoff card:
    - Copies the amount to clipboard automatically
    - Detects iOS vs Android in browser to choose the best URI (ios_url vs Android intent://)
    - Attempts automatic redirect on Android, and provides an immediate 1-tap launch pill for iOS Safari PWA
    - Shows an optional fallback System UPI link if the chosen app rejects parameters
    """
    urls = build_upi_urls(app_name, parsed_qr, amount, note)
    sym = st.session_state.get("sym", "₹")
    amt_display = f"{sym}{float(amount):,.2f}"
    merchant_label = ""
    if parsed_qr and parsed_qr.get("pa"):
        pn = parsed_qr.get("pn") or parsed_qr["pa"]
        merchant_label = f"{pn} ({parsed_qr['pa']})" if parsed_qr.get("pn") else parsed_qr["pa"]
    cc_badge = " · Paid by CC" if paid_by_cc else ""

    ios_url_json = json.dumps(urls["ios_url"])
    android_url_json = json.dumps(urls["android_url"])
    generic_url_json = json.dumps(urls["generic_upi_url"])
    amt_copy_json = json.dumps(urls["amt_copy"])
    app_label_esc = html.escape(urls["app_label"])
    merchant_esc = html.escape(merchant_label)
    amt_esc = html.escape(amt_display)
    cc_esc = html.escape(cc_badge)

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8" />
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            html, body {{
                background: transparent;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #F3F5F8;
            }}
            .wf-pay-card {{
                background: linear-gradient(180deg, rgba(52, 211, 153, 0.12) 0%, #111724 100%);
                border: 1px solid rgba(52, 211, 153, 0.36);
                border-radius: 14px;
                padding: 13px 14px;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .wf-pay-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 8px;
            }}
            .wf-pay-title {{
                font-size: 13px;
                font-weight: 600;
                color: #34D399;
            }}
            .wf-pay-sub {{
                font-size: 12px;
                color: #9CA6B8;
                margin-top: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 290px;
            }}
            .wf-pay-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                width: 100%;
                height: 44px;
                border-radius: 12px;
                background: #4F86F7;
                color: #FFFFFF;
                text-decoration: none;
                font-size: 14px;
                font-weight: 600;
                box-shadow: 0 2px 10px rgba(79, 134, 247, 0.32);
                -webkit-tap-highlight-color: transparent;
            }}
            .wf-pay-foot {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 11px;
                color: #9CA6B8;
            }}
            .wf-upi-alt {{
                color: #93C5FD;
                text-decoration: none;
                font-weight: 500;
            }}
        </style>
        </head>
        <body>
        <div class="wf-pay-card">
            <div class="wf-pay-top">
                <div style="min-width:0;">
                    <div class="wf-pay-title">Logged {amt_esc}{cc_esc}</div>
                    <div class="wf-pay-sub">{merchant_esc if merchant_esc else 'Ready to pay · ' + amt_esc + ' copied to clipboard'}</div>
                </div>
            </div>
            <a id="wfPayLaunchBtn" href="#" target="_top" class="wf-pay-btn">
                Open {app_label_esc} ({amt_esc}) →
            </a>
            <div class="wf-pay-foot">
                <span id="wfCopyStatus">Amount {html.escape(urls['amt_copy'])} copied</span>
                <a id="wfGenericUpiBtn" href="#" target="_top" class="wf-upi-alt">Open System UPI</a>
            </div>
        </div>
        <script>
        (function() {{
            const iosUrl = {ios_url_json};
            const androidUrl = {android_url_json};
            const genericUrl = {generic_url_json};
            const amtCopy = {amt_copy_json};

            const ua = navigator.userAgent || '';
            const isAndroid = /Android/i.test(ua);
            const targetUrl = isAndroid ? androidUrl : iosUrl;

            const launchBtn = document.getElementById('wfPayLaunchBtn');
            const altBtn = document.getElementById('wfGenericUpiBtn');
            launchBtn.setAttribute('href', targetUrl);
            altBtn.setAttribute('href', genericUrl);

            function copyAmt() {{
                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(amtCopy);
                    }}
                }} catch (e) {{}}
            }}
            copyAmt();

            launchBtn.addEventListener('click', function() {{
                copyAmt();
            }});

            if (isAndroid) {{
                setTimeout(function() {{
                    try {{
                        window.top.location.href = targetUrl;
                    }} catch (e) {{
                        window.location.href = targetUrl;
                    }}
                }}, 180);
            }}
        }})();
        </script>
        </body>
        </html>
        """,
        height=148,
    )
