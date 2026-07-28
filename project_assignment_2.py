import streamlit as st
import pandas as pd
import numpy as np

st.title("This is a calculator made by meeeeeeeeee !!!!!!!!!")

num1=st.number_input("Enter a number: ",value=1.0)
num2=st.number_input("Enter another number: ",value=1.0)

num3=num1+num2
num4=num1-num2
num5=num1*num2
num6=num1/num2
action=st.selectbox("Select an action",["sum","minus","multiplication","division"])
if action=="sum":
    st.write(f"The sum is {num3}")
elif action=="minus":
    st.write(f"The substration value is {num4}")
elif action=="multiplication":
    st.write(f"The multiplication is {num5}")
elif action=="division":
    st.write(f"The division is {num6}")


