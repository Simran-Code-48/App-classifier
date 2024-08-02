import streamlit as st
import pandas as pd
import google.generativeai as genai
import time

# -----------------------------------------------------

# # access API KEY
# genai.configure(api_key=st.secrets.API_KEY)
# # select a model
# model = genai.GenerativeModel('gemini-1.5-flash')
# # choose a prompt
# prompt = "Tell about you"
# # get a response
# response = model.generate_content(prompt)
# # response as text
# st.write(response.text)

# ------------------------------------------------------

# Access API KEY
genai.configure(api_key=st.secrets.API_KEY)
# Select a model
model = genai.GenerativeModel('gemini-1.5-flash')

# -----------------

st.title("📄 App Classifier")
st.write(
    "Upload a document conatining data , you want to classify."
)
uploaded_file = st.file_uploader(
    "Upload a document (.csv)", type=("csv")
)
if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file)
    # st.write("Table : ")
    # st.write(df.head(15))

    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].astype(str)

    if st.button("Submit"):
        # Initialize response container
        responses = []

        # Iterate over the dataframe in chunks of 15 rows
        for i in range(0, len(df), 15):
            chunk = df.iloc[i:i+15]
            prompt = (
                "We have a dataset where each row represents an app, along with its attributes. Based on this data, classify whether the app is female-centric, meaning it is primarily focused on female customers or the main consumers are females. "
                "Use provided data. Even if some data might be ambiguous or general, please make a reasoned assumption based on the descriptions and categories. Return the table {packageId, appName, true and false for female centric} only without reasoning\n\n"
                "Data is in the form :\n"
                f"package: String\n"
                f"appName: String\n"
                f"description: String\n"
                f"category: String\n"
                f"packageId: Integer\n"
                f"userCount: Integer\n\n"
                "Data:\n"
                f"{chunk.to_string(index=False)}\n\n"
            )
            
            # Send prompt to AI model
            response = model.generate_content(prompt)
            
            # Append the response to the list
            responses.append(response.text)
            
            # Display the intermediate results
            st.write("AI Model Response for chunk starting at row", i)
            st.write(response.text)
            
            st.write("-----------------------------")
            # Introduce a delay before sending the next request
            time.sleep(60)
