import os

import requests
import streamlit as st
import pandas as pd
import numpy as np

st.title("Weather App")

cityName = st.text_input("Enter your city name", placeholder="Enter your city name, Eg:London")
api_key = st.secrets.get("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY")

if not api_key:
    st.warning("Set OPENWEATHER_API_KEY in Streamlit secrets or as an environment variable.")
elif cityName:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={cityName}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    st.write(data)
