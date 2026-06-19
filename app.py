import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

st.set_page_config(page_title="Predicción precio de casas", page_icon="🏠")

st.title("Predicción del precio medio de casas")

# =========================
# CONFIGURACIÓN DATAROBOT
# =========================

DATAROBOT_API_KEY = st.secrets["DATAROBOT_API_KEY"].strip()
DATAROBOT_API_KEY = DATAROBOT_API_KEY.replace("Token ", "").replace("Bearer ", "").strip()

DATAROBOT_DEPLOYMENT_ID = st.secrets["DATAROBOT_DEPLOYMENT_ID"].strip()
DATAROBOT_HOST = st.secrets["DATAROBOT_HOST"].strip().rstrip("/")

BATCH_URL = f"{DATAROBOT_HOST}/api/v2/batchPredictions/"

HEADERS = {
    "Authorization": f"Token {DATAROBOT_API_KEY}",
    "User-Agent": "IntegrationSnippet-StandAlone-Python"
}

# =========================
# VARIABLES DEL MODELO
# =========================

st.subheader("Variables de entrada")

longitud = st.number_input("Longitud", value=-122.23, step=0.01)
latitud = st.number_input("Latitud", value=37.88, step=0.01)

edad_mediana_vivienda = st.number_input(
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
    ["NEAR BAY", "<1H OCEAN", "INLAND", "NEAR OCEAN", "ISLAND"]
)

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

st.subheader("Datos enviados")
st.dataframe(datos, use_container_width=True)

# =========================
# FUNCIÓN DE PREDICCIÓN
# =========================

def predecir_con_datarobot(df):
    payload = {
        "deploymentId": DATAROBOT_DEPLOYMENT_ID,
        "passthroughColumnsSet": "all"
    }

    crear_job = requests.post(
        BATCH_URL,
        headers={
            **HEADERS,
            "Content-Type": "application/json; encoding=utf-8"
        },
        json=payload
    )

    if crear_job.status_code not in [200, 201, 202]:
        raise Exception(f"Error creando job: {crear_job.text}")

    job = crear_job.json()

    upload_url = job["links"]["csvUpload"]
    job_url = job["links"]["self"]

    csv_data = df.to_csv(index=False).encode("utf-8")

    subir_csv = requests.put(
        upload_url,
        data=csv_data,
        headers={
            "Content-type": "text/csv; encoding=utf-8",
            "Content-length": str(len(csv_data))
        }
    )

    if subir_csv.status_code not in [200, 201, 202, 204]:
        raise Exception(f"Error subiendo CSV: {subir_csv.text}")

    while True:
        estado_response = requests.get(
            job_url,
            headers=HEADERS
        )

        if estado_response.status_code != 200:
            raise Exception(f"Error consultando estado: {estado_response.text}")

        estado = estado_response.json()
        status = estado["status"]

        if status == "COMPLETED":
            break

        if status in ["FAILED", "ABORTED"]:
            raise Exception(f"Job falló: {estado}")

        time.sleep(3)

    download_url = estado["links"]["download"]

    resultado_response = requests.get(
        download_url,
        headers=HEADERS
    )

    if resultado_response.status_code != 200:
        raise Exception(f"Error descargando resultado: {resultado_response.text}")

    resultado_df = pd.read_csv(StringIO(resultado_response.text))
    return resultado_df

# =========================
# BOTÓN
# =========================

if st.button("Predecir valor de vivienda"):
    try:
        with st.spinner("Consultando DataRobot..."):
            resultado = predecir_con_datarobot(datos)

        st.success("Predicción realizada correctamente")

        st.subheader("Resultado completo")
        st.dataframe(resultado, use_container_width=True)

        columnas_pred = [
            col for col in resultado.columns
            if "prediction" in col.lower()
            or "pred" in col.lower()
        ]

        if columnas_pred:
            prediccion = resultado[columnas_pred[0]].iloc[0]

            st.metric(
                "Valor mediano estimado de la vivienda",
                f"${float(prediccion):,.2f}"
            )
        else:
            st.warning("No se encontró la columna de predicción.")
            st.write(resultado.columns.tolist())

    except Exception as e:
        st.error("Error al consultar DataRobot")
        st.exception(e)
