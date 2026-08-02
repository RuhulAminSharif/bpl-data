import base64
import os
import streamlit as st


def set_page_config():
    st.set_page_config(
        page_title="BPL Analysis Dashboard", page_icon="🏏", layout="wide"
    )

    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "images"))
    logo_path = os.path.join(base_path, "bpl_logo.jpg")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode()
            st.markdown(
                f"""
                <div style='text-align: center;'>
                    <img src='data:image/jpeg;base64,{encoded_image}' width='160' height='90' style='object-fit: contain;'/>
                    <h1 style='margin-top:5px; font-size: 2.2rem;'>BPL Data Analysis Dashboard</h1>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<h1 style='text-align: center;'>BPL Data Analysis Dashboard</h1>",
            unsafe_allow_html=True,
        )


def apply_custom_css():
    """Injects modern SaaS card styles and responsive CSS grid rules."""
    st.markdown(
        """
        <style>
            /* KPI Card Base Design */
            .kpi-card {
                background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.01) 100%);
                border: 1px solid rgba(150, 150, 150, 0.2);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                min-height: 120px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
                word-wrap: break-word; /* Prevents text overflow */
            }

            .kpi-badge {
                display: inline-block;
                background-color: rgba(255, 75, 75, 0.15);
                color: #ff4b4b;
                font-size: 0.72rem;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 12px;
                margin-top: 6px;
                white-space: nowrap; /* Keeps percentage text on one line */
                width: max-content;
                max-width: 100%;
            }
            .kpi-card:hover {
                transform: translateY(-2px);
                border-color: #ff4b4b;
                box-shadow: 0 6px 16px rgba(255, 75, 75, 0.15);
            }
            .kpi-title {
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #888888;
                margin-bottom: 4px;
            }
            .kpi-value {
                font-size: 1.6rem;
                font-weight: 700;
                line-height: 1.2;
            }
            .kpi-subtitle {
                font-size: 0.85rem;
                font-weight: 600;
                color: #ff4b4b;
                margin-top: 4px;
            }

            /* Responsive Adjustments for Mobile / Tablet */
            @media (max-width: 768px) {
                .kpi-card {
                    padding: 12px 14px;
                    min-height: 90px;
                }
                .kpi-value {
                    font-size: 1.3rem;
                }
                .kpi-title {
                    font-size: 0.75rem;
                }
            }
        </style>
        
        """,
        unsafe_allow_html=True,
    )


def render_feature_card(
    title: str,
    value: str | int,
    subtitle: str | None = None,
    badge: str | None = None,
    icon: str = "📊",
):
    """Renders a feature card for metrics and player/team records."""
    badge_html = f"<div class='kpi-badge'>{badge}</div>" if badge else ""
    subtitle_html = f"<div class='kpi-subtitle'>{subtitle}</div>" if subtitle else ""

    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        {subtitle_html}
        {badge_html}
    </div>
    """

    # ENSURE unsafe_allow_html=True IS PASSED HERE!
    st.markdown(card_html, unsafe_allow_html=True)
