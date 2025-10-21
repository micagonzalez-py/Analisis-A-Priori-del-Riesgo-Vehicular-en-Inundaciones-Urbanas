# Añadir al inicio del archivo
from PIL import Image, ImageDraw, ImageFont
import base64

# Función que toma la figura matplotlib y genera una imagen social (PIL.Image)
def create_social_image(fig, params_text, logo_file=None, size="square"):
    """
    fig: matplotlib.figure.Figure
    params_text: str -> texto con parámetros para poner en el pie
    logo_file: file-like (BytesIO) o None
    size: "square" (1080x1080) o "landscape" (1200x675)
    """
    # TAMAÑOS (px)
    if size == "square":
        W, H = 1080, 1080
        graph_area = (80, 140, W-80, H-260)  # left, top, right, bottom
    else:
        W, H = 1200, 675
        graph_area = (80, 120, W-80, H-170)

    # Guardar figura matplotlib en buffer con fondo transparente
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches='tight', transparent=True)
    buf.seek(0)
    plot_img = Image.open(buf).convert("RGBA")

    # Crear fondo (gradiente sutil)
    base = Image.new("RGBA", (W, H), (255,255,255,255))
    # opcional: gradiente vertical (from white to soft color)
    top_color = (250, 252, 255)
    bottom_color = (240, 245, 250)
    for y in range(H):
        t = y / (H-1)
        r = int(top_color[0]*(1-t) + bottom_color[0]*t)
        g = int(top_color[1]*(1-t) + bottom_color[1]*t)
        b = int(top_color[2]*(1-t) + bottom_color[2]*t)
        ImageDraw.Draw(base).line([(0,y),(W,y)], fill=(r,g,b))

    # Encabezado
    header_h = 120 if size=="square" else 100
    draw = ImageDraw.Draw(base)
    try:
        # intenta cargar una fuente TTF limpia; si no, usa default
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_body = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
    except Exception:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    title_text = "Riesgo: Flotación y Deslizamiento"
    # Centrar título
    tw, th = draw.textsize(title_text, font=font_title)
    draw.text(((W-tw)/2, 30), title_text, font=font_title, fill=(30,30,40))

    # Pegar el plot en el área destinada (escalado manteniendo aspect)
    left, top, right, bottom = graph_area
    gw = right - left
    gh = bottom - top
    # escalar plot_img para que quepa en gw x gh
    plot_w, plot_h = plot_img.size
    scale = min(gw/plot_w, gh/plot_h)
    new_size = (int(plot_w*scale), int(plot_h*scale))
    plot_resized = plot_img.resize(new_size, Image.LANCZOS)
    paste_x = left + (gw - new_size[0])//2
    paste_y = top + (gh - new_size[1])//2
    base.paste(plot_resized, (paste_x, paste_y), plot_resized)

    # Pie con parámetros (background strip)
    footer_h = H - bottom + 30
    footer_y = bottom - 10
    draw.rectangle([(0, footer_y), (W, H)], fill=(255,255,255,230))
    # Texto de parámetros a la izquierda
    margin = 90
    x_text = margin
    y_text = footer_y + 12
    # dividir params_text en líneas si es necesario
    for i, line in enumerate(params_text.split("\n")):
        draw.text((x_text, y_text + i*24), line, font=font_body, fill=(40,40,40))

    # Logo o watermark a la derecha del pie
    if logo_file is not None:
        try:
            logo = Image.open(logo_file).convert("RGBA")
            max_logo_h = footer_h - 24
            logo_w, logo_h = logo.size
            scale = min((max_logo_h/logo_h), 0.35)  # no muy grande
            new_logo_size = (int(logo_w*scale), int(logo_h*scale))
            logo_resized = logo.resize(new_logo_size, Image.LANCZOS)
            logo_x = W - new_logo_size[0] - margin//2
            logo_y = footer_y + (footer_h - new_logo_size[1])//2
            base.paste(logo_resized, (logo_x, logo_y), logo_resized)
        except Exception as e:
            pass

    # Marca pequeña en esquina inferior izquierda (ej: @tu_usuario)
    handle = "@tu_usuario"
    draw.text((margin, H - 28), handle, font=font_small, fill=(80,80,80))

    # Opcional: overlay semi-transparente para destacar diagnóstico (si querés)
    return base.convert("RGB")  # RGB listo para guardar como PNG/JPEG

# Integración en Streamlit: botón para elegir tamaño, subir logo y descargar
st.markdown("---")
st.subheader("Exportar imagen para redes")
col_a, col_b, col_c = st.columns([1,1,1])
with col_a:
    size_opt = st.selectbox("Formato", ["square (1080×1080)", "landscape (1200×675)"])
with col_b:
    logo_up = st.file_uploader("Subir logo (opcional, PNG/SVG)", type=["png","jpg","jpeg"])
with col_c:
    filename = st.text_input("Nombre archivo", value="grafico_social")

if st.button("Generar imagen para redes"):
    selected_size = "square" if "square" in size_opt else "landscape"
    # Texto de parámetros a mostrar en pie
    params_text = f"Altura agua: {altura_agua:.2f} m  |  Velocidad: {velocidad_agua:.2f} m/s\nMasa: {masa_auto:.0f} kg  |  μ={mu:.2f}  Cd={Cd:.2f}"
    social_img = create_social_image(fig, params_text, logo_file=logo_up, size=selected_size)
    # Mostrar preview
    st.image(social_img, use_column_width=True)
    # Preparar descarga
    buf2 = io.BytesIO()
    social_img.save(buf2, format="PNG", optimize=True)
    buf2.seek(0)
    st.download_button("Descargar imagen (PNG)", buf2, file_name=f"{filename}.png", mime="image/png")

