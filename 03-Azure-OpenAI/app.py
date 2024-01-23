import openai
from flask import Flask
from flask import request
from PyPDF2 import PdfReader
from langchain.document_loaders import TextLoader
import itertools
import uuid
from werkzeug.utils import secure_filename
import os, json, boto3 
import shutil
import pinecone
from tqdm import tqdm
import time
from langchain.document_loaders.csv_loader import CSVLoader
import tiktoken
from service import rds_connect
import awsgi, fitz


app = Flask(__name__)
app.config["TIMEOUT"] = 60  # sets the timeout limit to 60 seconds

#load_dotenv()

pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEYS")
pinecone_environment = os.getenv("ENVIRONMENT")

#azure
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPEN_API_KEYS")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"


pdf_text = []

s3 = boto3.client('s3')
s3_bucket_name='use-s3-bucket-as-input'

def initialize_pinecone():
    pinecone.init(api_key=PINECONE_API_KEY, environment=pinecone_environment)


def delete_existing_pinecone_index():
    if pinecone_index_name in pinecone.list_indexes():
        pinecone.delete_index(pinecone_index_name)


def create_pinecone_index(index_name):
    pinecone.create_index(name=index_name, dimension=1536, metric="cosine", shards=1)
    pinecone_index = pinecone.Index(name=index_name)
    return pinecone_index

def get_pdf_text(file_path, bucket_name, file_type):
    print("get_pdf_text")
    text = ""

    # Download the PDF file from S3
    response = s3.get_object(Bucket=bucket_name, Key=file_path)
    pdf_content = response['Body'].read()
    
    if file_type == 1:
        # for pdf in pdf_docs:
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")

        # Extract text from each page
        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            text += page.get_text()
             
    # if file_type == 1:
    #     # for pdf in pdf_docs:
    #     pdf_reader = PdfReader(file_path)
    #     for page in pdf_reader.pages:
    #         text += page.extract_text()

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
    print("Split text into chunks")
    words = text.split()
    text_chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        text_chunks.append(chunk)
    return text_chunks


def batch_upsert(text_chunks, user_id, deployment_id, batch_size=10):
    print("Batch Upsert operation.")
    try:
        # create vectors to upsert
        vectors_to_upsert = []
        for chunk in tqdm(text_chunks):
            id = uuid.uuid4().hex
            chunk_embedding = get_embedding(chunk)
            vectors_to_upsert.append((id, chunk_embedding, {"text": chunk}))

        # upsert in batches
        batch_size = 10
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
    """Get embedding using OpenAI"""
    try:
        response = openai.Embedding.create(
            input=chunk,
            engine="text-embedding-ada-002"
        )
        embedding = response["data"][0]["embedding"]
    except openai.error.RateLimitError:
        print("************* Facing rate limit")
        time.sleep(60)
        response = openai.Embedding.create(
            input=chunk,
            engine="text-embedding-ada-002"
        )
        embedding = response["data"][0]["embedding"]
    
    return embedding

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

def get_response_from_openai_query(query, documents, prompt):
    """Get ChatGPT api response"""
    # prompt = get_prompt_for_query(query, documents)
    print("prompt1", prompt)
    print(query)
    prompt = prompt.format(documents=documents, query=query)
    print("prompt2", prompt)
    messages = [{"role": "user", "content": prompt}]
    print(messages)
    response = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=messages,
        temperature=0,
        max_tokens=800,
        top_p=1,
    )
    number_of_tokens = num_tokens_from_messages(messages)
    print(response["choices"][0])  
    if response["choices"][0]['finish_reason'] == 'stop': 
        return response["choices"][0]["message"]["content"], number_of_tokens
    else:
        print(response["choices"][0]['finish_reason'])
        return response["choices"][0]["message"]

def get_response_from_openai_chat(query, documents, prompt):
    """Get ChatGPT api response"""
    # prompt = get_prompt_for_query(query, documents)
    print("prompt1", prompt)
    print(query)
    prompt = prompt.format(documents=documents, query=query)
    print("prompt2", prompt)
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        engine="gpt-35-turbo",
        messages=messages,
        temperature=0,
        max_tokens=800,
        top_p=1,
    )
    number_of_tokens = num_tokens_from_messages(messages)
    return response["choices"][0]["message"]["content"], number_of_tokens


def get_prompt_for_query(query, documents):
    """Build prompt for question answering"""
    template = """
    You are given a paragraph and a query. You need to answer the query on the basis of paragraph. If the answer is not contained within the text below, say \"Sorry, I don't know. Please try again.\"\n\nP:{documents}\nQ: {query}\nA:
    """
    final_prompt = template.format(documents=documents, query=query)
    return final_prompt


def search_for_query(user_id, deployment_id, query, prompt, model):
    """Main function to search answer for query"""
    query_embedding = get_embedding(query)
    query_response = pinecone_index.query(
        namespace=f"namespace_{user_id}_{deployment_id}",
        vector=query_embedding,
        top_k=3,
        include_metadata=True,
    )
    documents = [match["metadata"]["text"] for match in query_response["matches"]]
    documents_as_str = "\n".join(documents)
    if model == "chat":
        response, tokens = get_response_from_openai_chat(query, documents_as_str, prompt)
    elif model == "query":
        response, tokens = get_response_from_openai_query(query, documents_as_str, prompt)
    return response, tokens


def remove_pdfs(user_id, deployment_id):
    # Get the Pinecone Index object for the target namespace
    sp_name = f"namespace_{user_id}_{deployment_id}"
    # Delete all vectors from the target namespace
    delete_response = pinecone_index.delete(delete_all=True, namespace=sp_name)
    return delete_response


# @app.route("/upload", methods=["POST"])
# def upload():
#     user_id = request.form["user_id"]
#     deployment_id = request.form["deployment_id"]
#     files = request.files.getlist("files")
#     USER_DIR = f"uploaded_files/{user_id}"
#     DEPLOYMENT_DIR = f"{USER_DIR}/{deployment_id}"
#     if files[0].filename == "":
#         return "Please select the pdf file."
#     else:
#         if not os.path.exists(DEPLOYMENT_DIR):
#             os.makedirs(DEPLOYMENT_DIR)

#         for file in files:
#             filename = secure_filename(file.filename)
#             file.save(f"{DEPLOYMENT_DIR}/{filename}")
#         return "files saved successfully"


@app.route("/train", methods=["POST"])
def train():
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    user_folder = f'uploaded_files/{user_id}/'
    deployment_folder = f'{user_folder}{deployment_id}/'
    USER_PROCESSED_FILE_DIR = f"processed_files/{user_id}/{deployment_id}/"

    # Check if user folder exists
    user_exists = any(obj['Key'] == user_folder for obj in s3.list_objects_v2(Bucket=s3_bucket_name)['Contents'])
    if not user_exists:
        return f"No files to train. Please upload new file to '{deployment_folder}'' in S3 bucket '{s3_bucket_name}'"

    # Check if deployment folder exists
    deployment_exists = any(obj['Key'] == deployment_folder for obj in s3.list_objects_v2(Bucket=s3_bucket_name)['Contents'])
    if not deployment_exists:
        return f"No files to train. Please upload new file to '{deployment_folder}'' in S3 bucket '{s3_bucket_name}'"

    #Read all .pdf files from the deployment folder
    objects = s3.list_objects(Bucket=s3_bucket_name, Prefix=deployment_folder)['Contents']
    
    print(objects) 

    for obj in objects:
        
        print(obj['Key']) 
        
        if obj['Key'].endswith('.pdf'):
            print("file is pdf")
            file_path = obj['Key']
            pdf_text = get_pdf_text(file_path, s3_bucket_name, file_type=1)
            
        elif obj['Key'].endswith('.txt'):
            print("file is txt")
            file_path = obj['Key']
            pdf_text = get_pdf_text(file_path, s3_bucket_name, file_type=2)
            
        elif obj['Key'].endswith('.csv'):
            print("file is csv")
            file_path = obj['Key']
            pdf_text = get_pdf_text(file_path, s3_bucket_name, file_type=3) 
            
        else:
            continue 

        # segment raw pdf text into chunks
        text_chunks = split_text_into_chunks(pdf_text)

        # create embeddings of chunks and batch upsert
        upsert_status = batch_upsert(
            text_chunks, user_id, deployment_id, batch_size=10
        )
        print(upsert_status)
        if upsert_status:
            
            # Check if USER_PROCESSED_FILE_DIR exists, create if not
            user_exists = any(obj['Key'] == USER_PROCESSED_FILE_DIR for obj in s3.list_objects_v2(Bucket=s3_bucket_name)['Contents'])
            if not user_exists:
                s3.put_object(Bucket=s3_bucket_name, Key=USER_PROCESSED_FILE_DIR, Body='')
                
            # Move the file to USER_PROCESSED_DIR
            
            file_name = os.path.basename(file_path)
            destination_key = f"{USER_PROCESSED_FILE_DIR}{file_name}" 
            
            s3.copy_object(
                Bucket=s3_bucket_name,
                CopySource={'Bucket': s3_bucket_name, 'Key': obj['Key']}, 
                Key=destination_key
            )
            # Delete the original object
            s3.delete_object(
                Bucket=s3_bucket_name,
                Key=obj['Key']
            )         
            
            # update DB
            print("updating DB")
            db_session.update_status(user_id, deployment_id, status=1)
            
        else:
            print("to be resolved db issue")
            db_session.update_status(user_id, deployment_id, status=0)
            # return "There was an error in upsert operation."
                
    return "Training Complete"


@app.route("/query", methods=["POST"])
def query():
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    question = request.form["question"]
    prompt = request.form["prompt"]
    response, tokens = search_for_query(user_id, deployment_id, question, prompt, model = "query")
    return {"response":response, "tokens":tokens}

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.form["user_id"]
    deployment_id = request.form["deployment_id"]
    question = request.form["question"]
    prompt = request.form["prompt"]
    response, tokens = search_for_query(user_id, deployment_id, question, prompt, model = "chat")
    return {"response":response, "tokens":tokens}


@app.route("/remove", methods=["POST"])
def remove():
    response = remove_pdfs(request.form["user_id"], request.form["deployment_id"])
    return "remove successful"


print("Creating DB session...")
global db_session
db_session = rds_connect()
print("DB Connection successful") 

def lambda_handler(event,context):
    print(event)
    
    if event['rawQueryString']:
        
        if 'AI-KEY' in event['queryStringParameters']:
            
            print("AI-KEY query string exists. Using the one provided from AI-KEY.")
            openai.api_key = event['queryStringParameters']['AI-KEY']
            
    else:
        event['queryStringParameters'] = {} 
    
    # print(openai.api_key) 
    event['httpMethod'] = event['requestContext']['http']['method']
    event['path'] = event['requestContext']['http']['path'] 
    
    print(event)
    
    initialize_pinecone()
    global pinecone_index
    pinecone_index = pinecone.Index(pinecone_index_name)
    #print(pinecone.describe_index(pinecone_index_name))

    ResponseToApi = awsgi.response(app, event, context)
    print(ResponseToApi)
    return ResponseToApi