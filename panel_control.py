import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODYxNzY0OSwiZXhwIjoyMTA0MTkzNjQ5fQ.wwwdUuXbH7_z2UnP3FhxRrKGWJF3ZCUwcxUseN87R-I"

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
            with st.spinner("Leyendo y filtrando columnas de Clientes por posición..."):
                try:
                    # header=None asigna números (0, 1, 2...) a las columnas. skiprows=1 ignora la fila 1.
                    df = pd.read_excel(archivo_clientes, header=None, skiprows=1)
                    
                    df_limpio = pd.DataFrame()
                    
                    # Mapeo de columnas: A=0, B=1, C=2, H=7, AO=40, AQ=42, AV=47, BG=58, BI=60, BJ=61, CG=84, CH=85
                    df_limpio["codigo"] = df[1].astype(str).str.strip()               # B
                    df_limpio["razon_social"] = df[2].astype(str).str.strip()         # C
                    df_limpio["domicilio"] = df[7].astype(str).str.strip()            # H
                    df_limpio["canal"] = df[40].astype(str).str.strip()               # AO
                    df_limpio["lista_precios"] = df[42].astype(str).str.strip()       # AQ
                    df_limpio["forma_pago"] = df[47].astype(str).str.strip()          # AV
                    df_limpio["categoria_impositiva"] = df[58].astype(str).str.strip()# BG
                    df_limpio["tipo_documento"] = df[60].astype(str).str.strip()      # BI
                    df_limpio["numero_documento"] = df[61].astype(str).str.strip()    # BJ
                    df_limpio["vendedor"] = df[84].astype(str).str.strip()            # CG
                    df_limpio["dia_visita"] = df[85].astype(str).str.strip()          # CH
                    
                    # Limpieza de nulos
                    invalidos = ['nan', 'None', 'NaT', '']
                    df_limpio = df_limpio.replace(invalidos, None)
                    
                    # Filtrar filas vacías donde el código sea nulo
                    df_limpio = df_limpio[df_limpio["codigo"].notna()]
                    
                    registros = df_limpio.to_dict(orient="records")
                    
                    # Insertar en Supabase
                    if len(registros) > 0:
                        with st.spinner("Subiendo clientes a Supabase..."):
                            batch_size = 500
                            for i in range(0, len(registros), batch_size):
                                lote = registros[i:i + batch_size]
                                supabase.table("clientes").upsert(lote, on_conflict="codigo").execute()
                            
                        st.success(f"¡Sincronización exitosa! Se procesaron {len(registros)} clientes.")
                    else:
                        st.warning("El archivo Excel no contiene registros válidos.")
                except Exception as e:
                    st.error(f"Error crítico en clientes: {e}")
                    
# --- PESTAÑA 2: PRECIOS Y ATRIBUTOS ---
with tab2:
    st.subheader("Subir Lista de Precios y Atributos")
    tipo_archivo = st.radio("¿Qué archivo vas a subir?", ["Lista de Precios 1 (General)", "Lista Mayorista", "Atributos y Categorías"])
    archivo_precios = st.file_uploader("Selecciona el archivo Excel/Tabular", type=["xlsx", "xls"], key="pre")

    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar"):
            with st.spinner("Procesando datos hacia Supabase..."):
                try:
                    if "Atributos" in tipo_archivo:
                        df = pd.read_csv(archivo_precios, sep='\t', encoding='latin-1')
                        df_limpio = pd.DataFrame()
                        df_limpio["codigo"] = df["CODIGO ARTICULO"].astype(str).str.strip()
                        df_limpio["categoria"] = df["DIVISION (DIVISION)"].astype(str).str.strip()
                        
                        # Lista de valores inválidos o vacíos a ignorar
                        invalidos = ['', 'nan', 'None', 'NAT', 'NaN', 'NATVAL']
                        
                        # Filtrar estrictamente filas que tengan código y categoría válidos
                        df_limpio = df_limpio[
                            ~df_limpio["codigo"].str.upper().isin(invalidos) &
                            ~df_limpio["categoria"].str.upper().isin(invalidos) &
                            df_limpio["codigo"].notna() &
                            df_limpio["categoria"].notna()
                        ]
                        
                        registros = df_limpio.to_dict(orient="records")
                        
                        registros_limpios = []
                        for row in registros:
                            new_row = {}
                            for k, v in row.items():
                                if pd.isna(v) or str(v).strip().lower() in ['nan', 'none', '']:
                                    new_row[k] = None
                                else:
                                    new_row[k] = str(v).strip()
                            registros_limpios.append(new_row)

                        for i in range(0, len(registros_limpios), 500):
                            lote = registros_limpios[i:i+500]
                            supabase.table("productos").upsert(lote, on_conflict="codigo").execute()
                            
                        st.success(f"¡Categorías sincronizadas con éxito! Se procesaron {len(registros_limpios)} registros válidos (se ignoraron los espacios en blanco).")
                    
                    else:
                        df = pd.read_excel(archivo_precios)
                        df_limpio = pd.DataFrame()
                        df_limpio["codigo"] = df["Artículo"].astype(str)
                        df_limpio["descripcion"] = df["Descripción.1"].astype(str)
                        
                        precio_col = "precio_final_mayorista" if "Mayorista" in tipo_archivo else "precio_final_lista1"
                        df_limpio[precio_col] = pd.to_numeric(df["Precio Final"], errors="coerce")
                        df_limpio["precio_unitario"] = pd.to_numeric(df["P.Unitario Final"], errors="coerce")
                        
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
                            for i in range(0, len(registros_limpios), 500):
                                lote = registros_limpios[i:i+500]
                                supabase.table("productos").upsert(lote, on_conflict="codigo").execute()
                            st.success(f"¡Precios sincronizados con éxito ({tipo_archivo})! Se procesaron {len(registros_limpios)} productos.")
                        else:
                            st.warning("El archivo de precios está vacío.")

                except Exception as e:
                    st.error(f"Error crítico: {e}")
                    
# --- PESTAÑA 3: STOCK ---
with tab3:
    st.subheader("Subir Stock Disponible")
    archivo_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx", "xls"], key="stk")

    if archivo_stock is not None:
        if st.button("Procesar y Sincronizar Stock"):
            with st.spinner("Leyendo stock y presentaciones..."):
                try:
                    df = pd.read_excel(archivo_stock)
                    
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df["Código Artículo"].astype(str)
                    df_limpio["descripcion"] = df["Descripción"].astype(str)
                    df_limpio["bultos"] = pd.to_numeric(df["Bultos"], errors="coerce")
                    df_limpio["unidades"] = pd.to_numeric(df["Unidades"], errors="coerce")
                    df_limpio["presentacion_bulto"] = df["Presentación Bulto"].astype(str)
                    df_limpio["presentacion_unidad"] = df["Presentación Unidad"].astype(str)

                    df_limpio = df_limpio.drop_duplicates(subset=["codigo"], keep="last")
                    
                    df_limpio = df_limpio.replace({np.nan: None, 'nan': None, 'NaT': None, 'None': 'nan'})
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
                            supabase.table("stock_actual").upsert(lote, on_conflict="codigo").execute()
                            
                        st.success(f"¡Stock actualizado con éxito! Se procesaron {len(registros_limpios)} registros.")
                    else:
                        st.warning("El archivo de stock está vacío.")
                except Exception as e:
                    st.error(f"Error crítico en stock: {e}")
