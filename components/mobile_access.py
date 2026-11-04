"""
Mobile Access & Simple Universal QR Code Component.
Provides a clean, unified QR code for both iOS (Safari) and Android (Chrome / Lens).
Supports Live Streamlit Cloud, Cloudflare HTTPS Tunnel, and direct Local Wi-Fi (LAN) IP.
"""

from __future__ import annotations

import io
from pathlib import Path
import re
import subprocess
import streamlit as st

try:
    import qrcode
    from PIL import Image as PILImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_public_https_url() -> str | None:
    """Reads the active Cloudflare HTTPS tunnel URL if running."""
    tunnel_file = PROJECT_ROOT / "data" / "tunnel_url.txt"
    if tunnel_file.exists():
        try:
            url = tunnel_file.read_text().strip()
            if url.startswith("https://") and "trycloudflare.com" in url:
                return url
        except Exception:
            pass

    log_path = Path("/tmp/tunnel.log")
    if log_path.exists():
        try:
            content = log_path.read_text()
            matches = re.findall(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com", content)
            if matches:
                latest_url = matches[-1]
                try:
                    tunnel_file.parent.mkdir(parents=True, exist_ok=True)
                    tunnel_file.write_text(latest_url)
                except Exception:
                    pass
                return latest_url
        except Exception:
            pass

    return None


def detect_lan_ip() -> str:
    """Detects LAN IP across active network interfaces."""
    for iface in ("en0", "en1", "en2", "wlan0", "eth0"):
        try:
            res = subprocess.run(
                ["ipconfig", "getifaddr", iface],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            ip = res.stdout.strip()
            if ip and ip != "127.0.0.1" and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                return ip
        except Exception:
            pass

    return "127.0.0.1"


def get_cloud_or_host_url() -> str | None:
    """Detects if app is deployed on Streamlit Community Cloud or custom domain."""
    try:
        if hasattr(st, "context"):
            if hasattr(st.context, "headers") and st.context.headers:
                host = st.context.headers.get("host") or st.context.headers.get("Host")
                if host and ("streamlit.app" in host or "herokuapp.com" in host or "render.com" in host):
                    return f"https://{host}"
            if hasattr(st.context, "url") and st.context.url:
                u = str(st.context.url).split("?")[0].rstrip("/")
                if "streamlit.app" in u:
                    return u
    except Exception:
        pass
    return None


def render_mobile_access_section(port: int = 8501) -> None:
    """
    Renders a simple, clean, non-chaotic QR code card for both Android and iOS Safari.
    Allows toggling between Cloud / Live URL, Cloudflare HTTPS, and Local Wi-Fi.
    Avoids using st.code to prevent dynamic chunk import issues.
    """
    cloud_url = get_cloud_or_host_url()
    https_url = get_public_https_url()
    lan_ip = detect_lan_ip()
    local_wifi_url = f"http://{lan_ip}:{port}"

    with st.container(border=True):
        col_qr, col_info = st.columns([1, 2])

        with col_info:
            st.markdown(
                """
                <div style="padding-top: 2px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: #064E3B;">📱 Open RightBin on Mobile</span>
                        <span style="background: #ECFDF5; color: #047857; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 9999px; border: 1px solid #A7F3D0;">iOS Safari & Android</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin-bottom: 8px; line-height: 1.4;">
                        Scan with your <strong>iPhone Camera (Safari)</strong> or <strong>Android (Camera / Google Lens)</strong> to test live image scanning.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Build available options
            options = []
            if cloud_url:
                options.append(f"🌐 Streamlit Cloud Live (HTTPS)")
            if https_url:
                options.append("🌐 Cloudflare HTTPS (Works Anywhere / 5G)")
            options.append(f"📶 Same Wi-Fi Network ({lan_ip})")

            connection_mode = st.radio(
                "Select Connection Mode for QR:",
                options=options,
                index=0,
                horizontal=True,
                label_visibility="collapsed",
                key="qr_connection_mode",
            )

            if cloud_url and "Streamlit Cloud" in connection_mode:
                target_url = cloud_url
                mode_tip = "🔒 **Cloud HTTPS Active**: Best for mobile camera permissions anywhere."
            elif https_url and "Cloudflare" in connection_mode:
                target_url = https_url
                mode_tip = "🔒 **Cloudflare HTTPS Active**: Best for iPhone Safari camera permissions on cellular data."
            else:
                target_url = local_wifi_url
                mode_tip = "⚡ **Direct Wi-Fi Active**: Your phone must be connected to the **same Wi-Fi** as this computer."

            # Render styled URL container instead of st.code to avoid syntax highlighter chunk loads
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 8px 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.86rem; word-break: break-all; margin: 6px 0;">
                    <a href="{target_url}" target="_blank" style="color: #047857; text-decoration: none; font-weight: 700;">{target_url}</a>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(mode_tip)

        with col_qr:
            if HAS_QRCODE:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=6,
                    border=2,
                )
                qr.add_data(target_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#064E3B", back_color="white")

                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                buf.seek(0)
                st.image(buf, caption="Scan QR with Phone Camera", use_container_width=True)
            else:
                st.info("QR engine loading...")
