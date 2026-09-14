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
            with st.spinner("Leyendo y filtrando columnas de Clientes..."):
                try:
                    df = pd.read_excel(archivo_clientes, header=None, skiprows=1)
                    
                    # Función para extraer celdas de forma segura evitando errores de índices y NaNs
                    def safe_get(row_idx, col_idx):
                        try:
                            val = df.iloc[row_idx, col_idx]
                            if pd.isna(val) or str(val).strip().lower() in ['nan', 'nat', 'none', '']:
                                return None
                            return str(val).strip()
                        except:
                            return None

                    registros_limpios = []
                    for idx in range(len(df)):
                        codigo = safe_get(idx, 1) # Columna B (Índice 1)
                        if not codigo:
                            continue # Si no tiene código, se ignora la fila
                        
                        row_data = {
                            "codigo": codigo,
                            "razon_social": safe_get(idx, 2),        # C = 2
                            "domicilio": safe_get(idx, 7),           # H = 7
                            "canal": safe_get(idx, 40),              # AO = 40
                            "lista_precios": safe_get(idx, 42),      # AQ = 42
                            "forma_pago": safe_get(idx, 47),         # AV = 47
                            "categoria_impositiva": safe_get(idx, 58), # BG = 58
                            "tipo_documento": safe_get(idx, 60),     # BI = 60
                            "numero_documento": safe_get(idx, 61),    # BJ = 61
                            "vendedor": safe_get(idx, 84),           # CG = 84
                            "dia_visita": safe_get(idx, 85)          # CH = 85
                        }
                        registros_limpios.append(row_data)

                    if len(registros_limpios) > 0:
                        batch_size = 500
                        for i in range(0, len(registros_limpios), batch_size):
                            lote = registros_limpios[i:i + batch_size]
                            supabase.table("clientes").upsert(lote, on_conflict="codigo").execute()
                        st.success(f"¡Sincronización exitosa! Se procesaron {len(registros_limpios)} clientes.")
                    else:
                        st.warning("El archivo Excel no contiene registros válidos.")
                except Exception as e:
                    st.error(f"Error crítico en clientes: {e}")
                    
# --- PESTAÑA 2: PRECIOS Y ATRIBUTOS ---
with tab2:
    st.subheader("Subir Lista de Precios y Atributos")
    tipo_archivo = st.radio("¿Qué archivo vas a subir?", ["Lista de Precios 1 (General)", "Lista Mayorista", "Atributos y Categorías"])
    archivo_precios = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"], key="pre")

    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar"):
            with st.spinner("Procesando datos hacia Supabase..."):
                try:
                    if "Atributos" in tipo_archivo:
                        # Atributos: A=0 (Código), C=2 (División/Categoría)
                        df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                        df_limpio = pd.DataFrame()
                        df_limpio["codigo"] = df[0].astype(str).str.strip()
                        df_limpio["categoria"] = df[2].astype(str).str.strip()
                        
                        invalidos = ['', 'nan', 'None', 'NAT', 'NaN', 'NATVAL']
                        df_limpio = df_limpio[
                            ~df_limpio["codigo"].str.upper().isin(invalidos) &
                            ~df_limpio["categoria"].str.upper().isin(invalidos) &
                            df_limpio["codigo"].notna() &
                            df_limpio["categoria"].notna()
                        ]
                        
                        registros_limpios = df_limpio.to_dict(orient="records")
                        
                        if len(registros_limpios) > 0:
                            for i in range(0, len(registros_limpios), 500):
                                lote = registros_limpios[i:i+500]
                                supabase.table("productos").upsert(lote, on_conflict="codigo").execute()
                            st.success(f"¡Categorías sincronizadas! Se procesaron {len(registros_limpios)} registros válidos.")
                        else:
                            st.warning("El archivo no tiene categorías válidas.")
                    
                    else:
                        # Precios: E=4 (cod), F=5 (desc), J=9 (unidades), P=15 (precio bulto), S=18 (precio unidad)
                        df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                        df_limpio = pd.DataFrame()
                        df_limpio["codigo"] = df[4].astype(str).str.strip()
                        df_limpio["descripcion"] = df[5].astype(str).str.strip()
                        
                        df_limpio["unidades_por_bulto"] = pd.to_numeric(df[9], errors="coerce")
                        
                        precio_bulto_col = "precio_bulto_mayorista" if "Mayorista" in tipo_archivo else "precio_bulto_lista1"
                        precio_unidad_col = "precio_unidad_mayorista" if "Mayorista" in tipo_archivo else "precio_unidad_lista1"
                        
                        df_limpio[precio_bulto_col] = pd.to_numeric(df[15], errors="coerce")
                        df_limpio[precio_unidad_col] = pd.to_numeric(df[18], errors="coerce")
                        
                        df_limpio = df_limpio.replace({'nan': None, 'NaT': None, 'None': None, np.nan: None})
                        df_limpio = df_limpio[df_limpio["codigo"].notna() & (df_limpio["codigo"] != 'None')]
                        
                        registros_limpios = df_limpio.to_dict(orient="records")

                        if len(registros_limpios) > 0:
                            for i in range(0, len(registros_limpios), 500):
                                lote = registros_limpios[i:i+500]
                                supabase.table("productos").upsert(lote, on_conflict="codigo").execute()
                            st.success(f"¡Precios sincronizados ({tipo_archivo})! Procesados {len(registros_limpios)} productos.")
                        else:
                            st.warning("El archivo de precios está vacío o es inválido.")

                except Exception as e:
                    st.error(f"Error crítico: {e}")
                    
# --- PESTAÑA 3: STOCK ---
with tab3:
    st.subheader("Subir Stock Disponible")
    archivo_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx", "xls"], key="stk")

    if archivo_stock is not None:
        if st.button("Procesar y Sincronizar Stock"):
            with st.spinner("Leyendo stock (Col A, C y D)..."):
                try:
                    # Stock: A=0 (Código), C=2 (Bultos), D=3 (Unidades)
                    df = pd.read_excel(archivo_stock, header=None, skiprows=1)
                    
                    df_limpio = pd.DataFrame()
                    df_limpio["codigo"] = df[0].astype(str).str.strip()
                    df_limpio["bultos"] = pd.to_numeric(df[2], errors="coerce").fillna(0)
                    df_limpio["unidades"] = pd.to_numeric(df[3], errors="coerce").fillna(0)

                    df_limpio = df_limpio.drop_duplicates(subset=["codigo"], keep="last")
                    df_limpio = df_limpio[df_limpio["codigo"].notna() & (df_limpio["codigo"] != 'None') & (df_limpio["codigo"] != 'nan')]
                    
                    registros_limpios = df_limpio.to_dict(orient="records")
                    
                    if len(registros_limpios) > 0:
                        batch_size = 500
                        for i in range(0, len(registros_limpios), batch_size):
                            lote = registros_limpios[i:i + batch_size]
                            supabase.table("stock_actual").upsert(lote, on_conflict="codigo").execute()
                            
                        st.success(f"¡Stock actualizado con éxito! Se procesaron {len(registros_limpios)} artículos.")
                    else:
                        st.warning("El archivo de stock está vacío.")
                except Exception as e:
                    st.error(f"Error crítico en stock: {e}")
                    
