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

# Establish a connection to the PostgreSQL database
def get_connection():
    try:
        conn = psycopg2.connect(conn_string)
        st.success("Connected successfully")
        return conn
    except OperationalError as e:
        st.error(f"Some connection issues: {e}")
        return None

conn = get_connection()

def fetch_existing_package_ids(conn, package_ids):
    try:
        cursor = conn.cursor()
        query = '''
            SELECT packageId FROM app_classifications WHERE packageId = ANY(%s)
        '''
        cursor.execute(query, (list(package_ids),))
        existing_package_ids = {row[0] for row in cursor.fetchall()}
        cursor.close()
        return existing_package_ids
    except Exception as e:
        st.error(f"Error fetching existing package IDs: {e}")
        return set()

# Insert data into the table
def insert_data_batch(data_batch):
    if conn:
        try:
            cursor = conn.cursor()
            insert_query = '''
                INSERT INTO app_classifications (packageId, appName, femaleCentric)
                VALUES %s
                ON CONFLICT (packageId)
                DO NOTHING
            '''
            args_str = ','.join(cursor.mogrify("(%s,%s,%s)", x).decode("utf-8") for x in data_batch)
            cursor.execute(insert_query % args_str)
            conn.commit()
            cursor.close()
        except Exception as e:
            conn.rollback()
            st.error(f"Error inserting data: {e}")

# Streamlit app interface
st.title("📄 App Classifier")
st.write("Upload a document containing data you want to classify.")
uploaded_file = st.file_uploader("Upload a document (.csv)", type=("csv"))

if uploaded_file is not None:
    # Read CSV file
    df = pd.read_csv(uploaded_file)
    st.write("File has ", df.shape[0], " rows. \n")

    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].astype(str)
    if conn is None:
        conn = get_connection()
    existing_package_ids = fetch_existing_package_ids(conn, df['packageId'].astype(int).tolist())

    # Remove rows that already exist in the database
    df = df[~df['packageId'].isin(existing_package_ids)]
    st.write("After removing existing rows, file has ", df.shape[0], " rows. \n")

    if st.button("Submit"):
        progress_text = "Operation in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        total_rows = df.shape[0]

        # Collect responses in batches of 15
        responses = []
        for index, row in df.iterrows():
            if conn is None:
                conn = get_connection()

            prompt = (
                "Below is the data of an app. Based on this data, classify whether the app is female-centric, meaning it is primarily focused on female customers or the main consumers are females. Use provided data. Even if some data might be ambiguous or general, please make a reasoned assumption based on the descriptions and categories. Return the response as true or false only where true represents female centric and false if not female centric \n"
                "\nData : {"
                f"\n\npackageId : {row['packageId']} ,"
                f"\n\ncategory : {row['category']} ,"
                f"\n\ndescription : {row['description']}"
                "\n\n}"
            )

            # Send prompt to AI model
            response = model.generate_content(prompt)
            is_female_centric = "False"
            if "true" in response.text.lower():
                is_female_centric = "True"
            if "false" in response.text.lower():
                is_female_centric = "False"

            responses.append((row['packageId'], row['appName'], is_female_centric))

            # Insert in batches of 15
            if len(responses) == 15:
                insert_data_batch(responses)
                responses.clear()

            progress_text = str(int((index + 1) * 100 / total_rows)) + "% done"
            my_bar.progress((index + 1) / total_rows, text=progress_text)
            time.sleep(4)

        # Insert any remaining responses
        if responses:
            insert_data_batch(responses)

        conn.close()
