import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de Conexión a Supabase (Tus credenciales de la API)
SUPABASE_URL = "https://davzcefwwhgwvtzfezlh.supabase.co"
# Nota: Para operaciones masivas desde el panel, se recomienda usar la clave service_role (o anon si no hay restricciones RLS)
SUPABASE_KEY = "TU_SUPABASE_ANON_KEY" 

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="DistriOks - Panel Controlador B2B", layout="wide")

st.title("📦 DistriOks - Panel Controlador y Backoffice")
st.markdown("Gestión centralizada de datos desde Chess y control de operaciones en tiempo real.")

# Menú lateral de navegación
menu = st.sidebar.selectbox("Seleccionar Módulo", ["Carga de Archivos Chess", "Pedidos Activos B2B"])

if menu == "Carga de Archivos Chess":
    st.header("🔄 Actualización de Datos desde Chess")
    st.markdown("Sube los reportes exportados para actualizar la base de datos en la nube al instante.")

    tab1, tab2, tab3 = st.tabs(["Maestro de Clientes", "Lista de Precios", "Stock Disponible"])

    # 1. CARGA DE CLIENTES
    with tab1:
        st.subheader("Subir Plantilla de Clientes")
        file_clientes = st.file_uploader("Selecciona el archivo Excel de Clientes", type=["xlsx"], key="cli")
        if file_clientes and st.button("Procesar y Sincronizar Clientes"):
            with st.spinner("Procesando clientes..."):
                df = pd.read_excel(file_clientes, header=2) # Ajustado al formato de Chess
                contador = 0
                for _, row in df.iterrows():
                    try:
                        cliente_data = {
                            "codigo_cliente": str(row.iloc[3]), # Columna Cliente
                            "razon_social": str(row.iloc[5]),  # Razón social
                            "email": str(row.iloc[10]) if pd.notna(row.iloc[10]) else "",
                            "telefono": str(row.iloc[12]) if pd.notna(row.iloc[12]) else "",
                            "direccion": f"{row.iloc[14]} {row.iloc[15]}", # Calle y Altura
                            "condicion_fiscal": str(row.iloc[24]) if pd.notna(row.iloc[24]) else "",
                            "vendedor_asignado": str(row.iloc[48]) if pd.notna(row.iloc[48]) else "",
                            "dia_visita": str(row.iloc[51]) if pd.notna(row.iloc[51]) else "",
                        }
                        supabase.table("clientes").upsert(cliente_data).execute()
                        contador += 1
                    except Exception as e:
                        st.error(f"Error detectado: {e}")
                    break
                st.success(f"¡Sincronización exitosa! Se procesaron {contador} clientes.")

    # 2. CARGA DE PRECIOS
    with tab2:
        st.subheader("Subir Plantilla de Precios y Productos")
        file_precios = st.file_uploader("Selecciona el archivo Excel de Precios", type=["xlsx"], key="pre")
        if file_precios and st.button("Procesar y Sincronizar Precios"):
            with st.spinner("Procesando precios y SKUs..."):
                df = pd.read_excel(file_precios, header=1)
                contador = 0
                for _, row in df.iterrows():
                    try:
                        producto_data = {
                            "codigo_sku": str(row.iloc[4]),     # Artículo
                            "nombre": str(row.iloc[5]),         # Descripción
                            "empaque": str(row.iloc[7]) if pd.notna(row.iloc[7]) else "UNIDAD", # Presentación
                            "precio_final": float(row.iloc[15]) if pd.notna(row.iloc[15]) else 0.0, # Precio Final
                            "subcategoria": "General"
                        }
                        supabase.table("productos").upsert(producto_data).execute()
                        contador += 1
                    except Exception as e:
                        continue
                st.success(f"¡Sincronización exitosa! Se procesaron {contador} productos/SKUs.")

    # 3. CARGA DE STOCK
    with tab3:
        st.subheader("Subir Plantilla de Stock Disponible")
        file_stock = st.file_uploader("Selecciona el archivo Excel de Stock", type=["xlsx"], key="stk")
        if file_stock and st.button("Procesar y Sincronizar Stock"):
            with st.spinner("Actualizando stock en tiempo real..."):
                df = pd.read_excel(file_stock, header=1)
                contador = 0
                for _, row in df.iterrows():
                    try:
                        stock_data = {
                            "codigo_sku": str(row.iloc[0]),
                            "descripcion": str(row.iloc[1]),
                            "bultos": int(row.iloc[2]) if pd.notna(row.iloc[2]) else 0,
                            "unidad_por_bulto": int(row.iloc[3]) if pd.notna(row.iloc[3]) else 1,
                            "unidades": int(row.iloc[4]) if pd.notna(row.iloc[4]) else 0,
                            "anulado": str(row.iloc[5]) if pd.notna(row.iloc[5]) else "NO"
                        }
                        supabase.table("stock_actual").upsert(stock_data).execute()
                        contador += 1
                    except Exception as e:
                        continue
                st.success(f"¡Stock actualizado! Se sincronizaron {contador} registros de inventario.")

elif menu == "Pedidos Activos B2B":
    st.header("📋 Monitoreo de Pedidos B2B")
    st.markdown("Listado de órdenes emitidas por los comercios desde la aplicación móvil.")

    if st.button("Actualizar Lista de Pedidos"):
        response = supabase.table("pedidos_b2b").select("*").execute()
        pedidos = response.data
        
        if pedidos:
            df_pedidos = pd.DataFrame(pedidos)
            st.dataframe(df_pedidos, use_container_width=True)
        else:
            st.info("No hay pedidos registrados en la nube todavía.")
