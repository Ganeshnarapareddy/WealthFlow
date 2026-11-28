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
        "ios_scheme": "credpay://upi/pay",
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


def _parse_tlvs(payload: str) -> list[tuple[str, str]]:
    """Parse EMVCo Tag-Length-Value (2-char tag, 2-digit length, value) records."""
    items = []
    idx = 0
    n = len(payload)
    while idx + 4 <= n:
        tag = payload[idx : idx + 2]
        len_str = payload[idx + 2 : idx + 4]
        if not len_str.isdigit():
            break
        val_len = int(len_str)
        val_start = idx + 4
        val_end = val_start + val_len
        if val_end > n:
            break
        items.append((tag, payload[val_start:val_end]))
        idx = val_end
    return items


def _parse_emvco_upi_qr(text: str) -> dict | None:
    """Decode BharatQR / EMVCo merchant QR payloads (e.g., SBI/Hitachi '000201...')."""
    tlvs = _parse_tlvs(text)
    if not tlvs:
        return None
    top_map = {t: v for t, v in tlvs}
    if top_map.get("00") != "01":
        return None

    pa = ""
    pn = top_map.get("59", "").strip()
    mc = top_map.get("52", "").strip()
    tr = ""
    tn = ""
    am_val = None

    raw_am = top_map.get("54", "").strip()
    if raw_am:
        try:
            f = float(raw_am)
            if f > 0:
                am_val = f
        except ValueError:
            am_val = None

    for t, val in tlvs:
        if t.isdigit() and 26 <= int(t) <= 51:
            sub = {st_tag: st_val for st_tag, st_val in _parse_tlvs(val)}
            guid = sub.get("00", "").upper()
            cand_pa = sub.get("01", "").strip()
            if (guid == "A000000524" or "@" in cand_pa) and "@" in cand_pa and " " not in cand_pa:
                pa = cand_pa
                break

    if not pa:
        for t, val in tlvs:
            if t.isdigit() and 26 <= int(t) <= 51:
                for _, st_val in _parse_tlvs(val):
                    s = st_val.strip()
                    if "@" in s and " " not in s and not s.lower().startswith("http"):
                        pa = s
                        break
            if pa:
                break

    if not pa:
        return None

    if "62" in top_map:
        add_map = {st_tag: st_val for st_tag, st_val in _parse_tlvs(top_map["62"])}
        tr = (add_map.get("05") or add_map.get("01") or add_map.get("07") or "").strip()
        tn = (add_map.get("08") or "").strip()

    return {
        "pa": pa,
        "pn": pn,
        "am": am_val,
        "tn": tn,
        "mc": mc,
        "tr": tr,
        "orgid": "",
        "mode": "",
    }


def parse_upi_qr(raw_value: str) -> dict | None:
    """
    Parse an NPCI UPI QR URI (upi://pay?pa=...&pn=...), BharatQR/EMVCo TLV ('000201...'),
    or bare UPI ID (name@bank).
    Returns normalized dict with pa, pn, am, tn, mc, tr, orgid, mode, or None if invalid.
    """
    if not raw_value or not isinstance(raw_value, str):
        return None
    text = raw_value.strip()
    if not text:
        return None

    if "://" not in text and "@" in text and " " not in text and "?" not in text and not text.startswith("000201"):
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

    if text.startswith("000201"):
        emv = _parse_emvco_upi_qr(text)
        if emv:
            return emv

    low = text.lower()
    if not (low.startswith("upi://") or low.startswith("upiglobal://") or "pa=" in low):
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
    Cross-platform (iOS Safari PWA + Android Chrome) QR scanner with clean icon controls:
    - Flash icon button & X close icon button in header (no engine debug text)
    - Separate Snap Photo (camera icon) and Upload QR (gallery icon) buttons below viewfinder
    - Dual-engine ZXing (HybridBinarizer + invert) + jsQR + BarcodeDetector
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
        <script src="https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js" async></script>
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
            const ZXING_URLS = [
                'https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js',
                'https://unpkg.com/@zxing/library@0.21.3/umd/index.min.js'
            ];

            function getHost() {{
                try {{
                    if (window.parent && window.parent.document) {{
                        return {{ win: window.parent, doc: window.parent.document }};
                    }}
                }} catch (e) {{}}
                return {{ win: window, doc: document }};
            }}

            function loadLib(targetDoc, urls, globalName, idPrefix) {{
                return new Promise(async (resolve) => {{
                    const targetWin = targetDoc.defaultView || window;
                    if (targetWin[globalName]) return resolve(targetWin[globalName]);
                    if (window[globalName]) return resolve(window[globalName]);

                    for (let i = 0; i < urls.length; i++) {{
                        const res = await new Promise((r) => {{
                            const sc = targetDoc.createElement('script');
                            sc.id = idPrefix + '-' + i;
                            sc.src = urls[i];
                            sc.async = true;
                            const t = setTimeout(() => r(targetWin[globalName] || null), 3500);
                            sc.onload = () => {{ clearTimeout(t); r(targetWin[globalName] || null); }};
                            sc.onerror = () => {{ clearTimeout(t); r(null); }};
                            targetDoc.head.appendChild(sc);
                        }});
                        if (res) return resolve(res);
                    }}
                    resolve(targetWin[globalName] || window[globalName] || null);
                }});
            }}

            async function getDecoders(hostDoc) {{
                const hostWin = hostDoc.defaultView || window.parent || window;
                const [jsQRfn, ZXingLib] = await Promise.all([
                    (hostWin.jsQR || window.jsQR)
                        ? Promise.resolve(hostWin.jsQR || window.jsQR)
                        : loadLib(hostDoc, JSQR_URLS, 'jsQR', 'wf-jsqr')
                            .then((fn) => fn || loadLib(document, JSQR_URLS, 'jsQR', 'wf-jsqr-l')),
                    (hostWin.ZXing || window.ZXing)
                        ? Promise.resolve(hostWin.ZXing || window.ZXing)
                        : loadLib(hostDoc, ZXING_URLS, 'ZXing', 'wf-zxing')
                            .then((lib) => lib || loadLib(document, ZXING_URLS, 'ZXing', 'wf-zxing-l')),
                ]);
                let detector = null;
                try {{
                    const BD = hostWin.BarcodeDetector || window.BarcodeDetector;
                    if (BD) detector = new BD({{ formats: ['qr_code'] }});
                }} catch (e) {{}}
                return {{ jsQRfn, ZXingLib, detector }};
            }}

            try {{
                const h = getHost();
                getDecoders(h.doc);
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

            function buildContrastImageData(imgData, invert) {{
                const w = imgData.width;
                const h = imgData.height;
                const src = imgData.data;
                const out = new Uint8ClampedArray(src.length);
                const len = w * h;
                const luma = new Uint8Array(len);
                const hist = new Uint32Array(256);

                for (let i = 0, j = 0; i < len; i++, j += 4) {{
                    const y = (src[j] * 77 + src[j + 1] * 150 + src[j + 2] * 29) >> 8;
                    luma[i] = y;
                    hist[y]++;
                }}
                const lowCut = Math.floor(len * 0.05);
                const highCut = Math.floor(len * 0.08);
                let acc = 0, minV = 0, maxV = 255;
                for (let k = 0; k < 256; k++) {{
                    acc += hist[k];
                    if (acc >= lowCut) {{ minV = k; break; }}
                }}
                acc = 0;
                for (let k = 255; k >= 0; k--) {{
                    acc += hist[k];
                    if (acc >= highCut) {{ maxV = k; break; }}
                }}
                const span = Math.max(16, maxV - minV);
                for (let i = 0, j = 0; i < len; i++, j += 4) {{
                    let v = ((luma[i] - minV) * 255) / span;
                    if (v < 0) v = 0;
                    if (v > 255) v = 255;
                    if (invert) v = 255 - v;
                    out[j] = out[j + 1] = out[j + 2] = v;
                    out[j + 3] = 255;
                }}
                return {{ data: out, width: w, height: h }};
            }}

            function tryZXingCanvas(ZXingLib, zxingReader, zxingHints, canvasEl, imgData) {{
                if (!ZXingLib || !zxingReader) return {{ text: null, err: null }};
                try {{
                    let src = null;
                    if (typeof ZXingLib.HTMLCanvasElementLuminanceSource === 'function') {{
                        src = new ZXingLib.HTMLCanvasElementLuminanceSource(canvasEl);
                    }} else if (typeof ZXingLib.RGBLuminanceSource === 'function') {{
                        const w = imgData.width;
                        const h = imgData.height;
                        const d = imgData.data;
                        const ints = new Int32Array(w * h);
                        for (let i = 0, j = 0; i < ints.length; i++, j += 4) {{
                            ints[i] = (d[j] << 16) | (d[j + 1] << 8) | d[j + 2];
                        }}
                        src = new ZXingLib.RGBLuminanceSource(ints, w, h);
                    }}
                    if (!src) return {{ text: null, err: 'no-src' }};

                    const candidates = [src];
                    if (typeof src.invert === 'function') {{
                        candidates.push(src.invert());
                    }}

                    for (const lum of candidates) {{
                        if (typeof ZXingLib.HybridBinarizer === 'function') {{
                            try {{
                                const bmp = new ZXingLib.BinaryBitmap(new ZXingLib.HybridBinarizer(lum));
                                const res = zxingReader.decode(bmp, zxingHints);
                                if (res && res.getText) return {{ text: res.getText(), err: null }};
                            }} catch (e) {{}}
                        }}
                        if (typeof ZXingLib.GlobalHistogramBinarizer === 'function') {{
                            try {{
                                const bmp2 = new ZXingLib.BinaryBitmap(new ZXingLib.GlobalHistogramBinarizer(lum));
                                const res2 = zxingReader.decode(bmp2, zxingHints);
                                if (res2 && res2.getText) return {{ text: res2.getText(), err: null }};
                            }} catch (e) {{}}
                        }}
                    }}
                    return {{ text: null, err: null }};
                }} catch (e) {{
                    return {{ text: null, err: String(e && e.message ? e.message : e) }};
                }}
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
                    <div style="width:100%;max-width:440px;display:flex;align-items:center;justify-content:space-between;gap:10px;">
                        <div style="min-width:0;">
                            <div style="font-size:18px;font-weight:700;color:#F3F5F8;">Scan UPI QR</div>
                            <div id="wf-qr-err" style="display:none;font-size:12px;color:#F87171;margin-top:2px;"></div>
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                            <button id="wf-qr-torch" type="button" aria-label="Toggle Flash" style="display:none;
                                width:40px;height:40px;border-radius:12px;border:1px solid rgba(255,255,255,0.16);
                                background:#182132;color:#9CA6B8;align-items:center;justify-content:center;cursor:pointer;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                                </svg>
                            </button>
                            <button id="wf-qr-close" type="button" aria-label="Close" style="
                                width:40px;height:40px;border-radius:12px;border:1px solid rgba(255,255,255,0.16);
                                background:#182132;color:#F3F5F8;display:flex;align-items:center;justify-content:center;cursor:pointer;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div style="position:relative;width:100%;max-width:360px;aspect-ratio:1/1;border-radius:18px;overflow:hidden;
                                background:#111724;border:1px solid rgba(255,255,255,0.16);display:flex;align-items:center;justify-content:center;">
                        <video id="wf-qr-video" playsinline webkit-playsinline muted autoplay style="width:100%;height:100%;object-fit:cover;display:none;"></video>
                        <div style="position:absolute;inset:12%;border:2px solid rgba(79,134,247,0.9);border-radius:14px;pointer-events:none;box-shadow:0 0 0 999px rgba(9,13,22,0.34);"></div>
                        <div id="wf-qr-status" style="position:relative;z-index:2;padding:16px;text-align:center;font-size:13px;color:#9CA6B8;">
                            Starting camera...
                        </div>
                    </div>
                    <div style="width:100%;max-width:360px;display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <label style="height:46px;border-radius:12px;background:#182132;border:1px solid rgba(255,255,255,0.16);
                                      color:#F3F5F8;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                                <circle cx="12" cy="13" r="4"></circle>
                            </svg>
                            <span>Snap Photo</span>
                            <input id="wf-qr-snap" type="file" accept="image/*" capture="environment" style="display:none;" />
                        </label>
                        <label style="height:46px;border-radius:12px;background:#182132;border:1px solid rgba(255,255,255,0.16);
                                      color:#F3F5F8;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;cursor:pointer;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                <polyline points="21 15 16 10 5 21"></polyline>
                            </svg>
                            <span>Upload QR</span>
                            <input id="wf-qr-gallery" type="file" accept="image/*" style="display:none;" />
                        </label>
                    </div>
                `;
                doc.body.appendChild(overlay);

                let stream = null;
                let rafId = null;
                let closed = false;
                let torchOn = false;
                const canvas = doc.createElement('canvas');
                const ctx = canvas.getContext('2d', {{ willReadFrequently: true }});
                const videoEl = overlay.querySelector('#wf-qr-video');
                videoEl.muted = true;
                videoEl.playsInline = true;
                const statusEl = overlay.querySelector('#wf-qr-status');
                const errEl = overlay.querySelector('#wf-qr-err');
                const torchBtn = overlay.querySelector('#wf-qr-torch');
                const snapInput = overlay.querySelector('#wf-qr-snap');
                const galleryInput = overlay.querySelector('#wf-qr-gallery');

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

                async function decodeCanvasAllEngines(decoders, zxingReader, zxingHints, useContrast) {{
                    const {{ jsQRfn, ZXingLib, detector }} = decoders;
                    if (detector) {{
                        try {{
                            const codes = await detector.detect(canvas);
                            if (codes && codes.length && codes[0].rawValue) {{
                                return codes[0].rawValue;
                            }}
                        }} catch (e) {{}}
                    }}
                    if (canvas.width <= 0 || canvas.height <= 0) return null;
                    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                    const zx = tryZXingCanvas(ZXingLib, zxingReader, zxingHints, canvas, imgData);
                    if (zx && zx.text) return zx.text;

                    if (typeof jsQRfn === 'function') {{
                        try {{
                            const code = jsQRfn(imgData.data, imgData.width, imgData.height, {{ inversionAttempts: 'attemptBoth' }});
                            if (code && code.data) return code.data;
                        }} catch (e) {{}}

                        if (useContrast) {{
                            for (const inv of [false, true]) {{
                                try {{
                                    const norm = buildContrastImageData(imgData, inv);
                                    const code2 = jsQRfn(norm.data, norm.width, norm.height, {{ inversionAttempts: 'dontInvert' }});
                                    if (code2 && code2.data) return code2.data;
                                }} catch (e) {{}}
                            }}
                        }}
                    }}
                    return null;
                }}

                function makeZXingInstance(ZXingLib) {{
                    if (!ZXingLib || !ZXingLib.QRCodeReader) return {{ reader: null, hints: null }};
                    try {{
                        const reader = new ZXingLib.QRCodeReader();
                        const hints = new Map();
                        if (ZXingLib.DecodeHintType && ZXingLib.DecodeHintType.TRY_HARDER) {{
                            hints.set(ZXingLib.DecodeHintType.TRY_HARDER, true);
                        }}
                        return {{ reader, hints }};
                    }} catch (e) {{
                        return {{ reader: null, hints: null }};
                    }}
                }}

                async function analyzeImageFile(file) {{
                    if (!file) return;
                    statusEl.style.display = 'block';
                    statusEl.textContent = 'Reading QR...';
                    const decoders = await getDecoders(doc);
                    const {{ reader: zxingReader, hints: zxingHints }} = makeZXingInstance(decoders.ZXingLib);

                    const img = new Image();
                    const url = URL.createObjectURL(file);
                    img.onload = async () => {{
                        const iw = img.naturalWidth || img.width;
                        const ih = img.naturalHeight || img.height;
                        const minDim = Math.min(iw, ih);

                        const attempts = [
                            {{ sx: 0, sy: 0, sw: iw, sh: ih, maxOut: 1400 }},
                            {{ sx: 0, sy: 0, sw: iw, sh: ih, maxOut: 800 }},
                            {{
                                sx: Math.round((iw - minDim * 0.72) / 2),
                                sy: Math.round((ih - minDim * 0.72) / 2),
                                sw: Math.round(minDim * 0.72),
                                sh: Math.round(minDim * 0.72),
                                maxOut: 1000
                            }},
                            {{
                                sx: Math.round((iw - minDim * 0.48) / 2),
                                sy: Math.round((ih - minDim * 0.48) / 2),
                                sw: Math.round(minDim * 0.48),
                                sh: Math.round(minDim * 0.48),
                                maxOut: 900
                            }},
                        ];

                        for (const a of attempts) {{
                            if (a.sw <= 0 || a.sh <= 0) continue;
                            const scale = Math.min(1, a.maxOut / Math.max(a.sw, a.sh));
                            canvas.width = Math.max(1, Math.round(a.sw * scale));
                            canvas.height = Math.max(1, Math.round(a.sh * scale));
                            ctx.drawImage(img, a.sx, a.sy, a.sw, a.sh, 0, 0, canvas.width, canvas.height);
                            const res = await decodeCanvasAllEngines(decoders, zxingReader, zxingHints, true);
                            if (res) {{
                                URL.revokeObjectURL(url);
                                handleDecoded(res);
                                return;
                            }}
                        }}

                        URL.revokeObjectURL(url);
                        statusEl.textContent = 'No QR code detected. Try again or enter UPI ID manually.';
                    }};
                    img.onerror = () => {{
                        URL.revokeObjectURL(url);
                        statusEl.textContent = 'Could not load image.';
                    }};
                    img.src = url;
                }}

                snapInput.addEventListener('change', (ev) => analyzeImageFile(ev.target.files && ev.target.files[0]));
                galleryInput.addEventListener('change', (ev) => analyzeImageFile(ev.target.files && ev.target.files[0]));

                (async () => {{
                    const decodersPromise = getDecoders(doc);
                    if (!win.navigator || !win.navigator.mediaDevices || !win.navigator.mediaDevices.getUserMedia) {{
                        statusEl.textContent = 'Live camera unavailable. Use Snap Photo or Upload QR below.';
                        return;
                    }}
                    try {{
                        try {{
                            stream = await win.navigator.mediaDevices.getUserMedia({{
                                video: {{
                                    facingMode: {{ ideal: 'environment' }},
                                    width: {{ ideal: 1920 }},
                                    height: {{ ideal: 1080 }}
                                }},
                                audio: false
                            }});
                        }} catch (e1) {{
                            stream = await win.navigator.mediaDevices.getUserMedia({{
                                video: {{ facingMode: 'environment' }},
                                audio: false
                            }});
                        }}
                        if (closed) {{
                            stream.getTracks().forEach(t => t.stop());
                            return;
                        }}

                        const track = stream.getVideoTracks()[0];
                        try {{
                            const caps = track && track.getCapabilities ? track.getCapabilities() : null;
                            if (caps) {{
                                if (caps.focusMode && caps.focusMode.includes('continuous')) {{
                                    await track.applyConstraints({{ advanced: [{{ focusMode: 'continuous' }}] }});
                                }}
                                if (caps.torch) {{
                                    torchBtn.style.display = 'flex';
                                    torchBtn.addEventListener('click', async () => {{
                                        torchOn = !torchOn;
                                        try {{
                                            await track.applyConstraints({{ advanced: [{{ torch: torchOn }}] }});
                                            torchBtn.style.color = torchOn ? '#FBBF24' : '#9CA6B8';
                                            torchBtn.style.borderColor = torchOn ? 'rgba(251, 191, 36, 0.55)' : 'rgba(255,255,255,0.16)';
                                            torchBtn.style.background = torchOn ? 'rgba(251, 191, 36, 0.16)' : '#182132';
                                        }} catch (e) {{}}
                                    }});
                                }}
                            }}
                        }} catch (e) {{}}

                        videoEl.srcObject = stream;
                        await videoEl.play();
                        videoEl.style.display = 'block';
                        statusEl.style.display = 'none';

                        const decoders = await decodersPromise;
                        const {{ reader: zxingReader, hints: zxingHints }} = makeZXingInstance(decoders.ZXingLib);

                        if (!decoders.detector && !zxingReader && !decoders.jsQRfn) {{
                            errEl.textContent = 'QR engine blocked offline — enter UPI ID manually';
                            errEl.style.display = 'block';
                            return;
                        }}

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
                                    const mode = frameCount % 3;
                                    if (mode === 0) {{
                                        const cropSize = Math.round(Math.min(vw, vh) * 0.76);
                                        const sx = Math.round((vw - cropSize) / 2);
                                        const sy = Math.round((vh - cropSize) / 2);
                                        const out = Math.min(960, cropSize);
                                        canvas.width = out;
                                        canvas.height = out;
                                        ctx.drawImage(videoEl, sx, sy, cropSize, cropSize, 0, 0, out, out);
                                    }} else if (mode === 1) {{
                                        const cropSize = Math.round(Math.min(vw, vh) * 0.52);
                                        const sx = Math.round((vw - cropSize) / 2);
                                        const sy = Math.round((vh - cropSize) / 2);
                                        const out = Math.min(840, cropSize);
                                        canvas.width = out;
                                        canvas.height = out;
                                        ctx.drawImage(videoEl, sx, sy, cropSize, cropSize, 0, 0, out, out);
                                    }} else {{
                                        const scale = Math.min(1, 1024 / Math.max(vw, vh));
                                        canvas.width = Math.round(vw * scale);
                                        canvas.height = Math.round(vh * scale);
                                        ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                                    }}
                                    const res = await decodeCanvasAllEngines(
                                        decoders, zxingReader, zxingHints, true
                                    );
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
                        statusEl.textContent = 'Camera unavailable. Use Snap Photo or Upload QR below.';
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


def render_pay_handoff_banner(
    app_name: str,
    amount: float,
    parsed_qr: dict | None,
    note: str = "",
    paid_by_cc: bool = False,
    home_btn_key: str = "m_sp_go_home",
):
    """
    Renders the post-log UPI handoff card:
    - Copies the amount to clipboard automatically
    - Launches the chosen UPI app (CRED / Paytm / GPay / PhonePe / BHIM)
    - Automatically navigates WealthFlow back to Home once the UPI app opens (or on return)
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
    home_key_json = json.dumps(home_btn_key)
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
            const homeBtnKey = {home_key_json};

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

            let launched = false;
            let homeTriggered = false;
            function triggerReturnHome() {{
                if (homeTriggered) return;
                homeTriggered = true;
                try {{
                    const doc = window.parent ? window.parent.document : document;
                    const homeWrap = doc.querySelector('.st-key-' + homeBtnKey);
                    const homeBtn = homeWrap ? homeWrap.querySelector('button') : null;
                    if (homeBtn) {{
                        homeBtn.click();
                        return;
                    }}
                    const dockWrap = doc.querySelector('.st-key-m_dock_home');
                    const dockBtn = dockWrap ? dockWrap.querySelector('button') : null;
                    if (dockBtn) dockBtn.click();
                }} catch (e) {{}}
            }}

            function scheduleHomeReturn() {{
                launched = true;
                setTimeout(triggerReturnHome, 550);
            }}

            try {{
                const pDoc = window.parent ? window.parent.document : document;
                const pWin = window.parent || window;
                pDoc.addEventListener('visibilitychange', function() {{
                    if (launched && !pDoc.hidden) triggerReturnHome();
                }});
                pWin.addEventListener('focus', function() {{
                    if (launched) triggerReturnHome();
                }});
            }} catch (e) {{}}

            launchBtn.addEventListener('click', function() {{
                copyAmt();
                scheduleHomeReturn();
            }});
            altBtn.addEventListener('click', function() {{
                copyAmt();
                scheduleHomeReturn();
            }});

            if (isAndroid) {{
                setTimeout(function() {{
                    scheduleHomeReturn();
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
