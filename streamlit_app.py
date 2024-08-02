import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import psycopg2
from psycopg2 import OperationalError

# Access API KEY
genai.configure(api_key=st.secrets.API_KEY)
# Select a model
model = genai.GenerativeModel('gemini-1.5-flash')
# Define your connection string
conn_string = st.secrets["conn_string"]
 
# # Establish a connection to the PostgreSQL database
def get_connection():
    try:
        conn = psycopg2.connect(conn_string)
        st.write("connection established")
        return conn
    except OperationalError as e:
        st.error(f"Could not connect to the database: {e}")
        return None

conn = get_connection()

# Insert data into the table
def insert_data(package_id, app_name, female_centric):
    
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
            if conn is None:
                conn = get_connection()
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
            st.write("AI Model Response for row", index)
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
        conn.close()