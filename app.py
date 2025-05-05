import streamlit as st
import pandas as pd
from io import BytesIO
import re
import json
import os
import urllib.parse
import gdown

st.set_page_config(page_title="Productos para Mascotas", layout="wide")

# --- CONFIG ---
PRODUCTOS_FILE = "productos.json"
GOOGLE_DRIVE_URL = "https://docs.google.com/spreadsheets/d/1s6WswhgEg_ICoQRcr5ZI3H4MMh0_rW1M/edit?usp=sharing"
WHATSAPP_PHONE_NUMBER = "5493516507867"

# --- Funciones para cargar productos ---
def descargar_archivo_drive(url, output):
    """Descarga un archivo de Google Drive usando gdown"""
    try:
        file_id = url.split('/d/')[1].split('/')[0]
        download_url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(download_url, output, quiet=False)
        return True
    except Exception as e:
        st.error(f"Error al descargar el archivo: {e}")
        return False

def cargar_productos_desde_drive():
    """Carga los productos desde Google Drive"""
    try:
        # Descargar el archivo temporalmente
        temp_file = "temp_productos.xlsx"
        if descargar_archivo_drive(GOOGLE_DRIVE_URL, temp_file):
            df = pd.read_excel(temp_file)
            productos = []
            
            for index, row in df.iterrows():
                codigo_alfa = row.get("COD_ALFA")
                detalle = row.get("DETALLE", "")
                precio = row.get("PRECIO")
                stock = row.get("STOCK")
                imagen = row.get("Link")

                if detalle and pd.notna(precio) and pd.notna(stock):
                    productos.append({
                        "nombre": str(detalle).strip(),
                        "precio": float(precio),
                        "stock": int(stock) if pd.notna(stock) else 0,
                        "codigo": str(codigo_alfa).strip() if pd.notna(codigo_alfa) else "",
                        "imagen": str(imagen).strip() if pd.notna(imagen) else None
                    })
            
            # Eliminar el archivo temporal
            os.remove(temp_file)
            st.success(f"✅ Se cargaron {len(productos)} productos desde Google Drive.")
            return productos
        else:
            return []
    except Exception as e:
        st.error(f"⚠️ Error al cargar el archivo desde Google Drive: {e}")
        return []

# --- SESSION STATE ---
if 'productos' not in st.session_state:
    st.session_state.productos = cargar_productos_desde_drive()
elif not st.session_state.productos:
    st.session_state.productos = cargar_productos_desde_drive()

st.title("Promociones Millex")

# --- MODO CLIENTE ---
if not st.session_state.productos:
    st.info("Todavía no hay productos cargados. Vuelve más tarde.")
else:
    st.markdown("### Productos disponibles:")
    cantidades = {}
    productos_disponibles = st.session_state.productos

    # CSS para uniformizar el tamaño de las imágenes y contenedores
    st.markdown("""
    <style>
    .producto-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        padding: 10px;
        border-radius: 10px;
        background: #cecccc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .producto-imagen {
        width: 100%;
        height: 180px;
        object-fit: contain;
        margin-bottom: 10px;
        border-radius: 8px;
        background: white;
        padding: 5px;
    }
    .producto-nombre {
        font-size: 16px;
        font-weight: bold;
        margin: 5px 0;
        color: #000000;
        min-height: 40px;
    }
    .producto-precio {
        font-size: 18px;
        font-weight: bold;
        color: #000000;
        margin: 5px 0;
    }
    .producto-info {
        font-size: 12px;
        color: #000000;
        margin: 2px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Mostrar productos en 3 columnas
    cols = st.columns(3)
    
    for idx, producto in enumerate(productos_disponibles):
        with cols[idx % 3]:
            # Contenedor principal del producto
            st.markdown(f"""
            <div class="producto-container">
                <div style="text-align: center;">
                    {f'<img src="{producto["imagen"]}" class="producto-imagen">' if producto.get("imagen") else '<div class="producto-imagen" style="display: flex; align-items: center; justify-content: center; color: #999;">Imagen no disponible</div>'}
                </div>
                <div class="producto-info">🔖 {producto.get("codigo", "Sin código")}</div>
                <div class="producto-nombre">{producto["nombre"]}</div>
                <div class="producto-precio">${producto["precio"]:.2f}</div>
            """, unsafe_allow_html=True)
            
            # Selector de cantidad
            cantidad = st.number_input(
                "Cantidad",
                min_value=0,
                max_value=producto.get('stock', None) if producto.get('stock') is not None else None,
                step=1,
                key=f"cantidad_{idx}",
                value=0
            )
            st.markdown("</div>", unsafe_allow_html=True)  # Cierre del contenedor
            
            if cantidad > 0:
                cantidades[idx] = cantidad

    st.markdown("---")

    # Sección de pedido
    if cantidades:
        st.markdown("### 🛒 Tu Pedido:")
        total = 0
        pedido_texto = "¡Hola! Quiero hacer el siguiente pedido:\n\n"
        pedido_items = []
        
        for idx, cant in cantidades.items():
            producto = productos_disponibles[idx]
            subtotal = cant * producto["precio"]
            total += subtotal
            item_linea = f"- {cant} x {producto['nombre']} (Código: {producto.get('codigo', 'N/A')}) = ${subtotal:.2f}"
            pedido_items.append(item_linea)
            pedido_texto += item_linea + "\n"

        st.markdown("\n".join(pedido_items))
        st.markdown(f"**Total del Pedido: ${total:.2f}**")
        st.markdown("---")

        st.markdown("### 🧾 Tus datos para el pedido:")
        razon_social = st.text_input("🏢 Razón Social *")
        cuit = st.text_input("🔢 CUIT *")
        nombre_cliente = st.text_input("🧍 Nombre de Contacto *")
        email_cliente = st.text_input("📧 Email de Contacto *")
        direccion_cliente = st.text_area("📍 Dirección de Entrega")
        st.markdown("<span style='font-size: 0.8em; color: gray;'>* Campos obligatorios</span>", unsafe_allow_html=True)

        if razon_social and cuit and nombre_cliente and email_cliente:
            pedido_texto += f"\nRazón Social: {razon_social}"
            pedido_texto += f"\nCUIT: {cuit}"
            pedido_texto += f"\nNombre: {nombre_cliente}"
            pedido_texto += f"\nEmail: {email_cliente}"
            if direccion_cliente:
                pedido_texto += f"\nDirección: {direccion_cliente}"

            if st.button("📲 Enviar Pedido por WhatsApp"):
                mensaje_codificado = urllib.parse.quote(pedido_texto)
                whatsapp_url = f"https://wa.me/{WHATSAPP_PHONE_NUMBER}?text={mensaje_codificado}"
                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank" style="display: inline-block; padding: 12px 20px; background-color: #25D366; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px; margin-top: 10px;">📲 Enviar Pedido por WhatsApp</a>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("⚠️ Por favor, completa todos los campos obligatorios (Razón Social, CUIT, Nombre y Email) para poder generar el mensaje de pedido.")
    else:
        st.info("Seleccioná la cantidad de los productos que deseas comprar.")
