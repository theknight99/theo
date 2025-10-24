import streamlit as st

def about():
    st.title("About This App")
    st.write("""
        This is a Streamlit application that demonstrates the use of various components and functionalities.
        
        ### Features
        - Interactive data visualization
        - User-friendly interface
        - Modular structure with separate pages and components
        
        ### Author
        Your Name
    """)

if __name__ == "__main__":
    about()