import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
import time

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODYxNzY0OSwiZXhwIjoyMTA0MTkzNjQ5fQ.wwwdUuXbH7_z2UnP3FhxRrKGWJF3ZCUwcxUseN87R-I"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Panel de Control DistriOks", page_icon="🏢", layout="wide")

# ==========================================
# MENÚ LATERAL (SIDEBAR)
# ==========================================
st.sidebar.title("DistriOks ERP")
st.sidebar.write("Panel de Administración")
st.sidebar.divider()

menu = st.sidebar.radio(
    "Menú Principal",
    ["📦 Gestión de Pedidos", "📊 Dashboard (Estadísticas)", "⚙️ Sincronización Chess"]
)

# ==========================================
# PANTALLA 1: GESTIÓN DE PEDIDOS
# ==========================================
# ==========================================
# PANTALLA 1: GESTIÓN DE PEDIDOS (TIPO CHESS ERP)
# ==========================================
if menu == "📦 Gestión de Pedidos":
    st.title("📦 Controles y Ajustes de Pedidos")
    
    # 1. Obtener pedidos desde Supabase
    res_pedidos = supabase.table('pedidos').select('*').order('created_at', desc=True).execute()
    pedidos_raw = res_pedidos.data
    
    if not pedidos_raw:
        st.info("No hay pedidos registrados en la base de datos.")
    else:
        # 2. Obtener clientes para cruzar el vendedor y la razón social
        res_clientes = supabase.table('clientes').select('codigo, razon_social, vendedor').execute()
        dict_clientes = {str(c['codigo']): c for c in res_clientes.data}

        # 3. Preparar el DataFrame principal
        for p in pedidos_raw:
            # Extraer fecha limpia (YYYY-MM-DD)
            p['Fecha'] = str(p.get('created_at', ''))[:10]
            # Cruzar datos del cliente
            cod_cliente = str(p.get('cliente_codigo', ''))
            datos_cli = dict_clientes.get(cod_cliente, {})
            p['Cliente'] = f"{cod_cliente} - {datos_cli.get('razon_social', 'Desconocido')}"
            p['Vendedor'] = datos_cli.get('vendedor', 'Sin Vendedor Asignado')
            
            # Calcular bultos y unidades totales del pedido
            bultos_totales = 0
            unidades_totales = 0
            for item in p.get('items', []):
                cant = float(item.get('cantidad', 0))
                if str(item.get('tipo', '')).lower() == 'bulto':
                    bultos_totales += cant
                else:
                    unidades_totales += cant
            
            p['Bultos'] = bultos_totales
            p['Unidades'] = unidades_totales
            p['Final'] = float(p.get('total', 0))

        df_pedidos = pd.DataFrame(pedidos_raw)

        # ---------------------------------------------------------
        # BREADCRUMBS Y FILTROS EN CASCADA (TIPO CHESS)
        # ---------------------------------------------------------
        col1, col2, col3 = st.columns(3)
        
        # Nivel 1: Filtro por Fecha
        fechas_disponibles = sorted(df_pedidos['Fecha'].unique(), reverse=True)
        with col1:
            fecha_sel = st.selectbox("📅 1) Fecha", ["Todas las Fechas"] + list(fechas_disponibles))
        
        # Filtrar DF por fecha
        if fecha_sel != "Todas las Fechas":
            df_pedidos = df_pedidos[df_pedidos['Fecha'] == fecha_sel]
            
        # Nivel 2: Filtro por Vendedor
        vendedores_disponibles = sorted(df_pedidos['Vendedor'].unique())
        with col2:
            vendedor_sel = st.selectbox("👤 2) Vendedor", ["Todos los Vendedores"] + list(vendedores_disponibles))
            
        # Filtrar DF por vendedor
        if vendedor_sel != "Todos los Vendedores":
            df_pedidos = df_pedidos[df_pedidos['Vendedor'] == vendedor_sel]
            
        # Nivel 3: Seleccionar Cliente/Pedido específico para ver detalle
        with col3:
            # Crear lista para el selector final
            opciones_pedido = ["Seleccione un pedido para ver el detalle..."]
            for idx, row in df_pedidos.iterrows():
                opciones_pedido.append(f"Ped #{row['id']} | {row['Cliente']} | {row['estado']}")
                
            pedido_sel_str = st.selectbox("🛒 3) Pedido / Cliente", opciones_pedido)

        st.divider()

        # ---------------------------------------------------------
        # VISTA DE RESUMEN (Grilla similar a Chess)
        # ---------------------------------------------------------
        if pedido_sel_str == "Seleccione un pedido para ver el detalle...":
            st.subheader(f"Resumen de Subtotales")
            
            # Agrupar dependiendo de los filtros seleccionados
            if fecha_sel == "Todas las Fechas":
                agrupado = df_pedidos.groupby('Fecha').agg({
                    'id': 'count', 
                    'Bultos': 'sum', 
                    'Unidades': 'sum', 
                    'Final': 'sum'
                }).reset_index()
                agrupado.rename(columns={'id': 'Cant. Pedidos', 'Fecha': 'Selección'}, inplace=True)
                
            elif vendedor_sel == "Todos los Vendedores":
                agrupado = df_pedidos.groupby('Vendedor').agg({
                    'id': 'count', 
                    'Bultos': 'sum', 
                    'Unidades': 'sum', 
                    'Final': 'sum'
                }).reset_index()
                agrupado.rename(columns={'id': 'Cant. Pedidos', 'Vendedor': 'Selección'}, inplace=True)
                
            else:
                # Mostrar lista de clientes si ya seleccionó fecha y vendedor
                agrupado = df_pedidos[['Cliente', 'id', 'Bultos', 'Unidades', 'Final', 'estado']].copy()
                agrupado.rename(columns={'id': 'Pedido #', 'Cliente': 'Selección', 'estado': 'Estado'}, inplace=True)

            # Fila de Totales Generales
            totales = pd.DataFrame([{
                'Selección': 'TOTALES',
                'Cant. Pedidos' if 'Cant. Pedidos' in agrupado.columns else 'Pedido #': len(df_pedidos),
                'Bultos': df_pedidos['Bultos'].sum(),
                'Unidades': df_pedidos['Unidades'].sum(),
                'Final': df_pedidos['Final'].sum()
            }])
            
            agrupado_final = pd.concat([agrupado, totales], ignore_index=True)
            
            # Formatear montos para la tabla visual
            agrupado_final['Final'] = agrupado_final['Final'].apply(lambda x: f"$ {x:,.2f}" if pd.notnull(x) else "")
            
            st.dataframe(agrupado_final, use_container_width=True, hide_index=True)

        # ---------------------------------------------------------
        # VISTA DE DETALLE DE PEDIDO Y ACCIONES
        # ---------------------------------------------------------
        else:
            # Extraer el ID del string seleccionado (ej: "Ped #15 | 123 - JUAN | En Preparación")
            id_seleccionado = int(pedido_sel_str.split('|')[0].replace("Ped #", "").strip())
            pedido_actual = df_pedidos[df_pedidos['id'] == id_seleccionado].iloc[0].to_dict()
            
            col_izq, col_der = st.columns([2, 1])
            
            with col_izq:
                st.markdown(f"### 📄 Detalle Pedido #{pedido_actual['id']}")
                st.write(f"**Cliente:** {pedido_actual['Cliente']}")
                st.write(f"**Vendedor:** {pedido_actual['Vendedor']}")
                st.write(f"**Fecha Solicitada:** {pedido_actual.get('fecha_entrega', 'No especificada')}")
                
                # Tabla de Items
                items = pedido_actual.get('items', [])
                if items:
                    df_items = pd.DataFrame(items)
                    if 'precio' in df_items.columns and 'cantidad' in df_items.columns:
                        df_items['subtotal'] = df_items['precio'] * df_items['cantidad']
                        # Formatear a moneda
                        df_items['precio'] = df_items['precio'].apply(lambda x: f"$ {x:,.2f}")
                        df_items['subtotal'] = df_items['subtotal'].apply(lambda x: f"$ {x:,.2f}")
                    st.dataframe(df_items, use_container_width=True, hide_index=True)
                
                st.markdown(f"## TOTAL FINAL: $ {pedido_actual['Final']:,.2f}")
                st.info("💡 Para imprimir este pedido, presiona **Ctrl + P**.")

            with col_der:
                st.markdown("### ⚙️ Acciones")
                
                # --- CAMBIO DE ESTADO ---
                estado_actual = pedido_actual.get('estado', 'En Preparación')
                lista_estados = ['En Preparación', 'En Reparto', 'Entregado', 'Cancelado', 'Rechazado']
                idx_estado = lista_estados.index(estado_actual) if estado_actual in lista_estados else 0
                
                nuevo_estado = st.selectbox("Estado del pedido:", lista_estados, index=idx_estado)
                if st.button("Guardar Estado", type="primary", use_container_width=True):
                    try:
                        supabase.table('pedidos').update({'estado': nuevo_estado}).eq('id', pedido_actual['id']).execute()
                        st.success(f"Estado actualizado a '{nuevo_estado}'")
                        time.sleep(1) # Pequeña pausa para que se vea el mensaje
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
# ==========================================
# PANTALLA 2: DASHBOARD
# ==========================================
elif menu == "📊 Dashboard (Estadísticas)":
    st.title("📊 Estadísticas y Gráficos")
    st.info("Aquí construiremos el panel estadístico tipo Nextbyn (ventas, curvas, top clientes) en la siguiente etapa.")

# ==========================================
# PANTALLA 3: CARGA DE DATOS
# ==========================================
elif menu == "⚙️ Sincronización Chess":
    st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Gestión inteligente y sincronización masiva hacia Supabase.</p>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible", "Promociones", "Sincronizar Reglas de Descuento por Lote/Marca"])

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

                            # Subir físicamente a Supabase
                            supabase.storage.from_('PROMOS').upload(
                                file=bytes_data,
                                path=nombre_unico,
                                file_options={"content-type": archivo.type}
                            )

                            # Obtener link público
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

    # --- PESTAÑA 5: REGLAS DE DESCUENTO ---
    with tab5:
        st.subheader("Sincronizar Reglas de Descuento por Lote/Marca")
        st.markdown("""
        Sube un archivo Excel con las siguientes columnas exactas:
        1. **tipo_regla** (Ej: `UN_CODIGO`, `MARCA`, `COMBINADOS`)
        2. **filtro** (Ej: `930`, `TRIO`, o códigos separados por coma `801,805,810`)
        3. **cantidad_minima** (Número mínimo de unidades/bultos para activar)
        4. **porcentaje_descuento** (Ej: `16.2` o `6.0`)
        5. **nombre_promo** (Texto descriptivo que verá el cliente)
        """)

        archivo_descuentos = st.file_uploader("Selecciona el Excel de Descuentos", type=["xlsx", "xls"], key="desc")

        if archivo_descuentos is not None:
            if st.button("Procesar y Sincronizar Descuentos"):
                with st.spinner("Leyendo reglas de descuento..."):
                    try:
                        df_desc = pd.read_excel(archivo_descuentos)
                        
                        reglas_limpias = []
                        for idx, row in df_desc.iterrows():
                            tipo = str(row.get('tipo_regla', '')).strip().upper()
                            filtro = str(row.get('filtro', '')).strip()
                            cant_min = row.get('cantidad_minima', 0)
                            porc = row.get('porcentaje_descuento', 0)
                            nombre = str(row.get('nombre_promo', 'Promoción')).strip()

                            if not tipo or not filtro or pd.isna(cant_min) or pd.isna(porc):
                                continue

                            reglas_limpias.append({
                                "tipo_regla": tipo,
                                "filtro": filtro,
                                "cantidad_minima": float(cant_min),
                                "porcentaje_descuento": float(porc),
                                "nombre_promo": nombre
                            })

                        if len(reglas_limpias) > 0:
                            supabase.table("reglas_descuentos").delete().neq("id", 0).execute()
                            supabase.table("reglas_descuentos").insert(reglas_limpias).execute()
                            st.success(f"¡Sincronización exitosa! Se cargaron {len(reglas_limpias)} reglas de descuento.")
                        else:
                            st.warning("El archivo no contiene reglas de descuento válidas o faltan columnas.")
                    except Exception as e:
                        st.error(f"Error crítico al procesar descuentos: {e}")
