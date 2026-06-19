import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Predicción valor vivienda",
    page_icon="🏠",
    layout="centered"
)

st.title("Predicción del valor medio de vivienda")
st.write("Modifica las variables de entrada y consulta el modelo desplegado en DataRobot.")

# =========================
# SECRETS DATAROBOT
# =========================

DATAROBOT_API_KEY = st.secrets["DATAROBOT_API_KEY"]
DATAROBOT_DEPLOYMENT_ID = st.secrets["DATAROBOT_DEPLOYMENT_ID"]
DATAROBOT_HOST = st.secrets["DATAROBOT_HOST"]

PREDICTION_URL = (
    f"{DATAROBOT_HOST}/predApi/v1.0/deployments/"
    f"{DATAROBOT_DEPLOYMENT_ID}/predictions"
)

HEADERS = {
    "Authorization": f"Bearer {DATAROBOT_API_KEY}",
    "Content-Type": "text/plain; charset=UTF-8"
}

# =========================
# FORMULARIO
# =========================

st.subheader("Variables de entrada")

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
# DATOS PARA EL MODELO
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
st.dataframe(datos, use_container_width=True)

csv_data = datos.to_csv(index=False)

# =========================
# PREDICCIÓN
# =========================

if st.button("Predecir valor de vivienda"):
    try:
        response = requests.post(
            PREDICTION_URL,
            headers=HEADERS,
            data=csv_data.encode("utf-8")
        )

        if response.status_code == 200:
            resultado = response.json()

            st.success("Predicción realizada correctamente")

            prediccion = resultado["data"][0]["prediction"]

            st.metric(
                label="Valor medio estimado de la vivienda",
                value=f"${prediccion:,.2f}"
            )

            with st.expander("Ver respuesta completa de DataRobot"):
                st.json(resultado)

        else:
            st.error("Error al consultar DataRobot")
            st.write("Código:", response.status_code)
            st.write(response.text)

    except Exception as e:
        st.error("Error ejecutando la predicción")
        st.write(e)
