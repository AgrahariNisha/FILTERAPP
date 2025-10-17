import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io

st.set_page_config(page_title="Photo Editor", page_icon="🖼️", layout="wide")
st.title("🖼️ Advanced Photo Editor (Clean view)")

# Upload
uploaded_file = st.file_uploader("📸 Upload an image (jpg / png)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGBA")  # keep alpha so rotations look nicer
    st.sidebar.header("🧰 Edit Controls")

    # Controls
    rotate_angle = st.sidebar.slider("Rotate (°)", 0, 360, 0)
    zoom = st.sidebar.slider("Zoom (%)", 50, 300, 100)
    # Pan sliders only useful when zoom > 100 (move the crop)
    pan_enabled = zoom > 100
    if pan_enabled:
        st.sidebar.markdown("**Pan (when zoomed in)**")
        pan_x = st.sidebar.slider("Pan X (left/right)", -100, 100, 0)
        pan_y = st.sidebar.slider("Pan Y (up/down)", -100, 100, 0)
    else:
        pan_x = 0
        pan_y = 0

    brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0)
    contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0)
    color = st.sidebar.slider("Color / Saturation", 0.0, 2.0, 1.0)
    flip = st.sidebar.selectbox("Flip", ["None", "Horizontal", "Vertical"])
    grayscale = st.sidebar.checkbox("Grayscale (B/W)")

    # Start processing (work on a copy)
    edited = image.copy()

    # Rotate (expand to keep whole rotated image)
    if rotate_angle != 0:
        edited = edited.rotate(rotate_angle, expand=True)

    # Zoom handling:
    w, h = edited.size

    if zoom == 100:
        # do nothing to size (no crop/resize)
        pass
    elif zoom > 100:
        # zoom in: crop a central region (with pan support) then upscale to original rotated size
        scale = zoom / 100.0
        crop_w = int(w / scale)
        crop_h = int(h / scale)

        # center + pan in pixels
        center_x = w // 2 + int((pan_x / 100.0) * (w - crop_w))
        center_y = h // 2 + int((pan_y / 100.0) * (h - crop_h))

        left = max(0, center_x - crop_w // 2)
        top = max(0, center_y - crop_h // 2)
        right = left + crop_w
        bottom = top + crop_h

        # ensure within bounds
        if right > w:
            right = w
            left = w - crop_w
        if bottom > h:
            bottom = h
            top = h - crop_h
        edited = edited.crop((left, top, right, bottom))
        # upscale back to original rotated dimensions for consistent side-by-side display
        edited = edited.resize((w, h), Image.LANCZOS)
    else:
        # zoom < 100 -> zoom out effect: shrink image and paste onto background canvas (letterbox)
        scale = zoom / 100.0
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        small = edited.resize((new_w, new_h), Image.LANCZOS)

        # create background same size as original and paste small image centered
        bg = Image.new("RGBA", (w, h), (0, 0, 0, 255))  # black background
        paste_x = (w - new_w) // 2
        paste_y = (h - new_h) // 2
        bg.paste(small, (paste_x, paste_y))
        edited = bg

    # Flip
    if flip == "Horizontal":
        edited = ImageOps.mirror(edited)
    elif flip == "Vertical":
        edited = ImageOps.flip(edited)

    # Brightness / Contrast / Color
    edited = ImageEnhance.Brightness(edited).enhance(brightness)
    edited = ImageEnhance.Contrast(edited).enhance(contrast)
    edited = ImageEnhance.Color(edited).enhance(color)

    # Grayscale
    if grayscale:
        # convert to 'L' then back to RGBA so display & download keep consistent mode
        edited = ImageOps.grayscale(edited).convert("RGBA")

    # Convert original to RGBA for consistent layout
    original_for_display = image.convert("RGBA")

    # Display only side-by-side (NO big image above)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🖼️ Original Image")
        st.image(original_for_display, use_container_width=True)
    with col2:
        st.markdown("### ✨ Edited Image")
        st.image(edited, use_container_width=True)

    # Download (use BytesIO so no extra file appears)
    buf = io.BytesIO()
    # save as PNG to keep quality & transparency handled
    edited.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    st.download_button("📥 Download Edited Image", data=buf, file_name="edited_image.png", mime="image/png")

else:
    st.info("📸 Please upload an image to begin editing.")
