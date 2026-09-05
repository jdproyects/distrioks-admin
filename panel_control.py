import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg2MTc2NDksImV4cCI6MjEwNDE5MzY0OX0.Gcsubn2IhWsnnXW0El02PZnTIjeRzlVds5peqMoBUPw"  # Asegúrate de poner tu clave real aquí

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Panel de Control DistriOks", page_icon="🔄", layout="centered")

st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Gestión optimizada y rápida de sincronización masiva.</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible"])

# --- PESTAÑA 1: CLIENTES ---
with tab1:
    st.subheader("Subir Plantilla de Clientes")
    archivo_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx", "xls"], key="cli")

    if archivo_clientes is not None:
        if st.button("Procesar y Sincronizar Clientes Rápidamente"):
            with st.spinner("Leyendo y filtrando datos limpios..."):
                try:
                    # skiprows=... salta las filas de título feas de Chess si las hubiera
                    df = pd.read_excel(archivo_clientes)
                    
                    # AQUÍ FILTRAMOS: Selecciona solo las columnas que SÍ existen en tu tabla de Supabase
                    # (Asegúrate de que estos nombres coincidan exactamente con las columnas de tu base de datos)
                    columnas_deseadas = ["codigo_cliente", "razon_social", "condicion_fiscal", "direccion", "vendedor_asignado", "dia_visita"] # <--- Cambia estos nombres por los reales de tus columnas
                    
                    # Si el Excel tiene otros nombres, filtramos para que solo tome las que nos interesan
                    df = df[[col for col in columnas_deseadas if col in df.columns]]
                    
                    df = df.astype(str).replace({'nan': None, 'NaT': None})
                    df = df.where(pd.notnull(df), None)
                    
                    registros = df.to_dict(orient="records")
                    
                    if len(registros) > 0:
                        with st.spinner("Sincronizando con Supabase..."):
                            batch_size = 500
                            for i in range(0, len(registros), batch_size):
                                lote = registros[i:i + batch_size]
                                supabase.table("clientes").upsert(lote).execute()
                                
                        st.success(f"¡Sincronización exitosa! Se procesaron {len(registros)} clientes.")
                    else:
                        st.warning("No se encontraron datos válidos con las columnas especificadas.")
                except Exception as e:
                    st.error(f"Error crítico en el proceso: {e}")
                    
# --- PESTAÑA 2: PRECIOS ---
with tab2:
    st.subheader("Subir Lista de Precios")
    archivo_precios = st.file_uploader("Selecciona el archivo Excel de Precios", type=["xlsx", "xls"], key="pre")

    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar Precios Rápidamente"):
            with st.spinner("Procesando lista de precios..."):
                try:
                    df = pd.read_excel(archivo_precios)
                    # --- NUEVA LÍNEA PARA CONVERTIR FECHAS A TEXTO ---
                    df = df.astype(str).replace({'nan': None, 'NaT': None})
                    df = df.where(pd.notnull(df), None)
                    registros = df.to_dict(orient="records")
                    
                    if len(registros) > 0:
                        batch_size = 500
                        for i in range(0, len(registros), batch_size):
                            lote = registros[i:i + batch_size]
                            supabase.table("productos").upsert(lote).execute()
                            
                        st.success(f"¡Precios actualizados! Se procesaron {len(registros)} registros.")
                    else:
                        st.warning("El archivo de precios está vacío.")
                except Exception as e:
                    st.error(f"Error crítico: {e}")

# --- PESTAÑA 3: STOCK ---
with tab3:
    st.subheader("Subir Stock Disponible")
    archivo_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx", "xls"], key="stk")

    if archivo_stock is not None:
        if st.button("Procesar y Sincronizar Stock Rápidamente"):
            with st.spinner("Actualizando stock..."):
                try:
                    df = pd.read_excel(archivo_stock)
                    # --- NUEVA LÍNEA PARA CONVERTIR FECHAS A TEXTO ---
                    df = df.astype(str).replace({'nan': None, 'NaT': None})
                    df = df.where(pd.notnull(df), None)
                    registros = df.to_dict(orient="records")
                    
                    if len(registros) > 0:
                        batch_size = 500
                        for i in range(0, len(registros), batch_size):
                            lote = registros[i:i + batch_size]
                            supabase.table("stock_actual").upsert(lote).execute()
                            
                        st.success(f"¡Stock actualizado! Se procesaron {len(registros)} registros.")
                    else:
                        st.warning("El archivo de stock está vacío.")
                except Exception as e:
                    st.error(f"Error crítico: {e}")
