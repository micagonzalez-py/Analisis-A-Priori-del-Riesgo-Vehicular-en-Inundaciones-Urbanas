# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import io

# --- constantes físicas ---
g = 9.81  # m/s²
densidad_agua = 1000  # kg/m³

# --- valores por defecto (los tuyos) ---
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

st.set_page_config(page_title="Simulador de Flotación y Deslizamiento", layout="wide")
st.title("Análisis A Priori: Flotación y Deslizamiento Vehicular")
st.markdown(
    "Escaneá el QR, completá parámetros y obtené el diagnóstico inmediato (En la esquina superior izquierda puede acceder a los parámetros). "
    
)

# --- SIDEBAR: parámetros del vehículo (permite guardar defaults) ---
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

# --- inputs principales en la página (fáciles de usar en móviles) ---
st.subheader("Condición de la inundación")
col1, col2 = st.columns([1,1])
with col1:
    altura_agua = st.slider("Altura del agua (m)", min_value=0.00, max_value=2.0, value=0.55, step=0.01)
with col2:
    velocidad_agua = st.slider("Velocidad del agua (m/s)", min_value=0.0, max_value=6.0, value=2.0, step=0.05)

# Cálculos derivados
area_base = largo_auto * ancho_auto
area_frontal = alto_auto * ancho_auto
peso = masa_auto * g

# Función que genera todo (plots + diagnóstico) - adaptada de tu código
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

    # Colormap
    cmap_riesgo = LinearSegmentedColormap.from_list(
        "riesgo_soft",
        ["#A8C686","#BFD88E", "#F4F1BB", "#f2a096", "#e0786c"]
    )

    # --- FIGURA
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
        ax0.text(bar.get_x() + bar.get_width()/2.0, yval + max(values)*0.03,
                 f'{yval:,.0f}', ha='center', va='bottom', fontsize=9)
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

# Mostrar plots y texto
fig, metrics = generar_plots_y_texto(altura_agua, velocidad_agua)
st.pyplot(fig)

# Diagnóstico textual (con emojis)
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

# Botón para descargar la imagen
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=150)
buf.seek(0)
st.download_button("Descargar gráfico (PNG)", buf, file_name="riesgo_flotacion_deslizamiento.png", mime="image/png")


