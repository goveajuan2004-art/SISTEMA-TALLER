import datetime
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Taller - Refrigeración Automotriz",
    layout="wide",
)

# Inicializar bases de datos temporales en la sesión si no existen
if "inventario" not in st.session_state:
  st.session_state.inventario = pd.DataFrame(
      columns=[
          "ID / Código",
          "Producto",
          "Categoría",
          "Stock",
          "Precio Unitario ($)",
      ]
  )
  # Datos de ejemplo iniciales
  st.session_state.inventario.loc[0] = [
      "GASS-01",
      "Gas R134a (Cilindro)",
      "Insumos",
      3,
      120.0,
  ]
  st.session_state.inventario.loc[1] = [
      "ACE-02",
      "Aceite PAG 46",
      "Lubricantes",
      8,
      25.0,
  ]
  st.session_state.inventario.loc[2] = [
      "OR-03",
      "O-ring Kit Universal",
      "Repuestos",
      30,
      12.5,
  ]

if "bitacora_salidas" not in st.session_state:
  st.session_state.bitacora_salidas = pd.DataFrame(
      columns=[
          "Fecha y Hora",
          "Cliente",
          "Vehículo",
          "Producto",
          "Cantidad",
          "Tipo",
      ]
  )

if "presupuestos" not in st.session_state:
  st.session_state.presupuestos = pd.DataFrame(
      columns=["Fecha", "Cliente", "Vehículo", "Detalle", "Total ($)"]
  )

# Menú lateral
st.sidebar.title("❄️ Taller de Refrigeración")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Menú Principal",
    [
        "📦 Inventario y Buscador",
        "📋 Bitácora de Salidas",
        "🧾 Presupuestos y Clientes",
    ],
)

# ==========================================
# 1. MÓDULO DE INVENTARIO, BUSCADOR Y ALERTAS
# ==========================================
if menu == "📦 Inventario y Buscador":
  st.header("📦 Gestión General de Inventario y Alertas")

  # --- PANEL DE CONTROL Y ESTADÍSTICAS RÁPIDAS ---
  df_inv = st.session_state.inventario
  total_productos = len(df_inv)
  stock_critico = (
      len(df_inv[df_inv["Stock"] < 5]) if not df_inv.empty else 0
  )

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric(
        label="📦 Tipos de Productos Registrados", value=total_productos
    )
  with col_m2:
    st.metric(
        label="⚠️ Alertas de Stock Bajo (< 5 un.)",
        value=stock_critico,
        delta=f"-{stock_critico} críticos" if stock_critico > 0 else "Todo bien",
        delta_color="inverse",
    )
  with col_m3:
    st.metric(
        label="📋 Total Movimientos en Bitácora",
        value=len(st.session_state.bitacora_salidas),
    )

  if stock_critico > 0 and not df_inv.empty:
    items_criticos = df_inv[df_inv["Stock"] < 5]["Producto"].tolist()
    st.warning(
        "⚠️ **Atención:** Los siguientes productos tienen stock bajo y"
        f" necesitan reposición: **{', '.join(items_criticos)}**"
    )

  st.markdown("---")

  tab1, tab2 = st.tabs(
      ["🔍 Buscador y Control de Stock", "➕ Registrar Nuevo Producto"]
  )

  with tab1:
    st.subheader("Inventario en Tiempo Real")

    # Buscador interactivo
    busqueda = st.text_input(
        "🔍 Buscar pieza por Nombre o Código (ID)...", ""
    )

    if busqueda:
      filtro = df_inv[
          df_inv["ID / Código"]
          .astype(str)
          .str.contains(busqueda, case=False, na=False)
          | df_inv["Producto"]
          .astype(str)
          .str.contains(busqueda, case=False, na=False)
      ]
    else:
      filtro = df_inv

    st.dataframe(filtro, use_container_width=True)

    st.markdown("---")
    st.subheader("⚡ Acciones (Meter, Sacar o Eliminar Stock)")

    if not df_inv.empty:
      col_acc1, col_acc2, col_acc3 = st.columns(3)

      # 1. METER STOCK
      with col_acc1:
        st.markdown("#### 📥 Meter Stock")
        with st.form("form_meter"):
          prod_sel_meter = st.selectbox(
              "Producto", df_inv["Producto"].tolist(), key="sel_meter"
          )
          cant_meter = st.number_input(
              "Cantidad a agregar", min_value=1, step=1, key="cant_m"
          )
          btn_meter = st.form_submit_button("Sumar Stock")

          if btn_meter:
            idx = st.session_state.inventario[
                st.session_state.inventario["Producto"] == prod_sel_meter
            ].index[0]
            st.session_state.inventario.loc[idx, "Stock"] += int(cant_meter)
            st.success(
                f"¡Se agregaron {cant_meter} unidades a {prod_sel_meter}!"
            )
            st.rerun()

      # 2. SACAR STOCK
      with col_acc2:
        st.markdown("#### 📤 Sacar Stock")
        tipo_retiro = st.selectbox(
            "Modo", ["Para Cliente", "Libre / Taller"], key="tipo_r"
        )

        if tipo_retiro == "Para Cliente":
          with st.form("form_sacar_cliente"):
            prod_sel_sacar = st.selectbox(
                "Producto", df_inv["Producto"].tolist(), key="sel_sacar_c"
            )
            cliente_salida = st.text_input("Cliente")
            vehiculo_salida = st.text_input("Vehículo")
            cant_sacar = st.number_input(
                "Cantidad", min_value=1, step=1, key="cant_s_c"
            )
            btn_sacar_c = st.form_submit_button("Descontar")

            if btn_sacar_c:
              if cliente_salida and vehiculo_salida:
                idx = st.session_state.inventario[
                    st.session_state.inventario["Producto"] == prod_sel_sacar
                ].index[0]
                stock_actual = int(
                    st.session_state.inventario.loc[idx, "Stock"]
                )

                if cant_sacar <= stock_actual:
                  st.session_state.inventario.loc[idx, "Stock"] = (
                      stock_actual - int(cant_sacar)
                  )
                  ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                  nueva_salida = pd.DataFrame({
                      "Fecha y Hora": [ahora],
                      "Cliente": [cliente_salida],
                      "Vehículo": [vehiculo_salida],
                      "Producto": [prod_sel_sacar],
                      "Cantidad": [int(cant_sacar)],
                      "Tipo": ["Reparación / Instalación"],
                  })
                  st.session_state.bitacora_salidas = pd.concat(
                      [st.session_state.bitacora_salidas, nueva_salida],
                      ignore_index=True,
                  )
                  st.success(
                      f"¡Descontadas {cant_sacar} un. de {prod_sel_sacar}!"
                  )
                  st.rerun()
                else:
                  st.error("Stock insuficiente.")
              else:
                st.error("Falta cliente y vehículo.")
        else:
          with st.form("form_sacar_libre"):
            prod_sel_libre = st.selectbox(
                "Producto", df_inv["Producto"].tolist(), key="sel_sacar_l"
            )
            cant_sacar_libre = st.number_input(
                "Cantidad", min_value=1, step=1, key="cant_s_l"
            )
            btn_sacar_l = st.form_submit_button("Descontar Libre")

            if btn_sacar_l:
              idx = st.session_state.inventario[
                  st.session_state.inventario["Producto"] == prod_sel_libre
              ].index[0]
              stock_actual = int(st.session_state.inventario.loc[idx, "Stock"])

              if cant_sacar_libre <= stock_actual:
                st.session_state.inventario.loc[idx, "Stock"] = (
                    stock_actual - int(cant_sacar_libre)
                )
                ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nueva_salida = pd.DataFrame({
                    "Fecha y Hora": [ahora],
                    "Cliente": ["N/A (Uso Interno)"],
                    "Vehículo": ["N/A"],
                    "Producto": [prod_sel_libre],
                    "Cantidad": [int(cant_sacar_libre)],
                    "Tipo": ["Uso interno / Ajuste"],
                })
                st.session_state.bitacora_salidas = pd.concat(
                    [st.session_state.bitacora_salidas, nueva_salida],
                    ignore_index=True,
                )
                st.success(
                    f"¡Descontadas {cant_sacar_libre} un. de {prod_sel_libre}!"
                )
                st.rerun()
              else:
                st.error("Stock insuficiente.")

      # 3. ELIMINAR PRODUCTO DEL INVENTARIO
      with col_acc3:
        st.markdown("#### 🗑️ Eliminar Producto")
        with st.form("form_eliminar_prod"):
          prod_a_borrar = st.selectbox(
              "Seleccionar para Borrar",
              df_inv["Producto"].tolist(),
              key="sel_borrar",
          )
          btn_borrar = st.form_submit_button(
              "Eliminar del Inventario", type="primary"
          )

          if btn_borrar:
            # Filtrar y eliminar la fila del producto
            st.session_state.inventario = st.session_state.inventario[
                st.session_state.inventario["Producto"] != prod_a_borrar
            ].reset_index(drop=True)
            st.success(f"¡El producto '{prod_a_borrar}' fue eliminado con éxito!")
            st.rerun()

  with tab2:
    st.subheader("Registrar Nuevo Material o Repuesto")
    with st.form("form_nuevo_producto"):
      col_n1, col_n2 = st.columns(2)
      with col_n1:
        nuevo_id = st.text_input("Código o ID (Opcional)")
      with col_n2:
        nuevo_nombre = st.text_input("Nombre de la Pieza / Material *")

      categoria = st.selectbox(
          "Categoría",
          [
              "Insumos (Gas/Aceite)",
              "Repuestos",
              "Herramientas",
              "Mangueras y Conexiones",
              "Otros",
          ],
      )
      cantidad_inicial = st.number_input(
          "Cantidad Inicial en Stock", min_value=0, step=1
      )
      precio_unit = st.number_input(
          "Precio Unitario ($)", min_value=0.0, step=0.1
      )

      guardar_nuevo = st.form_submit_button("Guardar Nuevo Producto")

      if guardar_nuevo:
        if nuevo_nombre:
          if not nuevo_id:
            nuevo_id = (
                f"PROD-{len(st.session_state.inventario) + 1:03d}"
            )

          df = st.session_state.inventario
          if nuevo_id in df["ID / Código"].values:
            st.error("Ya existe un producto con este código.")
          else:
            nuevo_row = pd.DataFrame({
                "ID / Código": [nuevo_id],
                "Producto": [nuevo_nombre],
                "Categoría": [categoria],
                "Stock": [int(cantidad_inicial)],
                "Precio Unitario ($)": [float(precio_unit)],
            })
            st.session_state.inventario = pd.concat(
                [df, nuevo_row], ignore_index=True
            )
            st.success(f"¡Producto '{nuevo_nombre}' registrado con éxito!")
            st.rerun()
        else:
          st.error("El nombre del producto es obligatorio.")

# ==========================================
# 2. BITÁCORA DE SALIDAS
# ==========================================
elif menu == "📋 Bitácora de Salidas":
  st.header("📋 Bitácora de Repuestos y Piezas Sacadas")
  st.markdown(
      "Control detallado ordenado por día, fecha y hora de cada salida del"
      " inventario."
  )

  if st.session_state.bitacora_salidas.empty:
    st.info("Aún no hay registros de salidas.")
  else:
    st.dataframe(st.session_state.bitacora_salidas, use_container_width=True)

# ==========================================
# 3. PRESUPUESTOS Y CLIENTES
# ==========================================
elif menu == "🧾 Presupuestos y Clientes":
  st.header("🧾 Control de Presupuestos y Registro Diario")

  with st.form("form_presupuesto"):
    c_nombre = st.text_input("Nombre del Cliente")
    c_vehiculo = st.text_input("Vehículo")
    detalle_trabajo = st.text_area(
        "Detalle del Presupuesto (Repuestos y Mano de Obra)"
    )
    total_presupuesto = st.number_input(
        "Monto Total ($)", min_value=0.0, step=1.0
    )

    guardar_presup = st.form_submit_button("Guardar Presupuesto y Cliente")

    if guardar_presup:
      if c_nombre and c_vehiculo:
        fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        nuevo_p = pd.DataFrame({
            "Fecha": [fecha_hoy],
            "Cliente": [c_nombre],
            "Vehículo": [c_vehiculo],
            "Detalle": [detalle_trabajo],
            "Total ($)": [float(total_presupuesto)],
        })
        st.session_state.presupuestos = pd.concat(
            [st.session_state.presupuestos, nuevo_p], ignore_index=True
        )
        st.success("¡Presupuesto guardado correctamente!")
        st.rerun()
      else:
        st.error("Completa el nombre del cliente y del vehículo.")

  st.subheader("Historial de Clientes y Presupuestos")
  if st.session_state.presupuestos.empty:
    st.info("No hay presupuestos registrados.")
  else:
    st.dataframe(st.session_state.presupuestos, use_container_width=True)