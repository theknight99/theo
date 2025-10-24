import streamlit as st
from src.pages import home, about

def main():
    st.set_page_config(page_title="My Streamlit App", layout="wide")
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ("Home", "About"))

    if page == "Home":
        home.show()
    elif page == "About":
        about.show()

if __name__ == "__main__":
    main()