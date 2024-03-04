import streamlit as st
import pandas as pd
import subprocess
import os
from PIL import Image
import glob
import shutil
import sys
import os
import openai
import time
import tiktoken
from openai import OpenAI
import sys
import site
os.environ["PYTHONPATH"] = os.path.pathsep.join(site.getsitepackages())


###############################################################################################################
st.title("🚀 Streamlit Financial Analyzer 📊")
st.sidebar.title("About this app")
st.sidebar.info(
    """
    **Welcome to our Streamlit App for Financial Analysis! 📈💹 To get started, follow these simple steps:**

    - **API Key Input:**
    Begin by entering your OpenAI API key to unlock the powerful capabilities of GPT-4, which drives this app's intelligent features 🛠️.
    
    - **Query Entry:**
        - Input your analysis request in the QUERY field. For example:
        - For plots, include "save to your query." 📊
        - For tables, include "save as CSV to your query." 🗃️
    
    - **Datafile Upload:**
    Upload your financial datafile for analysis. Our app supports various formats for a seamless user experience. 📂
    
    - **Plotting and Saving to Your Query:**
    When requesting a plot, make sure to specify "save to your query." 💾
    
    - **Table Creation and Saving as CSV to Your Query:**
    For tables, explicitly add "save as CSV to your query" to generate the table and save it as a CSV file. 💻
    
    - **Powered by GPT-4:**
    Please be patient, as our app powered by GPT-4 may take some time to generate comprehensive analysis results. ⌛
    
    """
)
key = st.text_input("Enter your OpenAI key")
client = OpenAI(api_key= key)

def llm_gpt4(text, system_message, delimiter="####", print_response=False, retries=3, sleep_time=10):
    while retries > 0:
        # Define messages with the user's input and a system message
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"{delimiter}{text}{delimiter}"}
        ]

        # Calculate max_tokens for output/completion
        encoding = tiktoken.encoding_for_model("gpt-4-0613")
        max_tokens = 8000 - (len(encoding.encode(text)) + len(encoding.encode(system_message))) - 13

        # Call to LLM model
        try:
            completion = client.chat.completions.create(
                model="gpt-4-0613",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0
            )
            response = completion.choices[0].message.content
            if print_response:
                print(response)
            break
        except openai.RateLimitError as e:
            print('Catching RateLimitError, retrying in 1 minute...')
            retries -= 1
            time.sleep(sleep_time)

    return response
################################################################################################################


# Function to run the code and return the output
def run_code_and_get_output(script_content):
    script_filename = 'temp_script.py'
    with open(script_filename, 'w', encoding='utf-8') as file:
        file.write(script_content)

    try:
        script_output = subprocess.check_output(['python', script_filename], universal_newlines=True)
        return script_output
    except subprocess.CalledProcessError as e:
        return f"Error running the script:\n{e}"
    finally:
        # Remove the temporary script file
        os.remove(script_filename)

# Get user input (replace this with your method of obtaining user input)
user_input = st.text_input("Input your Query")

# File uploader for the parquet file
data_file = st.file_uploader("Upload your Data")

if data_file is not None:
    with open(os.path.join(os.getcwd(), data_file.name), 'wb') as f:
        f.write(data_file.getvalue())

# Check if a file has been uploaded
if data_file is not None:
    with st.spinner("Analyzing data..."):
        data = pd.read_parquet(data_file)
        df_reset = data.reset_index()
        change_index = df_reset['symbol'].ne(df_reset['symbol'].shift())
        df_reset['symbol'] = df_reset['symbol'].ffill()
        data_columns = df_reset.columns
        statement = "These are the columns of my dataset:"
        final_text = "\n".join([statement] + list(data_columns))

        prompt = f"The dataframe is a parquet dataframe named {data_file.name}.\
        {final_text}, write a python code to {user_input}\
        The column timestamp are similar for the groups in the symbol column so comparison should be made based on the timestamp\
        I have this code already\
        data = pd.read_parquet('{data_file.name}')\
        df_reset = data.reset_index()\
        change_index = df_reset['symbol'].ne(df_reset['symbol'].shift())\
        df_reset['symbol'] = df_reset['symbol'].ffill()\
        The only categorical column is 'symbol' which has all the stock names\
        Please note, when you are asked to do computation using two or more 'symbol' column values, create a subset dataframe for each on join on the timestamp column.\
        please note, just return the code block and do not add any text explaining the code"

        # Run the code and get the output
        system_message = "This is a stock market data\
        Write an executable python code\
        please note, just return the code block and do not add any text explaining the code."

        response = llm_gpt4(prompt, system_message, delimiter="####", print_response=True, retries=3, sleep_time=10)
        response_without_code_blocks = response.replace('```python', '').replace('```', '')

        # Display the output based on its type
        output = run_code_and_get_output(response_without_code_blocks)

    current_directory = os.getcwd()

    # List all files in the directory
    files = os.listdir(current_directory)

    # Filter out image files (you can extend the list of image extensions)
    image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

    if image_files:
        for image_file in image_files:
            image_path = os.path.join(current_directory, image_file)
            image = Image.open(image_path)
            st.image(image, caption=image_file, use_column_width=True)
    else:
        csv_files = [f for f in os.listdir(current_directory) if f.endswith('.csv')]
        if csv_files:
            for csv_file in csv_files:
                csv_path = os.path.join(current_directory, csv_file)
                data = pd.read_csv(csv_path)
                st.table(data)
        else:
            " "
       
       
    files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif','.csv','.pq'))]

     
    for file in files:
        image_path = os.path.join(current_directory, file)
        os.remove(image_path)


