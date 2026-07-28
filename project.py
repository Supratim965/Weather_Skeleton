import streamlit as st
import pandas as pd
import numpy as np

st.title("Supratim's Title")
st.header("Supratim's Heading")
st.subheader("Supratim's Subheading")
name=st.text_input("Enter your name: ")
if st.button("Greet me"):
    st.write(f"Hello,{name}!")
