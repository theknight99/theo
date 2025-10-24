import streamlit as st

def home():
    st.title("Welcome to My Streamlit App")
    st.write("This is the home page of the application.")
    st.sidebar.header("Navigation")
    st.sidebar.markdown("[About](./about)")

if __name__ == "__main__":
    home()