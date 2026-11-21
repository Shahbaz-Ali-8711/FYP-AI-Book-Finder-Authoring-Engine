from views.reader_view import render_reader_view

def render_chatbot():
    import streamlit as st
    st.session_state["active_reader_tab"] = 1
    render_reader_view()
