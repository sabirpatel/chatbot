import streamlit as st
import requests # Used for making HTTP requests to the Gemini API
import json     # Used for handling JSON data

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini 2.0 Flash model to generate responses. "
    "To use this app in the Canvas environment, you don't need to provide an API key, as it will be automatically handled. "
    "For external deployment, you would typically configure your API key via environment variables."
)

# In the Canvas environment, the API key for gemini-2.0-flash is handled automatically.
# For a standard Streamlit deployment, you might load it from secrets or env vars.
# For this demonstration, we'll assume it's implicitly available or set to an empty string
# as per the instruction for fetch calls in the Canvas environment.
# const apiKey = "" ensures that Canvas provides the key.
api_key = "" # Leave this empty; Canvas provides the key for gemini-2.0-flash

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.
if "messages" not in st.session_state:
    # Initialize with an empty list. Gemini typically uses 'model' for its responses.
    st.session_state.messages = []

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    # Adapt role for display: 'model' from Gemini becomes 'assistant' for display
    display_role = 'assistant' if message["role"] == 'model' else message["role"]
    with st.chat_message(display_role):
        # Assuming parts[0].text exists for simplicity in content
        if message["parts"] and len(message["parts"]) > 0 and "text" in message["parts"][0]:
            st.markdown(message["parts"][0]["text"])
        else:
            st.markdown("*(Unable to display message content)*")


# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if prompt := st.chat_input("What is up?"):

    # Store and display the current prompt.
    user_message = {"role": "user", "parts": [{"text": prompt}]}
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare chat history for the Gemini API call
    # The Gemini API expects 'user' and 'model' roles.
    chat_history_for_gemini = []
    for msg in st.session_state.messages:
        # Ensure correct role names for Gemini API
        gemini_role = 'model' if msg["role"] == 'assistant' else msg["role"]
        chat_history_for_gemini.append({"role": gemini_role, "parts": msg["parts"]})

    # Gemini API endpoint
    gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    # Prepare the payload for the API request
    payload = {
        "contents": chat_history_for_gemini
    }

    try:
        # Make the POST request to the Gemini API
        response = requests.post(gemini_api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()

        # Process the API response
        assistant_response_content = "Sorry, I could not get a response."
        if result and "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
                if "text" in candidate["content"]["parts"][0]:
                    assistant_response_content = candidate["content"]["parts"][0]["text"]
                else:
                    st.error("Gemini API response part missing 'text'.")
            else:
                st.error("Gemini API response content or parts missing.")
        else:
            st.error(f"Unexpected Gemini API response structure: {result}")

        # Store and display the assistant's response.
        assistant_message = {"role": "model", "parts": [{"text": assistant_response_content}]}
        st.session_state.messages.append(assistant_message)
        with st.chat_message("assistant"):
            st.markdown(assistant_response_content)

    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with Gemini API: {e}")
        st.session_state.messages.append({"role": "model", "parts": [{"text": f"Error: Could not connect to the API. {e}"}]})
    except json.JSONDecodeError:
        st.error("Failed to parse JSON response from Gemini API.")
        st.session_state.messages.append({"role": "model", "parts": [{"text": "Error: Failed to parse API response."}]})
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.session_state.messages.append({"role": "model", "parts": [{"text": f"An unexpected error occurred: {e}"}]})
