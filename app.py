# app.py  
import streamlit as st  
from backend import process_message  
from llm import extract_preferences  

def init_session_state():  
    if 'messages' not in st.session_state:  
        st.session_state.messages = []  
    if 'preferences' not in st.session_state:  
        st.session_state.preferences = {}  

def update_preferences():
    if st.session_state.messages:
        # Combine user messages into a single string for preference extraction
        combined_user_input = " ".join(
            msg["content"] for msg in st.session_state.messages if msg["role"] == "user"
        )
        extracted_prefs = extract_preferences(combined_user_input)
        if isinstance(extracted_prefs, dict) and "error" not in extracted_prefs:
            st.session_state.preferences.update(extracted_prefs)

def main():  
    st.set_page_config(page_title="Tour Planner", page_icon="🌍")
    st.title("🌍 Tour Planner")  

    # Initialize session state  
    init_session_state()  

    # Sidebar with preferences display  
    with st.sidebar:  
        st.subheader("Your Travel Preferences")
        if st.session_state.preferences:
            st.json(st.session_state.preferences)
        else:
            st.markdown("_Preferences will appear here once provided._") 

        if st.button("Clear Chat"):  
            st.session_state.messages = []  
            st.session_state.preferences = {}  
            st.rerun()  

    st.markdown("""
    ### Welcome to your personal tour planner!
    I'll help you create the perfect one-day itinerary. Please tell me:
    - 📍 Which city you'd like to visit
    - 🕒 Your available time
    - 💰 Your budget
    - 🎯 Your interests (culture, food, adventure, etc.)
    - 🏨 Your starting point (hotel/location)
    """) 

    for message in st.session_state.messages:  
        with st.chat_message(message["role"]):  
            st.write(message["content"])  

    if user_input := st.chat_input("Tell me about your travel plans..."):  
        st.session_state.messages.append({"role": "user", "content": user_input})  

        with st.chat_message("user"):  
            st.write(user_input)  

        with st.chat_message("assistant"):  
            with st.spinner("Planning your perfect day..."):  
                response = process_message(user_input, st.session_state.messages[:-1])  
                st.write(response)  

        st.session_state.messages.append({"role": "assistant", "content": response})  

        # Update preferences after each interaction  
        update_preferences()  

if __name__ == "__main__":  
    main()  
