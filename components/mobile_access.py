"""
Mobile Access & Universal QR Code Component for RightBin.
Encodes the live Streamlit Cloud HTTPS URL or local Wi-Fi IP so users can scan
and classify waste items directly using their iPhone Safari or Android camera.
"""

from __future__ import annotations

import io
from pathlib import Path
import re
import socket
import subprocess
import streamlit as st

try:
    import qrcode
    from PIL import Image as PILImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default verified production Streamlit Cloud URL
PRODUCTION_CLOUD_URL = "https://rightbin-wzuhqi3mgruu7flc9ozfmd.streamlit.app"


def get_detected_cloud_url() -> str:
    """
    Detects the active Streamlit Cloud or public HTTPS domain from request headers.
    Falls back to the verified production deployment URL.
    """
    try:
        if hasattr(st, "context"):
            headers = getattr(st.context, "headers", None) or {}
            for h in ("x-forwarded-host", "host", "origin", "referer"):
                val = headers.get(h, "")
                if val:
                    clean_host = val.replace("https://", "").replace("http://", "").split("/")[0]
                    if "streamlit.app" in clean_host or "render.com" in clean_host or "herokuapp.com" in clean_host:
                        return f"https://{clean_host}"

            ctx_url = getattr(st.context, "url", None)
            if ctx_url:
                u = str(ctx_url).split("?")[0].rstrip("/")
                if "streamlit.app" in u:
                    return u
    except Exception:
        pass

    return PRODUCTION_CLOUD_URL


def detect_lan_ip() -> str:
    """Detects LAN IP across active network interfaces."""
    # 1. Socket probe (works across macOS, Linux, and Windows)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "127.0.0.1" and not ip.startswith("172."):
            return ip
    except Exception:
        pass

    # 2. macOS ipconfig probe
    for iface in ("en0", "en1", "wlan0", "eth0"):
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

    return "192.168.1.36"


def render_mobile_access_section(port: int = 8501) -> None:
    """
    Renders the QR code card for instant mobile scanning.
    Defaults to the live Streamlit Cloud HTTPS URL so any phone camera
    can scan and open the page without configuration or local network issues.
    """
    cloud_base_url = get_detected_cloud_url()
    lan_ip = detect_lan_ip()
    local_wifi_url = f"http://{lan_ip}:{port}/scan-waste"
    cloud_scan_url = f"{cloud_base_url}/scan-waste"

    with st.container(border=True):
        col_qr, col_info = st.columns([1, 2])

        with col_info:
            st.markdown(
                """
                <div style="padding-top: 2px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: #064E3B;">📱 Open RightBin on Mobile Camera</span>
                        <span style="background: #ECFDF5; color: #047857; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 9999px; border: 1px solid #A7F3D0;">iOS Safari & Android</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #475569; margin-bottom: 10px; line-height: 1.45;">
                        Point your <strong>iPhone Camera (Safari)</strong> or <strong>Android (Camera / Google Lens)</strong> at the QR code to test instant waste scanning with full camera support.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Available URL modes
            mode_options = [
                "🌐 Live Cloud (Works Everywhere / 5G / Mobile Data)",
                f"📶 Local Wi-Fi Network ({lan_ip})",
                "✏️ Custom URL",
            ]

            selected_mode = st.radio(
                "Select QR Connection Mode:",
                options=mode_options,
                index=0,
                horizontal=True,
                label_visibility="collapsed",
                key="qr_connection_mode_selector",
            )

            if "Live Cloud" in selected_mode:
                target_url = cloud_scan_url
                mode_tip = "🔒 **Public HTTPS Live**: Recommended. Works on any smartphone over 5G, 4G, or Wi-Fi with camera permissions enabled."
            elif "Local Wi-Fi" in selected_mode:
                target_url = local_wifi_url
                mode_tip = f"⚡ **Local Wi-Fi Active**: Your phone must be connected to the **same Wi-Fi** network as this computer ({lan_ip})."
            else:
                custom_input = st.text_input(
                    "Enter Custom URL:",
                    value=cloud_scan_url,
                    key="custom_qr_url_input",
                ).strip()
                target_url = custom_input if custom_input else cloud_scan_url
                mode_tip = "✏️ **Custom URL Active**: The QR code encodes your custom address."

            # URL Display Box with Clickable Link
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 10px 14px; margin: 8px 0; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
                    <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.86rem; word-break: break-all;">
                        <span style="color: #64748B; font-weight: 600;">Link:</span> 
                        <a href="{target_url}" target="_blank" style="color: #047857; text-decoration: underline; font-weight: 700;">{target_url}</a>
                    </div>
                    <a href="{target_url}" target="_blank" style="background: #10B981; color: white; text-decoration: none; padding: 5px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; white-space: nowrap;">
                        Open ↗
                    </a>
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
