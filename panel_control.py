import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
import time

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODYxNzY0OSwiZXhwIjoyMTA0MTkzNjQ5fQ.wwwdUuXbH7_z2UnP3FhxRrKGWJF3ZCUwcxUseN87R-I"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Panel de Control DistriOks", page_icon="🔄", layout="centered")

st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Gestión inteligente y sincronización masiva hacia Supabase.</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible", "Promociones"])

# --- PESTAÑA 1: CLIENTES ---
with tab1:
    st.subheader("Subir Plantilla de Clientes")
    archivo_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx", "xls"], key="cli")

    if archivo_clientes is not None:
        if st.button("Procesar y Sincronizar Clientes"):
            with st.spinner("Leyendo y filtrando columnas de Clientes..."):
                try:
                    df = pd.read_excel(archivo_clientes, header=None, skiprows=1)
                    
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
                        codigo = safe_get(idx, 1)
                        if not codigo:
                            continue
                        
                        row_data = {
                            "codigo": codigo,
                            "razon_social": safe_get(idx, 2),
                            "domicilio": safe_get(idx, 7),
                            "canal": safe_get(idx, 40),
                            "lista_precios": safe_get(idx, 42),
                            "forma_pago": safe_get(idx, 47),
                            "categoria_impositiva": safe_get(idx, 58),
                            "tipo_documento": safe_get(idx, 60),
                            "numero_documento": safe_get(idx, 61),
                            "vendedor": safe_get(idx, 84),
                            "dia_visita": safe_get(idx, 85)
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
    archivo_precios = st.file_uploader("Selecciona el archivo Excel/Tabular", type=["xlsx", "xls", "txt", "csv"], key="pre")

    if archivo_precios is not None:
        if st.button("Procesar y Sincronizar"):
            with st.spinner("Procesando datos hacia Supabase..."):
                try:
                    if "Atributos" in tipo_archivo:
                        try:
                            df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                        except:
                            archivo_precios.seek(0)
                            df = pd.read_csv(archivo_precios, sep=None, engine='python', header=None, skiprows=1, encoding='latin-1')

                        def safe_get_attr(row_idx, col_idx):
                            try:
                                val = df.iloc[row_idx, col_idx]
                                if pd.isna(val) or str(val).strip().lower() in ['nan', 'nat', 'none', '']:
                                    return None
                                return str(val).strip()
                            except:
                                return None

                        registros_limpios = []
                        invalidos = ['', 'nan', 'none', 'nat', 'natval', 'NaN']
                        
                        for idx in range(len(df)):
                            codigo = safe_get_attr(idx, 0)
                            categoria = safe_get_attr(idx, 2)
                            
                            if not codigo or not categoria:
                                continue
                            if codigo.lower() in invalidos or categoria.lower() in invalidos:
                                continue
                                
                            registros_limpios.append({
                                "codigo": codigo,
                                "categoria": categoria
                            })
                        
                        if len(registros_limpios) > 0:
                            for i in range(0, len(registros_limpios), 500):
                                lote = registros_limpios[i:i+500]
                                supabase.table("productos").upsert(lote, on_conflict="codigo").execute()
                            st.success(f"¡Categorías sincronizadas! Se procesaron {len(registros_limpios)} registros válidos.")
                        else:
                            st.warning("El archivo no tiene categorías válidas.")
                    
                    else:
                        df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                        
                        def safe_get_precio(row_idx, col_idx):
                            try:
                                val = df.iloc[row_idx, col_idx]
                                if pd.isna(val) or str(val).strip().lower() in ['nan', 'nat', 'none', '']:
                                    return None
                                return val
                            except:
                                return None

                        registros_limpios = []
                        for idx in range(len(df)):
                            codigo = safe_get_precio(idx, 4)
                            if not codigo or str(codigo).strip().lower() in ['nan', 'none', '']:
                                continue
                                
                            desc = safe_get_precio(idx, 5)
                            unidades_bulto = safe_get_precio(idx, 9)
                            
                            precio_bulto_idx = 15
                            precio_unidad_idx = 18
                            
                            precio_bulto_col = "precio_bulto_mayorista" if "Mayorista" in tipo_archivo else "precio_bulto_lista1"
                            precio_unidad_col = "precio_unidad_mayorista" if "Mayorista" in tipo_archivo else "precio_unidad_lista1"
                            
                            row_data = {
                                "codigo": str(codigo).strip(),
                                "descripcion": str(desc).strip() if desc is not None else None,
                                "unidades_por_bulto": float(unidades_bulto) if unidades_bulto is not None else None,
                                precio_bulto_col: float(safe_get_precio(idx, precio_bulto_idx)) if safe_get_precio(idx, precio_bulto_idx) is not None else None,
                                precio_unidad_col: float(safe_get_precio(idx, precio_unidad_idx)) if safe_get_precio(idx, precio_unidad_idx) is not None else None,
                            }
                            registros_limpios.append(row_data)

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

# --- PESTAÑA 4: PROMOCIONES ---
with tab4:
    st.subheader("Subir Novedades y Promociones")
    st.write("Sube imágenes para que aparezcan en la pantalla principal de la app.")

    # accept_multiple_files=True permite seleccionar varias fotos a la vez
    archivos_imagenes = st.file_uploader("Selecciona imágenes (JPG o PNG)", type=['jpg', 'jpeg', 'png'], key="promo", accept_multiple_files=True)

    if st.button("Subir Promociones"):
        if archivos_imagenes and len(archivos_imagenes) > 0:
            with st.spinner(f"Subiendo {len(archivos_imagenes)} imágenes a la nube..."):
                exitos = 0
                for archivo in archivos_imagenes:
                    try:
                        bytes_data = archivo.getvalue()
                        nombre_unico = f"{int(time.time())}_{archivo.name}"

                        # Subir físicamente a Supabase (CORREGIDO A MAYÚSCULAS: 'PROMOS')
                        supabase.storage.from_('PROMOS').upload(
                            file=bytes_data,
                            path=nombre_unico,
                            file_options={"content-type": archivo.type}
                        )

                        # Obtener link público (CORREGIDO A MAYÚSCULAS: 'PROMOS')
                        url_publica = supabase.storage.from_('PROMOS').get_public_url(nombre_unico)

                        # Guardar link en la tabla 'promociones'
                        supabase.table('promociones').insert({"imagen_url": url_publica}).execute()
                        
                        exitos += 1
                        st.image(url_publica, width=150, caption=f"Subida: {archivo.name}")

                    except Exception as e:
                        st.error(f"Error al subir {archivo.name}: {e}")
                
                if exitos > 0:
                    st.success(f"¡{exitos} promociones subidas con éxito! Ya deberían aparecer en la App.")
        else:
            st.warning("Por favor, selecciona al menos una imagen primero.")
