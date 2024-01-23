import openai
from flask import Flask
from flask import request 
from PyPDF2 import PdfReader
from langchain.document_loaders import TextLoader
import itertools
import uuid
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import shutil
import pinecone
from tqdm import tqdm
from langchain.document_loaders.csv_loader import CSVLoader
import tiktoken
from service import rds_connect
import awsgi, fitz
import subprocess, base64

app = Flask(__name__)
app.config["TIMEOUT"] = 60  # sets the timeout limit to 60 seconds

#load_dotenv()

pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
openai.api_key = os.getenv("OPEN_API_KEYS")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEYS")
pinecone_environment = os.getenv("ENVIRONMENT")
pdf_text = []


def initialize_pinecone():
    pinecone.init(api_key=PINECONE_API_KEY, environment=pinecone_environment)


def delete_existing_pinecone_index():
    if pinecone_index_name in pinecone.list_indexes():
        pinecone.delete_index(pinecone_index_name)


def create_pinecone_index(index_name):
    pinecone.create_index(name=index_name, dimension=1536, metric="cosine", shards=1)
    pinecone_index = pinecone.Index(name=index_name)
    return pinecone_index


def get_pdf_text(file_path, file_type):
    print("get_pdf_text")
    text = ""
    if file_type == 1:
        data = subprocess.check_output(f"cat {file_path}", shell=True)
        pdf_document = fitz.open(stream=data, filetype="pdf")

        # Extract text from each page
        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            text += page.get_text()

        # Save the extracted text to a PDF file in /tmp directory
        with open(file_path, 'w') as pdf_file:
            pdf_file.write(text) 

    # if file_type == 1:
    #     # for pdf in pdf_docs:
    #     pdf_reader = PdfReader(file_path)
    #     for page in pdf_reader.pages:
    #         print(page.extract_text())
    #         text += page.extract_text()
    #     print("===text from get_pdf_text===") 
    #     print(text)
    #     print("===END===")

    elif file_type == 2:
        loader = TextLoader(file_path)
        loaded_files = loader.load()
        for i in loaded_files:
            text += i.page_content
    
    elif file_type == 3:
        loader = CSVLoader(file_path=file_path)
        data = loader.load()
        for i in data:
            text += i.page_content
    
    return text
        


def chunks(iterable, batch_size=100):
    """A helper function to break an iterable into chunks of size batch_size."""
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


def split_text_into_chunks(text, chunk_size=500):
    words = text.split()
    text_chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        text_chunks.append(chunk)
    return text_chunks


def batch_upsert(text_chunks, user_id, deployment_id, batch_size=10):
    try:
        # create vectors to upsert
        vectors_to_upsert = []
        for chunk in tqdm(text_chunks):
            id = uuid.uuid4().hex
            chunk_embedding = get_embedding(chunk)
            vectors_to_upsert.append((id, chunk_embedding, {"text": chunk}))

        # upsert in batches
        batch_size = 10
        ##print(f"Vectors to upsert: {vectors_to_upsert}")
        for i in tqdm(range(0, len(vectors_to_upsert), batch_size)):
            batch = vectors_to_upsert[i : i + batch_size]
            pinecone_index.upsert(
                vectors=batch, namespace=f"namespace_{user_id}_{deployment_id}"
            )
        return True
    except Exception as e:
        print("Exception in batch upsert ", str(e))
        return False


def get_embedding(chunk):
    # print("Embedding...")
    """Get embedding using OpenAI"""
    response = openai.Embedding.create(
        input=chunk,
        model="text-embedding-ada-002",
    )
    embedding = response["data"][0]["embedding"]
    return embedding 


def get_response_from_openai(documents, query, prompt):
    print("get_response_from_openai")
    # print(f"query: {query}")
    # print(f"documents : {documents}")
    # print(f"prompt: {prompt}")
    """Get Completition api response"""
    prompt = prompt.format(documents=documents, query=query)  
    print(f"=====prompt for OpenAI======:\n {prompt}") 
    response = openai.Completion.create(
        #model="text-davinci-003",
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        temperature=0,
        max_tokens=800,
        top_p=1,
    )
    tokens = num_tokens_from_string(prompt)
    print("Response from get_response_from_openai --> ")
    print(response["choices"])

    return response["choices"][0]["text"], tokens
    

def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("p50k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 4
    tokens_per_name = -1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def get_response_from_openai_chat(query, documents, prompt):
    """Get ChatGPT api response"""
    prompt = prompt.format(documents=documents, query=query)
    messages = [{"role": "user", "content": prompt}]
    number_of_tokens = num_tokens_from_messages(messages)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        max_tokens=800,
        top_p=1,
    )
    return response["choices"][0]["message"]["content"], number_of_tokens


def get_prompt_for_query(query, documents):
    """Build prompt for question answering"""
    template = """
    You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say \"Sorry, I don't know. Please try again.\"\n\nP:{documents}\nQ: {query}\nA:
    """
    final_prompt = template.format(documents=documents, query=query)
    return final_prompt


def search_for_query(user_id, deployment_id, query, prompt, model_type):
    print("search_for_query")
    """Main function to search answer for query"""
    query_embedding = get_embedding(query)
    print(pinecone_index)
    query_response = pinecone_index.query(
        namespace=f"namespace_{user_id}_{deployment_id}",
        vector=query_embedding,
        top_k=3,
        include_metadata=True,
    )
    
    #print(f"Query Response: {query_response}") 
    documents = [match["metadata"]["text"] for match in query_response["matches"]]
    #print(f"Documents: {documents}")
    documents_as_str = "\n".join(documents)
    print(f"Document as STR: {documents_as_str}") 
    
    if model_type == "query":
        response,tokens = get_response_from_openai(documents_as_str, query, prompt)
    elif model_type == "chat":
        response, tokens = get_response_from_openai_chat(query, documents_as_str, prompt)
    return response, tokens


def remove_pdfs(user_id, deployment_id):
    # Get the Pinecone Index object for the target namespace
    sp_name = f"namespace_{user_id}_{deployment_id}"
    # Delete all vectors from the target namespace
    delete_response = pinecone_index.delete(delete_all=True, namespace=sp_name)
    return delete_response


@app.route("/upload", methods=["POST"])
def upload():
    print("upload")
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    files = request.files.getlist("files")
    USER_DIR = f"uploaded_files/{user_id}"
    DEPLOYMENT_DIR = f"/tmp/{USER_DIR}/{deployment_id}"
    if files[0].filename == "":
        return "Please select the pdf file."
    else:
        if not os.path.exists(DEPLOYMENT_DIR):
            os.makedirs(DEPLOYMENT_DIR)
        print(files)
        for file in files:
            filename = secure_filename(file.filename)
            file.save(f"{DEPLOYMENT_DIR}/{filename}")
            print(f"File saved: {DEPLOYMENT_DIR}/{filename}")

        return "files saved successfully"


@app.route("/train", methods=["POST"])
def train():
    print("train")
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    USER_UPLOAD_FILE_DIR = f"/tmp/uploaded_files/{user_id}/{deployment_id}"
    USER_PROCESSED_FILE_DIR = f"/tmp/processed_files/{user_id}/{deployment_id}"


    if os.path.exists(USER_UPLOAD_FILE_DIR) and os.listdir(USER_UPLOAD_FILE_DIR):
        files = os.listdir(USER_UPLOAD_FILE_DIR)
        print(files)
        for filename in files:
            file_path = os.path.join(USER_UPLOAD_FILE_DIR, filename)
            print(file_path, file_path[-4:])
            if file_path[-4:] == ".txt":
                pdf_text = get_pdf_text(file_path, file_type=2)
            elif file_path[-4:] == ".pdf":
                pdf_text = get_pdf_text(file_path, file_type=1)
            elif file_path[-4:] == ".csv":
                pdf_text = get_pdf_text(file_path, file_type=3)

            # segment raw pdf text into chunks
            text_chunks = split_text_into_chunks(pdf_text)
            ##print(f"Text chunks: {text_chunks}")
            # create embeddings of chunks and batch upsert
            upsert_status = batch_upsert(
                text_chunks, user_id, deployment_id, batch_size=10
            )

            if upsert_status:
                # Move the file to USER_PROCESSED_DIR
                if not os.path.exists(USER_PROCESSED_FILE_DIR):
                    os.makedirs(USER_PROCESSED_FILE_DIR)
                new_file_path = os.path.join(USER_PROCESSED_FILE_DIR, filename)

                shutil.move(file_path, new_file_path)
                
                # update DB
                db_session.update_status(user_id, deployment_id, status=1)
                
            else:
                print("to be resolved db issue")
                db_session.update_status(user_id, deployment_id, status=0)
        return "Training Complete"
    else:
        return "No files to train. Please upload new file."

@app.route("/chat", methods=["POST"])   
def chat():
    print("chat")
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    question = request.form["question"]
    prompt = request.form["prompt"]
    response, no_of_tokens = search_for_query(user_id, deployment_id, question, prompt, model_type="chat")
    response = {"response":response, "tokens_count":no_of_tokens}
    return response

@app.route("/query", methods=["POST"])
def query():
    print("query")
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    question = request.form["question"]
    prompt = request.form["prompt"]
    response, number_of_tokens = search_for_query(user_id, deployment_id, question, prompt, model_type="query")
    response = {"response":response, "tokens_count":number_of_tokens}
    return response

@app.route("/remove", methods=["POST"])
def remove():
    print("remove")
    response = remove_pdfs(request.form["user_id"], request.form["deployment_id"])
    return "remove successful"

 
if __name__ == "__main__":
    app.run(host="0.0.0.0")

print("Creating DB session...")
global db_session
db_session = rds_connect()
print("DB Connection successful") 

def lambda_handler(event,context):
    print(event)
    
    print(event['requestContext']['http']['path'])
    print(event['requestContext']['http']['method'])
    
    event['httpMethod'] = event['requestContext']['http']['method']
    event['path'] = event['requestContext']['http']['path'] 
    event['queryStringParameters'] = event['rawQueryString']
    
    print(event)
    # print(context)  
    
    initialize_pinecone()
    global pinecone_index
    pinecone_index = pinecone.Index(pinecone_index_name)
    #print(pinecone.describe_index(pinecone_index_name))

    ResponseToApi = awsgi.response(app, event, context)
    print(ResponseToApi)
    return ResponseToApi