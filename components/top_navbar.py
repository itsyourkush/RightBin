"""
Top Navigation Bar Component for RightBin — "Wet or Dry, Always Right."
Matches the modern Eco-SaaS horizontal navigation design specification.
Injects the SDG 13 Pill Badge and Forest Green 'Scan Waste' CTA button into the header.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


def render_top_navbar() -> None:
    """
    Renders the modern top navigation enhancements:
    - Pinned white header bar with subtle shadow & border
    - Active green pill tabs with leaf icons
    - SDG 13: Climate Action mint glowing badge on the right
    - Deep forest green 'Scan Waste' CTA button with compass/camera pointer
    """
    js_code = """
    <script>
    (function initRightBinTopNavbar() {
        function attachNavbarActions() {
            try {
                const doc = window.parent.document;
                if (!doc) return;

                const header = doc.querySelector('header[data-testid="stHeader"]') || 
                               doc.querySelector('.stAppHeader') ||
                               doc.querySelector('[data-testid="stHeader"]');
                if (!header) return;

                // Ensure right actions container exists
                let actionWrapper = doc.getElementById('rightbin-header-actions');
                if (!actionWrapper) {
                    actionWrapper = doc.createElement('div');
                    actionWrapper.id = 'rightbin-header-actions';
                    actionWrapper.className = 'rightbin-header-actions-wrapper';
                    actionWrapper.innerHTML = `
                        <div class="sdg-pill-badge" title="UN Sustainable Development Goal 13: Climate Action">
                            <span class="sdg-glow-dot"></span>
                            <span class="sdg-text">SDG 13: Climate Action</span>
                        </div>
                        <a id="header-scan-waste-cta" class="header-cta-button" href="scan-waste" target="_self">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
                            </svg>
                            <span>Scan Waste</span>
                        </a>
                    `;

                    // Attach to toolbar or header
                    const toolbar = header.querySelector('[data-testid="stToolbar"]') || header;
                    toolbar.appendChild(actionWrapper);

                    // Add click handler to navigate seamlessly
                    const ctaLink = actionWrapper.querySelector('#header-scan-waste-cta');
                    if (ctaLink) {
                        ctaLink.addEventListener('click', function(e) {
                            // Find native streamlit top nav link if available for instant SPA navigation
                            const nativeScanLink = doc.querySelector('a[data-testid="stTopNavLink"][href*="scan-waste"]') ||
                                                   doc.querySelector('a[data-testid="stTopNavLink"][href*="Scan_Waste"]');
                            if (nativeScanLink) {
                                e.preventDefault();
                                nativeScanLink.click();
                            }
                        });
                    }
                }
            } catch (err) {
                console.error("Top Navbar init error:", err);
            }
        }

        // Run immediately and retry briefly in case Streamlit is still mounting elements
        attachNavbarActions();
        setTimeout(attachNavbarActions, 150);
        setTimeout(attachNavbarActions, 600);
        setTimeout(attachNavbarActions, 1500);
    })();
    </script>
    """
    # Render with height 0 so it takes no vertical space on the canvas
    components.html(js_code, height=0, width=0)
