import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
import time

# --- CONFIGURACIÓN DE PÁGINA ---
# Debe ser la primera instrucción
st.set_page_config(page_title="DistriOks ERP", page_icon="🏢", layout="wide")

# ==========================================
# 🔐 SISTEMA DE LOGIN (AUTENTICACIÓN)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    # Diseño de la pantalla de Login
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col2:
        # Mostrar el logo en el centro
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.warning("Falta el archivo logo.png en la carpeta")
            
        st.markdown("<h2 style='text-align: center; color: #0D47A1;'>Panel de Control ERP</h2>", unsafe_allow_html=True)
        st.divider()
        
        usuario = st.text_input("Usuario", placeholder="Ingresa tu usuario")
        clave = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        if st.button("Iniciar Sesión", type="primary", use_container_width=True):
            if usuario == "admin" and clave == "oks2026":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
    
    # st.stop() detiene la ejecución aquí para que no cargue el resto del panel si no está logueado
    st.stop()


# ==========================================
# 🏢 CÓDIGO PRINCIPAL DEL ERP (POST-LOGIN)
# ==========================================

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhdnpjZWZ3d2hnd3Z0emZlemxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODYxNzY0OSwiZXhwIjoyMTA0MTkzNjQ5fQ.wwwdUuXbH7_z2UnP3FhxRrKGWJF3ZCUwcxUseN87R-I"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MENÚ LATERAL (SIDEBAR) ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        pass
    st.markdown("<h3 style='text-align: center;'>Administración</h3>", unsafe_allow_html=True)
    st.divider()

    menu = st.radio(
        "Navegación",
        ["📦 Gestión de Pedidos", "📊 Dashboard (Estadísticas)", "⚙️ Sincronización Chess"]
    )
    
    st.divider()
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()

# ==========================================
# PANTALLA 1: GESTIÓN DE PEDIDOS
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
            p['Fecha'] = str(p.get('created_at', ''))[:10]
            cod_cliente = str(p.get('cliente_codigo', ''))
            datos_cli = dict_clientes.get(cod_cliente, {})
            p['Cliente'] = f"{cod_cliente} - {datos_cli.get('razon_social', 'Desconocido')}"
            p['Vendedor'] = datos_cli.get('vendedor', 'Sin Vendedor Asignado')
            
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

        # Filtros en Cascada
        col1, col2, col3 = st.columns(3)
        
        fechas_disponibles = sorted(df_pedidos['Fecha'].unique(), reverse=True)
        with col1:
            fecha_sel = st.selectbox("📅 1) Fecha", ["Todas las Fechas"] + list(fechas_disponibles))
        
        if fecha_sel != "Todas las Fechas":
            df_pedidos = df_pedidos[df_pedidos['Fecha'] == fecha_sel]
            
        vendedores_disponibles = sorted(df_pedidos['Vendedor'].unique())
        with col2:
            vendedor_sel = st.selectbox("👤 2) Vendedor", ["Todos los Vendedores"] + list(vendedores_disponibles))
            
        if vendedor_sel != "Todos los Vendedores":
            df_pedidos = df_pedidos[df_pedidos['Vendedor'] == vendedor_sel]
            
        with col3:
            opciones_pedido = ["Seleccione un pedido para ver el detalle..."]
            for idx, row in df_pedidos.iterrows():
                opciones_pedido.append(f"Ped #{row['id']} | {row['Cliente']} | {row['estado']}")
                
            pedido_sel_str = st.selectbox("🛒 3) Pedido / Cliente", opciones_pedido)

        st.divider()

        # Vista Resumen
        if pedido_sel_str == "Seleccione un pedido para ver el detalle...":
            st.subheader(f"Resumen de Subtotales")
            
            if fecha_sel == "Todas las Fechas":
                agrupado = df_pedidos.groupby('Fecha').agg({
                    'id': 'count', 'Bultos': 'sum', 'Unidades': 'sum', 'Final': 'sum'
                }).reset_index()
                agrupado.rename(columns={'id': 'Cant. Pedidos', 'Fecha': 'Selección'}, inplace=True)
                
            elif vendedor_sel == "Todos los Vendedores":
                agrupado = df_pedidos.groupby('Vendedor').agg({
                    'id': 'count', 'Bultos': 'sum', 'Unidades': 'sum', 'Final': 'sum'
                }).reset_index()
                agrupado.rename(columns={'id': 'Cant. Pedidos', 'Vendedor': 'Selección'}, inplace=True)
                
            else:
                agrupado = df_pedidos[['Cliente', 'id', 'Bultos', 'Unidades', 'Final', 'estado']].copy()
                agrupado.rename(columns={'id': 'Pedido #', 'Cliente': 'Selección', 'estado': 'Estado'}, inplace=True)

            totales = pd.DataFrame([{
                'Selección': 'TOTALES',
                'Cant. Pedidos' if 'Cant. Pedidos' in agrupado.columns else 'Pedido #': len(df_pedidos),
                'Bultos': df_pedidos['Bultos'].sum(),
                'Unidades': df_pedidos['Unidades'].sum(),
                'Final': df_pedidos['Final'].sum()
            }])
            
            agrupado_final = pd.concat([agrupado, totales], ignore_index=True)
            agrupado_final['Final'] = agrupado_final['Final'].apply(lambda x: f"$ {x:,.2f}" if pd.notnull(x) else "")
            
            st.dataframe(agrupado_final, use_container_width=True, hide_index=True)

        # Vista Detalle
        else:
            id_seleccionado = int(pedido_sel_str.split('|')[0].replace("Ped #", "").strip())
            pedido_actual = df_pedidos[df_pedidos['id'] == id_seleccionado].iloc[0].to_dict()
            
            col_izq, col_der = st.columns([2, 1])
            
            with col_izq:
                st.markdown(f"### 📄 Detalle Pedido #{pedido_actual['id']}")
                st.write(f"**Cliente:** {pedido_actual['Cliente']}")
                st.write(f"**Vendedor:** {pedido_actual['Vendedor']}")
                st.write(f"**Fecha Solicitada:** {pedido_actual.get('fecha_entrega', 'No especificada')}")
                
                items = pedido_actual.get('items', [])
                if items:
                    df_items = pd.DataFrame(items)
                    if 'precio' in df_items.columns and 'cantidad' in df_items.columns:
                        df_items['subtotal'] = df_items['precio'] * df_items['cantidad']
                        df_items['precio'] = df_items['precio'].apply(lambda x: f"$ {x:,.2f}")
                        df_items['subtotal'] = df_items['subtotal'].apply(lambda x: f"$ {x:,.2f}")
                    st.dataframe(df_items, use_container_width=True, hide_index=True)
                
                st.markdown(f"## TOTAL FINAL: $ {pedido_actual['Final']:,.2f}")
                st.info("💡 Para imprimir este pedido, presiona **Ctrl + P**.")

            with col_der:
                st.markdown("### ⚙️ Acciones")
                estado_actual = pedido_actual.get('estado', 'En Preparación')
                lista_estados = ['En Preparación', 'En Reparto', 'Entregado', 'Cancelado', 'Rechazado']
                idx_estado = lista_estados.index(estado_actual) if estado_actual in lista_estados else 0
                
                nuevo_estado = st.selectbox("Estado del pedido:", lista_estados, index=idx_estado)
                if st.button("Guardar Estado", type="primary", use_container_width=True):
                    try:
                        supabase.table('pedidos').update({'estado': nuevo_estado}).eq('id', pedido_actual['id']).execute()
                        st.success(f"Estado actualizado a '{nuevo_estado}'")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ==========================================
# PANTALLA 2: DASHBOARD (ESTADÍSTICAS)
# ==========================================
elif menu == "📊 Dashboard (Estadísticas)":
    st.title("📊 Panel Gerencial y Estadísticas")
    st.write("Métricas de rendimiento y evolución comercial en tiempo real.")

    # 1. Obtener datos de pedidos y clientes
    res_pedidos = supabase.table('pedidos').select('*').execute()
    pedidos_raw = res_pedidos.data

    if not pedidos_raw:
        st.warning("No hay suficientes datos de pedidos registrados para generar el dashboard.")
    else:
        res_clientes = supabase.table('clientes').select('codigo, razon_social, vendedor').execute()
        dict_clientes = {str(c['codigo']): c for c in res_clientes.data}

        # 2. Procesar datos para análisis
        for p in pedidos_raw:
            p['Fecha'] = str(p.get('created_at', ''))[:10]
            cod_cli = str(p.get('cliente_codigo', ''))
            cli_info = dict_clientes.get(cod_cli, {})
            p['Vendedor'] = cli_info.get('vendedor', 'Sin Asignar')
            p['Total'] = float(p.get('total', 0))
            
            bultos = 0
            for item in p.get('items', []):
                if str(item.get('tipo', '')).lower() == 'bulto':
                    bultos += float(item.get('cantidad', 0))
            p['Bultos'] = bultos

        df = pd.DataFrame(pedidos_raw)

        # 3. Tarjetas KPI Superiores (Estilo Nextbyn)
        total_ventas = df['Total'].sum()
        total_pedidos = len(df)
        total_bultos = df['Bultos'].sum()

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Facturación Total", f"$ {total_ventas:,.2f}")
        kpi2.metric("📦 Total de Pedidos", f"{total_pedidos}")
        kpi3.metric("📦 Total de Bultos", f"{total_bultos:,.1f}")

        st.divider()

        # 4. Gráficos Interactivos con Plotly
        import plotly.express as px

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📈 Evolución Diaria de Ventas")
            df_fecha = df.groupby('Fecha')['Total'].sum().reset_index()
            fig_fecha = px.line(
                df_fecha, 
                x='Fecha', 
                y='Total', 
                markers=True, 
                title="Curva de Ventas ($)"
            )
            fig_fecha.update_layout(
                xaxis_title="Fecha", 
                yaxis_title="Monto ($)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_fecha, use_container_width=True)

        with col_g2:
            st.subheader("👤 Ventas por Vendedor")
            df_vend = df.groupby('Vendedor')['Total'].sum().reset_index()
            fig_vend = px.bar(
                df_vend, 
                x='Vendedor', 
                y='Total', 
                text_auto='.2s', 
                title="Facturación por Asesor ($)",
                color='Vendedor'
            )
            fig_vend.update_layout(
                xaxis_title="Vendedor", 
                yaxis_title="Total ($)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_vend, use_container_width=True)
            
# ==========================================
# PANTALLA 3: CARGA DE DATOS
# ==========================================
elif menu == "⚙️ Sincronización Chess":
    st.markdown("<h1 style='text-align: center;'>🔄 Actualización de Datos desde Chess</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Gestión inteligente y sincronización masiva hacia Supabase.</p>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible", "Promociones", "Reglas Descuento"])

    # --- PESTAÑA 1: CLIENTES ---
    with tab1:
        st.subheader("Subir Plantilla de Clientes")
        archivo_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx", "xls"], key="cli")

        if archivo_clientes is not None:
            if st.button("Procesar y Sincronizar Clientes"):
                with st.spinner("Leyendo y filtrando columnas..."):
                    try:
                        df = pd.read_excel(archivo_clientes, header=None, skiprows=1)
                        def safe_get(row_idx, col_idx):
                            try:
                                val = df.iloc[row_idx, col_idx]
                                if pd.isna(val) or str(val).strip().lower() in ['nan', 'nat', 'none', '']: return None
                                return str(val).strip()
                            except: return None

                        registros_limpios = []
                        for idx in range(len(df)):
                            codigo = safe_get(idx, 1)
                            if not codigo: continue
                            
                            registros_limpios.append({
                                "codigo": codigo, "razon_social": safe_get(idx, 2), "domicilio": safe_get(idx, 7),
                                "canal": safe_get(idx, 40), "lista_precios": safe_get(idx, 42), "forma_pago": safe_get(idx, 47),
                                "categoria_impositiva": safe_get(idx, 58), "tipo_documento": safe_get(idx, 60),
                                "numero_documento": safe_get(idx, 61), "vendedor": safe_get(idx, 84), "dia_visita": safe_get(idx, 85)
                            })

                        if registros_limpios:
                            for i in range(0, len(registros_limpios), 500):
                                supabase.table("clientes").upsert(registros_limpios[i:i + 500], on_conflict="codigo").execute()
                            st.success(f"¡Sincronización exitosa! Se procesaron {len(registros_limpios)} clientes.")
                        else: st.warning("Archivo sin registros válidos.")
                    except Exception as e: st.error(f"Error: {e}")
                        
    # --- PESTAÑA 2: PRECIOS Y ATRIBUTOS ---
    with tab2:
        st.subheader("Subir Lista de Precios y Atributos")
        tipo_archivo = st.radio("¿Qué archivo vas a subir?", ["Lista de Precios 1", "Lista Mayorista", "Atributos y Categorías"])
        archivo_precios = st.file_uploader("Selecciona el archivo", type=["xlsx", "xls", "txt", "csv"], key="pre")

        if archivo_precios is not None:
            if st.button("Procesar y Sincronizar"):
                with st.spinner("Procesando datos..."):
                    try:
                        if "Atributos" in tipo_archivo:
                            try: df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                            except: 
                                archivo_precios.seek(0)
                                df = pd.read_csv(archivo_precios, sep=None, engine='python', header=None, skiprows=1, encoding='latin-1')

                            def safe_get_attr(r, c):
                                try:
                                    val = df.iloc[r, c]
                                    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return None
                                    return str(val).strip()
                                except: return None

                            registros_limpios = []
                            for idx in range(len(df)):
                                cod = safe_get_attr(idx, 0)
                                cat = safe_get_attr(idx, 2)
                                if cod and cat and cod.lower() not in ['nan', 'none']:
                                    registros_limpios.append({"codigo": cod, "categoria": cat})
                            
                            if registros_limpios:
                                for i in range(0, len(registros_limpios), 500):
                                    supabase.table("productos").upsert(registros_limpios[i:i+500], on_conflict="codigo").execute()
                                st.success(f"¡Procesados {len(registros_limpios)} registros válidos.")
                            else: st.warning("El archivo no tiene categorías válidas.")
                        
                        else:
                            df = pd.read_excel(archivo_precios, header=None, skiprows=1)
                            def safe_get_precio(r, c):
                                try:
                                    val = df.iloc[r, c]
                                    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']: return None
                                    return val
                                except: return None

                            registros_limpios = []
                            for idx in range(len(df)):
                                cod = safe_get_precio(idx, 4)
                                if not cod or str(cod).strip().lower() in ['nan', 'none']: continue
                                
                                u_b = safe_get_precio(idx, 9)
                                p_b = safe_get_precio(idx, 15)
                                p_u = safe_get_precio(idx, 18)
                                
                                pb_col = "precio_bulto_mayorista" if "Mayorista" in tipo_archivo else "precio_bulto_lista1"
                                pu_col = "precio_unidad_mayorista" if "Mayorista" in tipo_archivo else "precio_unidad_lista1"
                                
                                registros_limpios.append({
                                    "codigo": str(cod).strip(),
                                    "descripcion": str(safe_get_precio(idx, 5)).strip() if safe_get_precio(idx, 5) else None,
                                    "unidades_por_bulto": float(u_b) if u_b else None,
                                    pb_col: float(p_b) if p_b else None,
                                    pu_col: float(p_u) if p_u else None,
                                })

                            if registros_limpios:
                                for i in range(0, len(registros_limpios), 500):
                                    supabase.table("productos").upsert(registros_limpios[i:i+500], on_conflict="codigo").execute()
                                st.success(f"¡Sincronizados {len(registros_limpios)} productos!")
                            else: st.warning("Archivo inválido.")
                    except Exception as e: st.error(f"Error: {e}")
                        
    # --- PESTAÑA 3: STOCK ---
    with tab3:
        st.subheader("Subir Stock Disponible")
        archivo_stock = st.file_uploader("Selecciona el archivo Excel", type=["xlsx", "xls"], key="stk")

        if archivo_stock is not None:
            if st.button("Procesar Stock"):
                with st.spinner("Leyendo stock..."):
                    try:
                        df = pd.read_excel(archivo_stock, header=None, skiprows=1)
                        df_limpio = pd.DataFrame()
                        df_limpio["codigo"] = df[0].astype(str).str.strip()
                        df_limpio["bultos"] = pd.to_numeric(df[2], errors="coerce").fillna(0)
                        df_limpio["unidades"] = pd.to_numeric(df[3], errors="coerce").fillna(0)
                        df_limpio = df_limpio.drop_duplicates(subset=["codigo"], keep="last")
                        df_limpio = df_limpio[df_limpio["codigo"].notna() & (df_limpio["codigo"] != 'None')]
                        
                        regs = df_limpio.to_dict(orient="records")
                        if regs:
                            for i in range(0, len(regs), 500):
                                supabase.table("stock_actual").upsert(regs[i:i + 500], on_conflict="codigo").execute()
                            st.success(f"¡Actualizados {len(regs)} artículos!")
                    except Exception as e: st.error(f"Error: {e}")

    # --- PESTAÑA 4: PROMOCIONES ---
    with tab4:
        st.subheader("Subir Promociones")
        archivos_imagenes = st.file_uploader("Selecciona imágenes", type=['jpg', 'jpeg', 'png'], key="promo", accept_multiple_files=True)

        if st.button("Subir Promociones"):
            if archivos_imagenes:
                with st.spinner(f"Subiendo {len(archivos_imagenes)} imágenes..."):
                    exitos = 0
                    for arch in archivos_imagenes:
                        try:
                            bytes_data = arch.getvalue()
                            nombre_unico = f"{int(time.time())}_{arch.name}"
                            supabase.storage.from_('PROMOS').upload(file=bytes_data, path=nombre_unico, file_options={"content-type": arch.type})
                            url_pub = supabase.storage.from_('PROMOS').get_public_url(nombre_unico)
                            supabase.table('promociones').insert({"imagen_url": url_pub}).execute()
                            exitos += 1
                            st.image(url_pub, width=150)
                        except Exception as e: st.error(f"Error con {arch.name}: {e}")
                    if exitos > 0: st.success("¡Subidas con éxito!")
            else: st.warning("Selecciona una imagen.")

    # --- PESTAÑA 5: REGLAS DE DESCUENTO ---
    with tab5:
        st.subheader("Sincronizar Reglas de Descuento")
        archivo_descuentos = st.file_uploader("Selecciona el Excel", type=["xlsx", "xls"], key="desc")

        if archivo_descuentos is not None:
            if st.button("Procesar Descuentos"):
                with st.spinner("Leyendo reglas..."):
                    try:
                        df_desc = pd.read_excel(archivo_descuentos)
                        reglas = []
                        for idx, row in df_desc.iterrows():
                            tipo = str(row.get('tipo_regla', '')).strip().upper()
                            filtro = str(row.get('filtro', '')).strip()
                            cant_min = row.get('cantidad_minima', 0)
                            porc = row.get('porcentaje_descuento', 0)
                            nom = str(row.get('nombre_promo', 'Promoción')).strip()

                            if tipo and filtro and pd.notna(cant_min) and pd.notna(porc):
                                reglas.append({"tipo_regla": tipo, "filtro": filtro, "cantidad_minima": float(cant_min), "porcentaje_descuento": float(porc), "nombre_promo": nom})

                        if reglas:
                            supabase.table("reglas_descuentos").delete().neq("id", 0).execute()
                            supabase.table("reglas_descuentos").insert(reglas).execute()
                            st.success(f"¡Cargadas {len(reglas)} reglas!")
                    except Exception as e: st.error(f"Error: {e}")
