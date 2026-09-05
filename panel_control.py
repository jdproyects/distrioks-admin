import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg2MTc2NDksImV4cCI6MjEwNDE5MzY0OX0.Gcsubn2IhWsnnXW0El02PZnTIjeRzlVds5peqMoBUPw"  # <--- REEMPLAZA CON TU CLAVE REAL

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Panel de Control DistriOks", page_icon="🔄", layout="centered")

st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Sincronización inteligente de clientes desde Chess hacia Supabase.</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible"])

# --- PESTAÑA 1: CLIENTES ---
with tab1:
    st.subheader("Subir Plantilla de Clientes")
    archivo_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx", "xls"], key="cli")

    if archivo_clientes is not None:
        if st.button("Procesar y Sincronizar Clientes"):
            with st.spinner("Leyendo y filtrando columnas de Chess..."):
                try:
                    df = pd.read_excel(archivo_clientes)
                    
                    # 1. Creamos un DataFrame limpio solo con las columnas que necesitas del Excel
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df["Cliente"].astype(str)
                    df_limpio["razon_social"] = df["Razón social"].astype(str)
                    df_limpio["calle"] = df["Calle"].astype(str)
                    df_limpio["altura"] = df["Altura"].astype(str)
                    df_limpio["categoria"] = df["Categoria"].astype(str)
                    df_limpio["identificador"] = df["Identificador"].astype(str)
                    df_limpio["ruta_venta"] = df["Descripción Ruta Vta."].astype(str)
                    
                    # 2. Limpieza general de nulos o valores extraños para Supabase
                    df_limpio = df_limpio.replace({'nan': None, 'NaT': None, 'None': None})
                    df_limpio = df_limpio.where(pd.notnull(df_limpio), None)
                    
                    registros = df_limpio.to_dict(orient="records")
                    
                    if len(registros) > 0:
                        with st.spinner("Subiendo registros limpios a Supabase..."):
                            batch_size = 500
                            for i in range(0, len(registros), batch_size):
                                lote = registros[i:i + batch_size]
                                supabase.table("clientes").upsert(lote).execute()
                                
                        st.success(f"¡Sincronización exitosa! Se procesaron y guardaron {len(registros)} clientes perfectamente.")
                    else:
                        st.warning("El archivo Excel no contiene registros válidos.")
                except Exception as e:
                    st.error(f"Error crítico en el proceso: {e}")

# --- PESTAÑA 2: PRECIOS ---
with tab2:
    st.subheader("Subir Lista de Precios")
    archivo_precios = st.file_uploader("Selecciona el archivo Excel de Precios", type=["xlsx", "xls"], key="pre")
    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar Precios"):
            st.info("Módulo de precios listo para cuando cargues tu archivo.")

# --- PESTAÑA 3: STOCK ---
with tab3:
    st.subheader("Subir Stock Disponible")
    archivo_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx", "xls"], key="stk")
    if archivo_stock is not None:
        if st.button("Procesar y Sincronizar Stock"):
            st.info("Módulo de stock listo para cuando cargues tu archivo.")
