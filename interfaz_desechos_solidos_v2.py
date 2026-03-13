import streamlit as st
import pandas as pd
import sqlite3
import math
from datetime import datetime

# ---------------------------
# Configuración
# ---------------------------

DISTANCIA = 0.30   # 30 cm
FACTOR_CORRECCION = 2
NIVEL_DISPENSA = 74  # Bq/g

# Periodos de semidesintegración (días)
HALF_LIFE = {
    "I-131": 8.02,
    "Tc-99m": 0.25,
    "Ra-223": 11.43,
    "Lu-177": 6.65,
    "F-18": 0.076
}

# Constantes gamma aproximadas (mSv m² / MBq h)
GAMMA = {
    "I-131": 5.95e-5,
    "Tc-99m": 2.05e-5,
    "Ra-223": 4.54e-5,
    "Lu-177": 5.17e-6,
    "F-18": 1.49e-4
}

# ---------------------------
# Base de datos
# ---------------------------

conn = sqlite3.connect("registros_desechos.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS registros (
    fecha TEXT,
    bulto TEXT,
    radionuclido TEXT,
    masa REAL,
    medicion REAL,
    actividad REAL,
    tiempo REAL
)
""")

conn.commit()

# ---------------------------
# Funciones
# ---------------------------

def calcular_actividad_cps(cps, eficiencia, masa):
    actividad = (cps * 4 * math.pi * DISTANCIA**2 * FACTOR_CORRECCION) / (eficiencia * masa)
    return actividad

def calcular_actividad_dosis(dosis, gamma, masa):
    actividad = (dosis * DISTANCIA**2 * FACTOR_CORRECCION) / (gamma * masa)
    return actividad

def calcular_tiempo_decaimiento(A0, nivel, T12):
    if A0 <= nivel:
        return 0
    t = (T12 / math.log(2)) * math.log(A0 / nivel)
    return t

# ---------------------------
# Interfaz
# ---------------------------

st.title("Gestión de Desechos Radiactivos")
st.write("Estimación de actividad y tiempo de resguardo")

bulto = st.text_input("Número de bulto")

radionuclido = st.selectbox(
    "Radionúclido",
    ["I-131", "Tc-99m", "Ra-223", "Lu-177", "F-18"]
)

masa = st.number_input("Masa del bulto (g)", min_value=0.0)

metodo = st.radio(
    "Método de medición",
    ["CPS", "Tasa de dosis"]
)

actividad = None

if metodo == "CPS":

    cps = st.number_input("Conteos por segundo (CPS)", min_value=0.0)
    eficiencia = st.number_input("Eficiencia del detector", min_value=0.0001)

    if st.button("Calcular actividad"):

        actividad = calcular_actividad_cps(cps, eficiencia, masa)

else:

    dosis = st.number_input("Tasa de dosis (mSv/h)", min_value=0.0)
    gamma = GAMMA[radionuclido]

    if st.button("Calcular actividad"):

        actividad = calcular_actividad_dosis(dosis, gamma, masa)

if actividad:

    st.subheader("Resultados")

    st.write(f"Actividad estimada: {actividad:.2f} Bq/g")

    T12 = HALF_LIFE[radionuclido]

    tiempo = calcular_tiempo_decaimiento(actividad, NIVEL_DISPENSA, T12)

    st.write(f"Tiempo de resguardo estimado: {tiempo:.2f} días")

    if actividad <= NIVEL_DISPENSA:
        st.success("El desecho puede liberarse")
    else:
        st.warning("Debe almacenarse para decaimiento")

    if st.button("Guardar registro"):

        cursor.execute("""
        INSERT INTO registros VALUES (?,?,?,?,?,?,?)
        """, (
            datetime.now(),
            bulto,
            radionuclido,
            masa,
            actividad,
            actividad,
            tiempo
        ))

        conn.commit()

        st.success("Registro guardado")

# ---------------------------
# Mostrar base de datos
# ---------------------------

st.subheader("Historial de registros")

df = pd.read_sql("SELECT * FROM registros", conn)

st.dataframe(df)
