import os
import uuid
import subprocess
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Predicción precio medio de casas",
    page_icon="🏠",
    layout="centered"
)

st.title("Predicción del precio medio de casas")
st.write(
    "Aplicación conectada a un modelo desplegado en DataRobot para estimar "
    "el valor mediano de una vivienda."
)

API_KEY = st.secrets["DATAROBOT_API_KEY"]
DEPLOYMENT_ID = st.secrets["DATAROBOT_DEPLOYMENT_ID"]
HOST = st.secrets["DATAROBOT_HOST"]

PREDICT_SCRIPT = "predict.py"

st.subheader("Variables de entrada")

col1, col2 = st.columns(2)

with col1:
    longitud = st.number_input(
        "Longitud",
        value=-122.23,
        step=0.01
    )

    latitud = st.number_input(
        "Latitud",
        value=37.88,
        step=0.01
    )

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

with col2:
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
        options=[
            "<1H OCEAN",
            "INLAND",
            "ISLAND",
            "NEAR BAY",
            "NEAR OCEAN"
        ]
    )

datos_validos = True

if total_dormitorios > total_habitaciones:
    st.error("El total de dormitorios no debería ser mayor que el total de habitaciones.")
    datos_validos = False

if hogares > poblacion:
    st.error("El número de hogares no debería ser mayor que la población.")
    datos_validos = False

input_data = pd.DataFrame([{
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
st.dataframe(input_data, use_container_width=True)

if st.button("Predecir precio medio", disabled=not datos_validos):

    unique_id = str(uuid.uuid4())
    input_file = f"input_{unique_id}.csv"
    output_file = f"output_{unique_id}.csv"

    input_data.to_csv(input_file, index=False)

    command = [
        "python3",
        PREDICT_SCRIPT,
        input_file,
        output_file,
        DEPLOYMENT_ID,
        f"--api_key={API_KEY}",
        f"--host={HOST}"
    ]

    try:
        with st.spinner("Consultando el modelo desplegado en DataRobot..."):
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

        predictions = pd.read_csv(output_file)

        st.subheader("Resultado completo del modelo")
        st.dataframe(predictions, use_container_width=True)

        columnas_prediccion = [
            col for col in predictions.columns
            if "PREDICTION" in col.upper()
        ]

        if columnas_prediccion:
            valor_predicho = predictions.loc[0, columnas_prediccion[0]]

            st.metric(
                "Precio medio estimado de la vivienda",
                f"${float(valor_predicho):,.2f}"
            )
        else:
            st.warning("No se encontró automáticamente la columna de predicción.")
            st.write("Columnas disponibles:")
            st.write(predictions.columns.tolist())

    except subprocess.CalledProcessError as e:
        st.error("Error ejecutando predict.py")
        st.code(e.stderr)

    except Exception as e:
        st.error("Error inesperado")
        st.code(str(e))

    finally:
        if os.path.exists(input_file):
            os.remove(input_file)

        if os.path.exists(output_file):
            os.remove(output_file)
