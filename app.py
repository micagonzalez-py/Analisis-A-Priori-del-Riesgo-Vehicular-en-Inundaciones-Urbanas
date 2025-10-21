# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

# -------------------------
# Config y constantes
# -------------------------
st.set_page_config(page_title="Simulador de Flotación y Deslizamiento", layout="wide")
st.title("Análisis A Priori: Flotación y Deslizamiento Vehicular")
st.markdown(
    "Escaneá el QR, completá parámetros y obtené el diagnóstico inmediato."
)

# físicos / defaults
g = 9.81
densidad_agua = 1000
DEFAULTS = {
    "altura_libre_suelo": 0.28,
    "masa_auto": 3000,
    "largo_auto": 4.795,
    "ancho_auto": 1.855,
    "alto_auto": 1.835,
    "porcentaje_flotante": 1.0,
    "Cd": 1.0,
    "mu": 0.5
}

# Metadatos textual (según tus indicaciones)
AUTORES = "Micaela González · Eduardo Ojeda · Marcelo Castier · Christian Shaerer · Liz Ojeda"
HANDLES = "@SocientificaPy  @SCientificaPy"
SUBTITULO = "Escaneá el QR y obtené tu diagnóstico."
TITULO_CORTO = "Riesgo de Flotación y Deslizamiento"
FOOTER_TAG = "Proyecto desarrollado en Python"

# -------------------------
# Sidebar: parámetros del vehículo
# -------------------------
st.sidebar.header("Parámetros del vehículo")
altura_libre_suelo = st.sidebar.number_input("Altura libre suelo (m)", value=DEFAULTS["altura_libre_suelo"], step=0.01, format="%.2f")
masa_auto = st.sidebar.number_input("Masa (kg)", value=DEFAULTS["masa_auto"], step=10)
largo_auto = st.sidebar.number_input("Largo (m)", value=DEFAULTS["largo_auto"], step=0.01, format="%.3f")
ancho_auto = st.sidebar.number_input("Ancho (m)", value=DEFAULTS["ancho_auto"], step=0.01, format="%.3f")
alto_auto = st.sidebar.number_input("Alto (m)", value=DEFAULTS["alto_auto"], step=0.01, format="%.3f")
st.sidebar.markdown("---")
st.sidebar.header("Parámetros hidrodinámicos")
porcentaje_flotante = st.sidebar.slider("Porcentaje flotante (factor)", 0.0, 1.0, DEFAULTS["porcentaje_flotante"], step=0.01)
Cd = st.sidebar.slider("Coef. arrastre Cd", 0.1, 3.0, DEFAULTS["Cd"], step=0.01)
mu = st.sidebar.slider("Coef. fricción (μ)", 0.0, 1.5, DEFAULTS["mu"], step=0.01)

# -------------------------
# Inputs principales
# -------------------------
st.subheader("Condición de la inundación")
col1, col2 = st.columns([1,1])
with col1:
    altura_agua = st.slider("Altura del agua (m)", min_value=0.00, max_value=2.0, value=0.55, step=0.01)
with col2:
    velocidad_agua = st.slider("Velocidad del agua (m/s)", min_value=0.0, max_value=6.0, value=2.0, step=0.05)

# -------------------------
# Cálculos
# -------------------------
area_base = largo_auto * ancho_auto
area_frontal = alto_auto * ancho_auto
peso = masa_auto * g

def generar_plots_y_texto(altura_agua, velocidad_agua):
    # fuerzas
    altura_sumergida = max(0, altura_agua - altura_libre_suelo)
    volumen_desplazado = altura_sumergida * area_base
    empuje = densidad_agua * g * volumen_desplazado * porcentaje_flotante
    normal = max(0, peso - empuje)
    friccion = mu * normal
    area_lateral_sumergida = altura_sumergida * ancho_auto
    fuerza_arrastre = 0.5 * Cd * densidad_agua * area_lateral_sumergida * velocidad_agua**2
    se_mueve = fuerza_arrastre > friccion
    se_flota = empuje > peso

    # Mapa
    alturas = np.linspace(0.01, 1.8, 200)
    velocidades = np.linspace(0.01, 6.0, 200)
    A, V = np.meshgrid(alturas, velocidades)
    altura_sum = np.maximum(0, A - altura_libre_suelo)
    empuje_grid = densidad_agua * g * altura_sum * area_base * porcentaje_flotante
    normal_grid = np.maximum(0, peso - empuje_grid)
    friccion_grid = mu * normal_grid
    area_lateral_grid = altura_sum * ancho_auto
    arrastre_grid = 0.5 * Cd * densidad_agua * area_lateral_grid * V**2
    riesgo_arrastre = np.clip(arrastre_grid / (friccion_grid + 1e-9), 0, 3)
    riesgo_empuje = np.clip(empuje_grid / (peso + 1e-9), 0, 2)

    # Colormap (mantener paleta suave)
    cmap_riesgo = LinearSegmentedColormap.from_list("riesgo_soft", ["#C5E26A", "#F4F1BB", "#f2a096", "#e0786c"])

    # --- FIGURA matplotlib
    fig, axes = plt.subplots(3, 1, figsize=(7, 11), gridspec_kw={'height_ratios':[1.1,1,1]}, constrained_layout=True)
    ax0, ax1, ax2 = axes

    # barras
    labels = ['Peso', 'F. Empuje', 'F. Fricción', 'F. Arrastre']
    values = [peso, empuje, friccion, fuerza_arrastre]
    colors = ['#4B6A9B', '#63ACE5', '#7BC043', '#FF6F61']
    bars = ax0.bar(labels, values, color=colors, edgecolor="black", alpha=0.95)
    ax0.set_ylabel("Fuerza (N)")
    ax0.set_title(f"Altura Agua: {altura_agua:.2f} m  |  Velocidad: {velocidad_agua:.2f} m/s")
    for bar in bars:
        yval = bar.get_height()
        ax0.text(bar.get_x() + bar.get_width()/2.0, yval + max(values)*0.03, f'{yval:,.0f}', ha='center', va='bottom', fontsize=9)
    ax0.set_ylim(0, max(values)*1.25)
    ax0.grid(axis='y', linestyle='--', alpha=0.4)

    # mapa arrastre/friccion
    im1 = ax1.imshow(riesgo_arrastre, extent=[alturas.min(), alturas.max(), velocidades.min(), velocidades.max()],
                     origin='lower', aspect='auto', cmap=cmap_riesgo)
    ax1.scatter(altura_agua, velocidad_agua, color='black', s=40, zorder=6)
    ax1.set_title("Mapa de Riesgo: Arrastre / Fricción")
    ax1.set_xlabel("Altura del Agua [m]")
    ax1.set_ylabel("Velocidad [m/s]")
    plt.colorbar(im1, ax=ax1, orientation='vertical', label='Arrastre / Fricción')

    # mapa empuje/peso
    im2 = ax2.imshow(riesgo_empuje, extent=[alturas.min(), alturas.max(), velocidades.min(), velocidades.max()],
                     origin='lower', aspect='auto', cmap=cmap_riesgo)
    ax2.scatter(altura_agua, velocidad_agua, color='black', s=40, zorder=6)
    ax2.set_title("Mapa de Riesgo: Empuje / Peso")
    ax2.set_xlabel("Altura del Agua [m]")
    ax2.set_ylabel("Velocidad [m/s]")
    plt.colorbar(im2, ax=ax2, orientation='vertical', label='Empuje / Peso')

    return fig, {
        "empuje": empuje,
        "peso": peso,
        "friccion": friccion,
        "fuerza_arrastre": fuerza_arrastre,
        "se_mueve": se_mueve,
        "se_flota": se_flota
    }

# Mostrar plots y texto en la app
fig, metrics = generar_plots_y_texto(altura_agua, velocidad_agua)
st.pyplot(fig)

st.markdown("---")
diag = []
diag.append(f"🔵 **Empuje:** {metrics['empuje']:,.0f} N")
diag.append(f"🔴 **Peso:** {metrics['peso']:,.0f} N")
diag.append(f"🟢 **Fuerza de fricción:** {metrics['friccion']:,.0f} N")
diag.append(f"🟠 **Fuerza de arrastre:** {metrics['fuerza_arrastre']:,.0f} N")
if metrics["se_flota"]:
    diag.append("⚠️ **El vehículo tiende a FLOTAR.**")
else:
    diag.append("✅ **El vehículo permanece apoyado en el suelo.**")
if metrics["se_mueve"]:
    diag.append("🚨 **El vehículo puede DESLIZARSE por el arrastre.**")
else:
    diag.append("🛑 **El vehículo se mantiene inmóvil (fricción suficiente).**")
st.markdown("\n\n".join(diag))

# -------------------------
# Sección: Poster / recortes automáticos (pero ajustables)
# -------------------------
st.markdown("---")
st.subheader("Poster y recortes (logos / QR) — Editor rápido")
st.markdown("Subí tu póster o usa el póster por defecto. Ajustá los recortes si es necesario para mejorar la calidad de los logos/QR incluidos en la story.")

# Ruta por defecto del poster (estaba en el contenedor)
DEFAULT_POSTER_PATH = "/mnt/data/98d1318b-e812-4b71-8776-8147b061014e.png"
uploaded = st.file_uploader("Subir póster (opcional, PNG/JPG). Si no subís, uso el póster por defecto.", type=["png","jpg","jpeg"])
if uploaded is not None:
    poster = Image.open(uploaded).convert("RGBA")
else:
    if os.path.exists(DEFAULT_POSTER_PATH):
        poster = Image.open(DEFAULT_POSTER_PATH).convert("RGBA")
        st.info("Usando póster por defecto subido anteriormente.")
    else:
        poster = None
        st.warning("No se encontró póster por defecto. Subí uno para recortar logos/QR.")

if poster is not None:
    # mostrar poster
    st.image(poster, caption="Póster (fuente para logos y QR)", use_column_width=True)

    W, H = poster.size
    st.write(f"Dimensiones poster: {W}px × {H}px")

    st.markdown("Ajustá las áreas de recorte (valores relativos). Si los logos/QR se ven cortados, mové las barras.")
    # Defaults razonables asumidas (basadas en tu poster original; el usuario puede ajustarlas)
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.write("Logo (izq) - franja superior")
        lx = st.slider("lx (left fraction)", 0.0, 0.5, 0.03, step=0.01, key="lx")
        ly = st.slider("ly (top fraction)", 0.0, 0.2, 0.02, step=0.01, key="ly")
        lw = st.slider("lw (width fraction)", 0.05, 0.5, 0.22, step=0.01, key="lw")
        lh = st.slider("lh (height fraction)", 0.02, 0.4, 0.12, step=0.01, key="lh")

    with col_b:
        st.write("Logo (der) - franja superior")
        rx = st.slider("rx (left fraction)", 0.5, 0.98, 0.72, step=0.01, key="rx")
        ry = st.slider("ry (top fraction)", 0.0, 0.2, 0.02, step=0.01, key="ry")
        rw = st.slider("rw (width fraction)", 0.03, 0.5, 0.22, step=0.01, key="rw")
        rh = st.slider("rh (height fraction)", 0.02, 0.4, 0.12, step=0.01, key="rh")

    with col_c:
        st.write("QR (inferior derecha)")
        qx = st.slider("qx (left fraction)", 0.5, 0.98, 0.78, step=0.01, key="qx")
        qy = st.slider("qy (top fraction)", 0.6, 0.98, 0.72, step=0.01, key="qy")
        qw = st.slider("qw (width fraction)", 0.03, 0.5, 0.18, step=0.01, key="qw")
        qh = st.slider("qh (height fraction)", 0.03, 0.5, 0.18, step=0.01, key="qh")

    # calcular boxes y recortar
    def fraction_to_box(fx, fy, fw, fh, W, H):
        left = int(fx * W)
        top = int(fy * H)
        right = int((fx + fw) * W)
        bottom = int((fy + fh) * H)
        # proteger límites
        left = max(0, min(left, W-1))
        top = max(0, min(top, H-1))
        right = max(left+1, min(right, W))
        bottom = max(top+1, min(bottom, H))
        return (left, top, right, bottom)

    box_l = fraction_to_box(lx, ly, lw, lh, W, H)
    box_r = fraction_to_box(rx, ry, rw, rh, W, H)
    box_q = fraction_to_box(qx, qy, qw, qh, W, H)

    logo_left = poster.crop(box_l).convert("RGBA")
    logo_right = poster.crop(box_r).convert("RGBA")
    qr_crop = poster.crop(box_q).convert("RGBA")

    st.write("Preview recortes:")
    c1, c2, c3 = st.columns([1,1,1])
    c1.image(logo_left, caption="Logo encuentro (izq)")
    c2.image(logo_right, caption="Logo sociedad (der)")
    c3.image(qr_crop, caption="QR (inferior derecha)")

else:
    logo_left = None
    logo_right = None
    qr_crop = None

# -------------------------
# Función para componer la story Instagram
# -------------------------
def create_story_instagram(fig_matplotlib, logo_left=None, logo_right=None, qr_img=None,
                           title=TITULO_CORTO, subtitle=SUBTITULO, autores=AUTORES,
                           handles=HANDLES, footer_tag=FOOTER_TAG):
    # Tamaño historia Instagram
    W, H = 1080, 1920
    bg_top = (21, 48, 114)  # azul oscuro para franja superior (coherente con póster)
    bg_body_top = (250, 252, 255)
    bg_body_bottom = (245, 247, 250)

    # Crear fondo con gradiente sutil vertical
    base = Image.new("RGB", (W, H), bg_body_top)
    draw = ImageDraw.Draw(base)
    for y in range(H):
        t = y / (H - 1)
        r = int(bg_body_top[0] * (1-t) + bg_body_bottom[0] * t)
        g = int(bg_body_top[1] * (1-t) + bg_body_bottom[1] * t)
        b = int(bg_body_top[2] * (1-t) + bg_body_bottom[2] * t)
        draw.line([(0, y), (W, y)], fill=(r,g,b))

    # franja superior fina
    franja_h = 110
    draw.rectangle([0, 0, W, franja_h], fill=bg_top)

    # logos en la franja superior
    margin = 40
    if logo_left is not None:
        # escalar logo manteniendo proporción para que no supere la franja
        max_h = franja_h - 20
        lw, lh = logo_left.size
        scale = min(1.0, max_h / lh)
        new_sz = (int(lw*scale), int(lh*scale))
        logo_l = logo_left.resize(new_sz, Image.LANCZOS)
        base.paste(logo_l, (margin, (franja_h - new_sz[1])//2), logo_l)

    if logo_right is not None:
        max_h = franja_h - 20
        lw, lh = logo_right.size
        scale = min(1.0, max_h / lh)
        new_sz = (int(lw*scale), int(lh*scale))
        logo_r = logo_right.resize(new_sz, Image.LANCZOS)
        base.paste(logo_r, (W - margin - new_sz[0], (franja_h - new_sz[1])//2), logo_r)

    # Cargar fuente (si no está disponible, usar default)
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
        font_sub = ImageFont.truetype("DejaVuSans.ttf", 28)
        font_auth = ImageFont.truetype("DejaVuSans.ttf", 22)
        font_handles = ImageFont.truetype("DejaVuSans.ttf", 20)
        font_footer = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_auth = ImageFont.load_default()
        font_handles = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # Título y subtítulo (centrados)
    # Título multilinea si es muy largo
    title_y = franja_h + 36
    # ajustar tamaño de fuente si texto es demasiado largo (simple ajuste)
    draw.text((W//2 - draw.textsize(title)[0]//2, title_y), title, font=font_title, fill=(255,255,255))
    # subtitle en azul oscuro bajo el título
    subtitle_y = title_y + 56
    draw.text((W//2 - draw.textsize(subtitle)[0]//2, subtitle_y), subtitle, font=font_sub, fill=(21,48,114))

    # Autores debajo del subtitulo
    auth_y = subtitle_y + 46
    draw.text((W//2 - draw.textsize(autores)[0]//2, auth_y), autores, font=font_auth, fill=(60,60,60))

    # Convertir figura matplotlib a imagen PIL y escalar para area central
    buf = io.BytesIO()
    fig_matplotlib.savefig(buf, format="png", dpi=150, bbox_inches='tight', transparent=True)
    buf.seek(0)
    plot_img = Image.open(buf).convert("RGBA")

    # Área central destinada al plot
    plot_top = auth_y + 50
    plot_left = 60
    plot_right = W - 60
    plot_bottom = H - 320  # dejar espacio para footer/QR
    gw = plot_right - plot_left
    gh = plot_bottom - plot_top

    # Escalar plot_img manteniendo ratio
    pw, ph = plot_img.size
    scale = min(gw/pw, gh/ph)
    new_plot_sz = (int(pw*scale), int(ph*scale))
    plot_resized = plot_img.resize(new_plot_sz, Image.LANCZOS)
    paste_x = plot_left + (gw - new_plot_sz[0])//2
    paste_y = plot_top + (gh - new_plot_sz[1])//2
    base.paste(plot_resized, (paste_x, paste_y), plot_resized)

    # franja inferior (gris suave)
    footer_h = 260
    footer_y = H - footer_h
    draw.rectangle([0, footer_y, W, H], fill=(245,247,250))

    # QR a la derecha dentro del footer
    if qr_img is not None:
        max_q_h = footer_h - 80
        qw, qh = qr_img.size
        scale_q = min(1.0, max_q_h / qh)
        new_q = (int(qw*scale_q), int(qh*scale_q))
        q_res = qr_img.resize(new_q, Image.LANCZOS)
        q_x = W - margin - new_q[0]
        q_y = footer_y + (footer_h - new_q[1])//2
        base.paste(q_res, (q_x, q_y), q_res)

    # handles y texto a la izquierda del footer
    handles_x = 80
    handles_y = footer_y + 40
    draw.text((handles_x, handles_y), handles, font=font_handles, fill=(30,30,30))
    draw.text((handles_x, handles_y + 40), footer_tag, font=font_footer, fill=(21,48,114))

    return base

# -------------------------
# Generar y descargar story
# -------------------------
st.markdown("---")
st.subheader("Exportar story (Instagram 1080×1920)")

if st.button("Generar story Instagram"):
    # generate current fig again (it already exists)
    story_img = create_story_instagram(fig, logo_left=logo_left, logo_right=logo_right, qr_img=qr_crop,
                                       title=TITULO_CORTO, subtitle=SUBTITULO, autores=AUTORES,
                                       handles=HANDLES, footer_tag=FOOTER_TAG)
    st.image(story_img, caption="Preview story (1080×1920)", use_column_width=False)
    buf_out = io.BytesIO()
    story_img.save(buf_out, format="PNG", optimize=True)
    buf_out.seek(0)
    st.download_button("Descargar story (PNG)", buf_out, file_name="story_instagram.png", mime="image/png")

st.markdown("Si querés que mejore los recortes automáticamente, mové los sliders hasta que los previews de logo y QR queden perfectos. Si querés, subí logos de mayor resolución para reemplazarlos.")
