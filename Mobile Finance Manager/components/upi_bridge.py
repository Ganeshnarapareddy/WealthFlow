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


def render_qr_scanner_widget(target_input_key: str, button_label: str = "Scan Merchant QR"):
    """
    Renders a cross-platform (iOS Safari PWA + Android Chrome) QR scanner launcher.
    Mounts a full-screen camera overlay inside window.parent.document (live camera + photo fallback)
    and syncs decoded UPI URI back to Streamlit's keyed text_input via React's native value setter.
    """
    key_json = json.dumps(target_input_key)
    lbl_json = json.dumps(button_label)

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
                overflow: hidden;
            }}
            .wf-scan-btn {{
                width: 100%;
                height: 44px;
                border-radius: 12px;
                border: 1px solid rgba(79, 134, 247, 0.45);
                background: rgba(79, 134, 247, 0.14);
                color: #93C5FD;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                -webkit-tap-highlight-color: transparent;
                transition: background 140ms ease, transform 90ms ease;
            }}
            .wf-scan-btn:active {{
                transform: scale(0.98);
                background: rgba(79, 134, 247, 0.24);
            }}
        </style>
        </head>
        <body>
        <button id="wfScanTrigger" type="button" class="wf-scan-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
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
            document.getElementById('wfScanBtnLabel').textContent = BTN_LABEL;

            function getHost() {{
                try {{
                    if (window.parent && window.parent.document) {{
                        return {{ win: window.parent, doc: window.parent.document }};
                    }}
                }} catch (e) {{}}
                return {{ win: window, doc: document }};
            }}

            function ensureJsQR(hostDoc) {{
                return new Promise((resolve) => {{
                    const hostWin = hostDoc.defaultView || window.parent || window;
                    if (typeof hostWin.jsQR === 'function') return resolve(hostWin.jsQR);
                    let existing = hostDoc.getElementById('wf-jsqr-lib');
                    if (existing) {{
                        existing.addEventListener('load', () => resolve(hostWin.jsQR || null));
                        setTimeout(() => resolve(hostWin.jsQR || null), 2500);
                        return;
                    }}
                    const sc = hostDoc.createElement('script');
                    sc.id = 'wf-jsqr-lib';
                    sc.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
                    sc.async = true;
                    sc.onload = () => resolve(hostWin.jsQR || null);
                    sc.onerror = () => resolve(null);
                    hostDoc.head.appendChild(sc);
                }});
            }}

            // Preload decoder in background so modal opens instantly
            try {{
                const h = getHost();
                ensureJsQR(h.doc);
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
                }}, 60);
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
                    'background:rgba(9,13,22,0.97)',
                    'display:flex', 'flex-direction:column', 'align-items:center', 'justify-content:space-between',
                    'padding:calc(18px + env(safe-area-inset-top, 0px)) 16px calc(24px + env(safe-area-inset-bottom, 0px)) 16px',
                    'font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif',
                    'color:#F3F5F8'
                ].join(';');

                overlay.innerHTML = `
                    <div style="width:100%;max-width:440px;display:flex;align-items:center;justify-content:space-between;">
                        <div>
                            <div style="font-size:17px;font-weight:700;color:#F3F5F8;">Scan UPI QR</div>
                            <div style="font-size:12px;color:#9CA6B8;margin-top:2px;">Point camera at merchant QR code</div>
                        </div>
                        <button id="wf-qr-close" type="button" style="
                            height:38px;padding:0 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.16);
                            background:#182132;color:#F3F5F8;font-size:13px;font-weight:600;cursor:pointer;">
                            Close
                        </button>
                    </div>
                    <div style="position:relative;width:100%;max-width:360px;aspect-ratio:1/1;border-radius:18px;overflow:hidden;
                                background:#111724;border:1px solid rgba(255,255,255,0.16);display:flex;align-items:center;justify-content:center;">
                        <video id="wf-qr-video" playsinline muted autoplay style="width:100%;height:100%;object-fit:cover;display:none;"></video>
                        <div id="wf-qr-reticle" style="position:absolute;inset:14%;border:2px solid rgba(79,134,247,0.85);border-radius:14px;pointer-events:none;box-shadow:0 0 0 999px rgba(9,13,22,0.38);"></div>
                        <div id="wf-qr-status" style="position:relative;z-index:2;padding:16px;text-align:center;font-size:13px;color:#9CA6B8;">
                            Starting camera...
                        </div>
                    </div>
                    <div style="width:100%;max-width:360px;display:flex;flex-direction:column;gap:10px;">
                        <label style="width:100%;height:44px;border-radius:12px;background:#182132;border:1px solid rgba(255,255,255,0.16);
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
                const statusEl = overlay.querySelector('#wf-qr-status');
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

                async function decodeCanvas(jsQRfn, barcodeDetector) {{
                    if (barcodeDetector) {{
                        try {{
                            const codes = await barcodeDetector.detect(canvas);
                            if (codes && codes.length && codes[0].rawValue) {{
                                return codes[0].rawValue;
                            }}
                        }} catch (e) {{}}
                    }}
                    if (jsQRfn && canvas.width > 0 && canvas.height > 0) {{
                        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const code = jsQRfn(imgData.data, imgData.width, imgData.height, {{ inversionAttempts: 'attemptBoth' }});
                        if (code && code.data) return code.data;
                    }}
                    return null;
                }}

                // Photo / Gallery QR fallback (works even if getUserMedia is restricted)
                fileInput.addEventListener('change', async (ev) => {{
                    const file = ev.target.files && ev.target.files[0];
                    if (!file) return;
                    statusEl.style.display = 'block';
                    statusEl.textContent = 'Reading QR from photo...';
                    const jsQRfn = await ensureJsQR(doc);
                    const detector = ('BarcodeDetector' in win) ? new win.BarcodeDetector({{ formats: ['qr_code'] }}) : null;
                    const img = new Image();
                    const url = URL.createObjectURL(file);
                    img.onload = async () => {{
                        const maxDim = 1024;
                        const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
                        canvas.width = Math.max(1, Math.round(img.width * scale));
                        canvas.height = Math.max(1, Math.round(img.height * scale));
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        URL.revokeObjectURL(url);
                        const res = await decodeCanvas(jsQRfn, detector);
                        if (res) {{
                            handleDecoded(res);
                        }} else {{
                            statusEl.textContent = 'No QR code detected in that photo. Try another shot or enter UPI ID manually.';
                        }}
                    }};
                    img.onerror = () => {{
                        URL.revokeObjectURL(url);
                        statusEl.textContent = 'Could not load image.';
                    }};
                    img.src = url;
                }});

                // Live camera stream
                (async () => {{
                    const jsQRfn = await ensureJsQR(doc);
                    const detector = ('BarcodeDetector' in win) ? new win.BarcodeDetector({{ formats: ['qr_code'] }}) : null;
                    if (!win.navigator || !win.navigator.mediaDevices || !win.navigator.mediaDevices.getUserMedia) {{
                        statusEl.textContent = 'Live camera unavailable here. Tap "Snap Photo / Upload QR Image" below.';
                        return;
                    }}
                    try {{
                        stream = await win.navigator.mediaDevices.getUserMedia({{
                            video: {{ facingMode: {{ ideal: 'environment' }} }},
                            audio: false
                        }});
                        if (closed) {{
                            stream.getTracks().forEach(t => t.stop());
                            return;
                        }}
                        videoEl.srcObject = stream;
                        await videoEl.play();
                        videoEl.style.display = 'block';
                        statusEl.style.display = 'none';

                        let lastScan = 0;
                        async function tick(ts) {{
                            if (closed) return;
                            if (ts - lastScan > 140 && videoEl.readyState >= 2) {{
                                lastScan = ts;
                                const vw = videoEl.videoWidth;
                                const vh = videoEl.videoHeight;
                                if (vw > 0 && vh > 0) {{
                                    const maxW = 640;
                                    const scale = Math.min(1, maxW / vw);
                                    canvas.width = Math.round(vw * scale);
                                    canvas.height = Math.round(vh * scale);
                                    ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                                    const res = await decodeCanvas(jsQRfn, detector);
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
                        statusEl.textContent = 'Camera permission denied or unavailable. Use "Snap Photo / Upload QR Image" below.';
                    }}
                }})();
            }}

            document.getElementById('wfScanTrigger').addEventListener('click', openScannerOverlay);
        }})();
        </script>
        </body>
        </html>
        """,
        height=48,
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

            // On Android, browsers allow direct intent launch; iOS uses the explicit tap link above
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
