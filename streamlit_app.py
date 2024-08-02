# import streamlit as st
# import pandas as pd
# import google.generativeai as genai
# import time
# import psycopg2

# # -----------------------------------------------------

# # # access API KEY
# # genai.configure(api_key=st.secrets.API_KEY)
# # # select a model
# # model = genai.GenerativeModel('gemini-1.5-flash')
# # # choose a prompt
# # prompt = "Tell about you"
# # # get a response
# # response = model.generate_content(prompt)
# # # response as text
# # st.write(response.text)

# # ------------------------------------------------------

# # Access API KEY
# genai.configure(api_key=st.secrets.API_KEY)
# # Select a model
# model = genai.GenerativeModel('gemini-1.5-flash')
# # Define your connection string
# conn_string = st.secrets["conn_string"]


# # Establish a connection to the PostgreSQL database
# def get_connection():
#     try:
#         conn = psycopg2.connect(conn_string)
#         return conn
#     except OperationalError as e:
#         st.error(f"Could not connect to the database: {e}")
#         return None
# # -----------------

# st.title("📄 App Classifier")
# st.write(
#     "Upload a document conatining data , you want to classify."
# )
# uploaded_file = st.file_uploader(
#     "Upload a document (.csv)", type=("csv")
# )
# if uploaded_file is not None:
#     # Read CSV file
#     df = pd.read_csv(uploaded_file)
#     # st.write("Table : ")
#     # st.write(df.head(15))

#     for column in df.columns:
#         if df[column].dtype == 'object':
#             df[column] = df[column].astype(str)

#     if st.button("Submit"):
#         # Initialize response container
#         responses = []

#         # Iterate over the dataframe in chunks of 15 rows
#         for i in range(0, len(df), 15):
#             chunk = df.iloc[i:i+15]
#             prompt = (
#                 "We have a dataset where each row represents an app, along with its attributes. Based on this data, classify whether the app is female-centric, meaning it is primarily focused on female customers or the main consumers are females. "
#                 "Use provided data. Even if some data might be ambiguous or general, please make a reasoned assumption based on the descriptions and categories. Return the table {packageId, appName, true and false for female centric} only without reasoning\n\n"
#                 "Data is in the form :\n"
#                 f"package: String\n"
#                 f"appName: String\n"
#                 f"description: String\n"
#                 f"category: String\n"
#                 f"packageId: Integer\n"
#                 f"userCount: Integer\n\n"
#                 "Data:\n"
#                 f"{chunk.to_string(index=False)}\n\n"
#             )
            
#             # Send prompt to AI model
#             response = model.generate_content(prompt)
            
#             # Append the response to the list
#             responses.append(response.text)
#             st.write(f"Response type: {type(response.text)}")
#             st.write(f"Response content: {response.text}")
            
#             # Display the intermediate results
#             st.write("AI Model Response for chunk starting at row", i)
#             st.write(response.text)
            
#             st.write("-----------------------------")
#             # Introduce a delay before sending the next request
#             time.sleep(60)


# ------test------
import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import psycopg2
from psycopg2 import OperationalError
import json

# Access API KEY
genai.configure(api_key=st.secrets.API_KEY)
# Select a model
model = genai.GenerativeModel('gemini-1.5-flash')
# Define your connection string
conn_string = st.secrets["conn_string"]

# Establish a connection to the PostgreSQL database
def get_connection():
    try:
        conn = psycopg2.connect(conn_string)
        return conn
    except OperationalError as e:
        st.error(f"Could not connect to the database: {e}")
        return None

conn = get_connection()

# Insert data into the table
def insert_data(package_id, app_name, female_centric):
    # conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO app_classifications (packageId, appName, femaleCentric)
                VALUES (%s, %s, %s)
            ''', (package_id, app_name, female_centric))
            conn.commit()
            cursor.close()
            st.success("Changes saved successfully!")
        except Exception as e:
            st.error(f"Error inserting data: {e}")

# -----------------

# if conn:
st.title("📄 App Classifier")
st.write("Upload a document containing data you want to classify.")
uploaded_file = st.file_uploader("Upload a document (.csv)", type=("csv"))

if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file)

    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].astype(str)
    
    if st.button("Submit"):
        # responses
        responses = []

        for index, row in df.iterrows():
            # st.write(f"Row index: {index}")
            prompt = (
                "Below is the data of an app. Based on this data, classify whether the app is female-centric, meaning it is primarily focused on female customers or the main consumers are females. Use provided data. Even if some data might be ambiguous or general, please make a reasoned assumption based on the descriptions and categories. Return the response as true or false only where true respresents female centric and false if not female centric \n"
                "\nData : {"
                f"\n\npackageId : {row['packageId']} ,"
                f"\n\ncategory : {row['category']} ,"
                f"\n\ndescription : {row['description']}" 
                "\n\n}"               
            )
            # st.write(prompt)
            # Send prompt to AI model
            response = model.generate_content(prompt)
            is_female_centric = "False"
            if "true" in response.text.lower():
                is_female_centric = "True"
            if "false" in response.text.lower():
                is_female_centric = "False"
            insert_data(row['packageId'], row['appName'], is_female_centric)
            st.write("AI Model Response for chunk starting at row", index)
            st.write("Package ID : ",row['packageId'])
            st.write(row['appName'])
            # st.write(row['packageId'])
            st.write(response.text)
            if "true" in response.text.lower():
                st.write("Female centric")
            if "false" in response.text.lower():
                st.write("Non Female centric")
            st.write("-----------------------------------------------------------------")
            time.sleep(4)

    

    # if st.button("Submit"):
    #     # Initialize response container
    #     responses = []

    #     # Iterate over the dataframe in chunks of 15 rows
    #     for i in range(0, len(df)):
    #         row = df[i]
    #         prompt = (
    #             "We have a dataset where each row represents an app, along with its attributes. Based on this data, classify whether the app is female-centric, meaning it is primarily focused on female customers or the main consumers are females. "
    #             "Use provided data. Even if some data might be ambiguous or general, please make a reasoned assumption based on the descriptions and categories. Return the response as true or false only where true respresents female centric and false if not female centric "
    #             "Data is in the form :\n"
    #             f"package: String\n"
    #             f"appName: String\n"
    #             f"description: String\n"
    #             f"category: String\n"
    #             f"packageId: Integer\n"
    #             f"userCount: Integer\n\n"
    #             "Data:\n"
    #             f"{row.to_string(index=False)}\n\n"
    #         )
            
            # # Send prompt to AI model
            # response = model.generate_content(prompt)
            # st.write("AI Model Response for chunk starting at row", i)
            # st.write(response.text)
            # if "true" in response.text:
            #     st.write("Female centric")
            # if "false" in response.text:
            #     st.write("Non Female centric")
            
    #         st.write("-----------------------------")
    #         # Introduce a delay before sending the next request
    #         time.sleep(4)
