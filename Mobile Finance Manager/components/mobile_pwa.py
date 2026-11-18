import json
import streamlit.components.v1 as components


def mount_ios_pwa_bridge(logo_b64: str | None = None):
    """
    Injects iOS Safari 'Add to Home Screen' standalone PWA metadata, apple-touch-icon,
    viewport-fit=cover, numeric keypad hints (inputmode='decimal'), and right-edge
    popover viewport clamping into the parent Streamlit document.
    """
    logo_json = json.dumps(logo_b64 or "")
    components.html(
        f"""
        <script>
        (function() {{
            const logoB64 = {logo_json};
            let docs = [];
            try {{ if (window.parent && window.parent.document) docs.push(window.parent.document); }} catch (e) {{}}
            try {{ if (window.top && window.top.document && !docs.includes(window.top.document)) docs.push(window.top.document); }} catch (e) {{}}

            function upsertMeta(doc, name, content) {{
                let el = doc.querySelector('meta[name="' + name + '"]');
                if (!el) {{
                    el = doc.createElement('meta');
                    el.setAttribute('name', name);
                    doc.head.appendChild(el);
                }}
                el.setAttribute('content', content);
            }}

            function upsertLink(doc, rel, href) {{
                if (!href) return;
                let el = doc.querySelector('link[rel="' + rel + '"]');
                if (!el) {{
                    el = doc.createElement('link');
                    el.setAttribute('rel', rel);
                    doc.head.appendChild(el);
                }}
                el.setAttribute('href', href);
            }}

            docs.forEach(function(doc) {{
                try {{
                    upsertMeta(doc, 'viewport', 'width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover');
                    upsertMeta(doc, 'apple-mobile-web-app-capable', 'yes');
                    upsertMeta(doc, 'mobile-web-app-capable', 'yes');
                    upsertMeta(doc, 'apple-mobile-web-app-status-bar-style', 'black-translucent');
                    upsertMeta(doc, 'apple-mobile-web-app-title', 'WealthFlow');
                    upsertMeta(doc, 'theme-color', '#090D16');
                    if (logoB64) {{
                        upsertLink(doc, 'apple-touch-icon', logoB64);
                    }}
                }} catch (e) {{}}
            }});

            // Enhance number inputs for iPhone decimal keypad & clamp popovers inside viewport
            try {{
                const doc = window.parent.document;
                const win = window.parent;

                function enhanceMobileDom() {{
                    doc.querySelectorAll('input[type="number"]').forEach(function(inp) {{
                        if (!inp.getAttribute('inputmode')) {{
                            inp.setAttribute('inputmode', 'decimal');
                        }}
                    }});

                    // Strip popover chevron AND its wrapper inside top-right profile icon button so person icon sits dead-center
                    const prof = doc.querySelector('.st-key-m_profile_pop button');
                    if (prof) {{
                        prof.querySelectorAll('[data-testid="stIconMaterial"]').forEach(function(ic) {{
                            if ((ic.textContent || '').trim().toLowerCase() !== 'person') {{
                                ic.style.display = 'none';
                                if (ic.parentElement && ic.parentElement !== prof) {{
                                    ic.parentElement.style.display = 'none';
                                }}
                            }}
                        }});
                    }}

                    // Keep every popover safely inside narrow mobile viewport
                    const vw = win.innerWidth || doc.documentElement.clientWidth || 393;
                    doc.querySelectorAll('[data-baseweb="popover"]').forEach(function(layer) {{
                        if (!layer.querySelector('[data-testid="stPopoverBody"]')) return;
                        if (layer.querySelector('.wf-m-profile-head')) {{
                            layer.style.position = 'fixed';
                            layer.style.top = '58px';
                            layer.style.right = '12px';
                            layer.style.left = 'auto';
                            layer.style.transform = 'none';
                            return;
                        }}
                        const rect = layer.getBoundingClientRect();
                        if (rect.width > 0 && rect.right > vw - 10) {{
                            const shift = Math.ceil(rect.right - (vw - 10));
                            if (shift > 1) {{
                                const cur = parseFloat(layer.style.marginLeft || '0') || 0;
                                layer.style.marginLeft = (cur - shift) + 'px';
                            }}
                        }}
                        if (rect.width > 0 && rect.left < 10) {{
                            const shiftR = Math.ceil(10 - rect.left);
                            if (shiftR > 1) {{
                                const cur = parseFloat(layer.style.marginLeft || '0') || 0;
                                layer.style.marginLeft = (cur + shiftR) + 'px';
                            }}
                        }}
                    }});
                }}

                if (!win.__wfMobileObs) {{
                    win.__wfMobileObs = new MutationObserver(enhanceMobileDom);
                    win.__wfMobileObs.observe(doc.body, {{ childList: true, subtree: true }});
                }}
                enhanceMobileDom();
                setTimeout(enhanceMobileDom, 250);
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )
