import gradio as gr


def create_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="gray",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="#f8fafb",
        body_text_color="#1e293b",
        block_background_fill="white",
        block_border_width="1px",
        block_border_color="#e2e8f0",
        block_radius="12px",
        button_primary_background_fill="#2563eb",
        button_primary_text_color="white",
        button_primary_border_color="#2563eb",
        button_primary_background_fill_hover="#1d4ed8",
        button_secondary_background_fill="#f1f5f9",
        button_secondary_text_color="#475569",
        slider_color="#2563eb",
        input_background_fill="#f8fafc",
        input_border_color="#cbd5e1",
        input_radius="8px",
    )
