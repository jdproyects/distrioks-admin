import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg2MTc2NDksImV4cCI6MjEwNDE5MzY0OX0.Gcsubn2IhWsnnXW0El02PZnTIjeRzlVds5peqMoBUPw"  # <--- REEMPLAZA CON TU CLAVE REAL

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Panel de Control DistriOks", page_icon="🔄", layout="centered")

st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Gestión inteligente y sincronización masiva hacia Supabase.</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible"])

# --- PESTAÑA 1: CLIENTES ---
with tab1:
    st.subheader("Subir Plantilla de Clientes")
    archivo_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx", "xls"], key="cli")

    if archivo_clientes is not None:
        if st.button("Procesar y Sincronizar Clientes"):
            with st.spinner("Leyendo y filtrando columnas de Clientes..."):
                try:
                    df = pd.read_excel(archivo_clientes)
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df["Cliente"].astype(str)
                    df_limpio["razon_social"] = df["Razón social"].astype(str)
                    df_limpio["calle"] = df["Calle"].astype(str)
                    df_limpio["altura"] = df["Altura"].astype(str)
                    df_limpio["categoria"] = df["Categoria"].astype(str)
                    df_limpio["identificador"] = df["Identificador"].astype(str)
                    df_limpio["ruta_venta"] = df["Descripción Ruta Vta."].astype(str)
                    
                    df_limpio = df_limpio.replace({np.nan: None, 'nan': None, 'NaT': None, 'None': None})
                    registros = df_limpio.to_dict(orient="records")
                    
                    registros_limpios = []
                    for row in registros:
                        new_row = {}
                        for k, v in row.items():
                            if pd.isna(v) or v in ['nan', 'NaT', 'None', '']:
                                new_row[k] = None
                            else:
                                new_row[k] = v
                        registros_limpios.append(new_row)
                    
                    if len(registros_limpios) > 0:
                        with st.spinner("Subiendo clientes a Supabase..."):
                            batch_size = 500
                            for i in range(0, len(registros_limpios), batch_size):
                                lote = registros_limpios[i:i + batch_size]
                                supabase.table("clientes").upsert(lote).execute()
                                
                        st.success(f"¡Sincronización exitosa! Se procesaron {len(registros_limpios)} clientes.")
                    else:
                        st.warning("El archivo Excel no contiene registros válidos.")
                except Exception as e:
                    st.error(f"Error crítico en clientes: {e}")

# --- PESTAÑA 2: PRECIOS ---
with tab2:
    st.subheader("Subir Lista de Precios")
    archivo_precios = st.file_uploader("Selecciona el archivo Excel de Precios", type=["xlsx", "xls"], key="pre")

    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar Precios"):
            with st.spinner("Procesando y filtrando lista de precios..."):
                try:
                    df = pd.read_excel(archivo_precios)
                    
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df["Artículo"].astype(str)
                    df_limpio["descripcion"] = df["Descripción.1"].astype(str)
                    df_limpio["precio_final"] = pd.to_numeric(df["Precio Final"], errors="coerce")
                    
                    df_limpio = df_limpio.replace({np.nan: None, 'nan': None, 'NaT': None, 'None': None})
                    registros = df_limpio.to_dict(orient="records")
                    
                    registros_limpios = []
                    for row in registros:
                        new_row = {}
                        for k, v in row.items():
                            if pd.isna(v) or v in ['nan', 'NaT', 'None', '']:
                                new_row[k] = None
                            else:
                                new_row[k] = v
                        registros_limpios.append(new_row)
                    
                    if len(registros_limpios) > 0:
                        batch_size = 500
                        for i in range(0, len(registros_limpios), batch_size):
                            lote = registros_limpios[i:i + batch_size]
                            supabase.table("productos").upsert(lote).execute()
                            
                        st.success(f"¡Precios sincronizados con éxito! Se procesaron {len(registros_limpios)} productos.")
                    else:
                        st.warning("El archivo de precios está vacío.")
                except Exception as e:
                    st.error(f"Error crítico en precios: {e}")
                    
# --- PESTAÑA 3: STOCK ---
with tab3:
    st.subheader("Subir Stock Disponible")
    archivo_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx", "xls"], key="stk")

    if archivo_stock is not None:
        if st.button("Procesar y Sincronizar Stock"):
            with st.spinner("Leyendo las primeras 3 columnas del stock..."):
                try:
                    df = pd.read_excel(archivo_stock)
                    
                    # Seleccionamos estrictamente las primeras 3 columnas por su posición índice (0, 1 y 2)
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df.iloc[:, 0].astype(str)
                    df_limpio["descripcion"] = df.iloc[:, 1].astype(str)
                    df_limpio["bultos"] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
                    
                    df_limpio = df_limpio.replace({np.nan: None, 'nan': None, 'NaT': None, 'None': None})
                    registros = df_limpio.to_dict(orient="records")
                    
                    registros_limpios = []
                    for row in registros:
                        new_row = {}
                        for k, v in row.items():
                            if pd.isna(v) or v in ['nan', 'NaT', 'None', '']:
                                new_row[k] = None
                            else:
                                new_row[k] = v
                        registros_limpios.append(new_row)
                    
                    if len(registros_limpios) > 0:
                        batch_size = 500
                        for i in range(0, len(registros_limpios), batch_size):
                            lote = registros_limpios[i:i + batch_size]
                            supabase.table("stock_actual").upsert(lote).execute()
                            
                        st.success(f"¡Stock actualizado con éxito! Se procesaron {len(registros_limpios)} registros.")
                    else:
                        st.warning("El archivo de stock está vacío.")
                except Exception as e:
                    st.error(f"Error crítico en stock: {e}")
                    
