from langchain.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import Ollama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from dotenv import load_dotenv
import streamlit as st
import os
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory


current_dir = os.path.dirname(os.path.abspath(__file__))
PARENT_dIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
ROOT_DIR = os.path.abspath(os.path.join(PARENT_dIR, os.pardir))

if "history" not in st.session_state:
    st.session_state.history = []

load_dotenv()
st.header("Smart Eye chat")

os.environ["GOOGLE_API_KEY"] = os.environ["API_KEY"]
genai.configure(api_key=os.environ["API_KEY"])
model = ChatGoogleGenerativeAI(
    model="gemini-pro", temperature=0.1, convert_system_message_to_human=True
)
memory = ConversationBufferMemory(memory_key="chat_history", input_key="question")

# Vector Database
persist_directory = ROOT_DIR  # Persist directory path
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"}
)

vectordb = Chroma(
    persist_directory=persist_directory,
    embedding_function=embeddings,
    collection_name="smarteye",
)

print("Vector DB Loaded\n")

# Quering Model
# query_chain = RetrievalQA.from_chain_type(llm=model, retriever=vectordb.as_retriever())

prompt_template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:"""
my_prompt = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)


query_chain = ConversationalRetrievalChain.from_llm(
    llm=model,
    retriever=vectordb.as_retriever(),
    verbose=True,
    combine_docs_chain_kwargs={"prompt": my_prompt},
    memory=memory,
)


for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


prompt = st.chat_input("Post your query")
if prompt:
    st.session_state.history.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("💡Thinking"):
        response = query_chain({"question": prompt})
        print(response)
        st.session_state.history.append(
            {"role": "Assistant", "content": response["answer"]}
        )

        with st.chat_message("Assistant"):
            st.markdown(response["answer"])
