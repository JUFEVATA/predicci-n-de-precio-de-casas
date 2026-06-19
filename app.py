import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Predicción precio medio de vivienda",
    page_icon="🏠",
    layout="centered"
)

st.title("Predicción del precio medio de vivienda")
st.write("Ingresa las variables del inmueble y el modelo devolverá una predicción.")

# =========================
# CONFIGURACIÓN DATAROBOT
# =========================

DATAROBOT_API_TOKEN = st.secrets["DATAROBOT_API_TOKEN"]
DATAROBOT_DEPLOYMENT_URL = st.secrets["DATAROBOT_DEPLOYMENT_URL"]

HEADERS = {
    "Authorization": f"Bearer {DATAROBOT_API_TOKEN}",
    "Content-Type": "application/json; charset=UTF-8"
}

# =========================
# FORMULARIO DE VARIABLES
# =========================

st.subheader("Variables del modelo")

longitud = st.number_input("Longitud", value=-122.23, step=0.01)
latitud = st.number_input("Latitud", value=37.88, step=0.01)

edad_mediana_vivienda = st.slider(
    "Edad mediana de la vivienda",
    min_value=1,
    max_value=60,
    value=30
)

total_habitaciones = st.number_input(
    "Total de habitaciones",
    min_value=1,
    value=880
)

total_dormitorios = st.number_input(
    "Total de dormitorios",
    min_value=1,
    value=129
)

poblacion = st.number_input(
    "Población",
    min_value=1,
    value=322
)

hogares = st.number_input(
    "Hogares",
    min_value=1,
    value=126
)

ingreso_mediano = st.number_input(
    "Ingreso mediano",
    min_value=0.0,
    value=8.3252,
    step=0.01
)

proximidad_oceano = st.selectbox(
    "Proximidad al océano",
    [
        "NEAR BAY",
        "<1H OCEAN",
        "INLAND",
        "NEAR OCEAN",
        "ISLAND"
    ]
)

# =========================
# DATAFRAME DE ENTRADA
# =========================

datos = pd.DataFrame([{
    "longitud": longitud,
    "latitud": latitud,
    "edad_mediana_vivienda": edad_mediana_vivienda,
    "total_habitaciones": total_habitaciones,
    "total_dormitorios": total_dormitorios,
    "poblacion": poblacion,
    "hogares": hogares,
    "ingreso_mediano": ingreso_mediano,
    "proximidad_oceano": proximidad_oceano
}])

st.subheader("Datos enviados al modelo")
st.dataframe(datos)

# =========================
# PREDICCIÓN
# =========================

if st.button("Predecir precio medio"):
    try:
        response = requests.post(
            DATAROBOT_DEPLOYMENT_URL,
            headers=HEADERS,
            json=datos.to_dict(orient="records")
        )

        if response.status_code == 200:
            resultado = response.json()

            st.success("Predicción realizada correctamente")

            try:
                prediccion = resultado["data"][0]["prediction"]
                st.metric(
                    label="Precio medio estimado de la vivienda",
                    value=f"${prediccion:,.2f}"
                )
            except:
                st.write("Respuesta del modelo:")
                st.json(resultado)

        else:
            st.error("Error al consultar el modelo")
            st.write("Código de error:", response.status_code)
            st.write(response.text)

    except Exception as e:
        st.error("Ocurrió un error al realizar la predicción")
        st.write(e)
