import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..config.db import reports_collection
from typing import List
from fastapi import UploadFile

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rbac-diagnosis-index")
UPLOAD_DIR_RAW = os.getenv("UPLOAD_DIR", "./uploaded_reports")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Normalize upload directory path at module level (handle Windows/Unix paths)
UPLOAD_DIR_PATH = Path(UPLOAD_DIR_RAW)
if UPLOAD_DIR_PATH.is_absolute() and str(UPLOAD_DIR_PATH).startswith('/') and os.name == 'nt':
    # Convert Unix-style absolute path to relative on Windows
    UPLOAD_DIR_PATH = Path(UPLOAD_DIR_RAW.lstrip('/'))
UPLOAD_DIR_PATH.mkdir(parents=True, exist_ok=True)

# initialize pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    spec = ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    existing_indexes = [i["name"] for i in pc.list_indexes()]
    
    if PINECONE_INDEX_NAME not in existing_indexes:
        pc.create_index(name=PINECONE_INDEX_NAME, dimension=768, metric="dotproduct", spec=spec)
        while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)
    
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    import logging
    logging.error(f"Failed to initialize Pinecone: {str(e)}")
    raise ValueError(f"Pinecone initialization failed: {str(e)}")


async def load_vectorstore(uploaded_files:List[UploadFile],uploaded:str,doc_id:str):
    """
        Save files, chunk texts, embed texts, upsert in Pinecone and write metadata to Mongo
    """
    if not uploaded_files:
        raise ValueError("No files provided for upload")
    
    # Use the normalized upload directory path
    upload_dir = UPLOAD_DIR_PATH
    
    # Use the correct Google embedding model name (gemini-embedding-001)
    embed_model=GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        output_dimensionality=EMBEDDING_DIM,
    )
    
    all_chunks = []
    all_texts = []
    all_ids = []
    all_metadatas = []
    saved_files = []
    total_chunks = 0

    try:
        # Process each uploaded file
        for file in uploaded_files:
            if not file.filename:
                continue
                
            filename = Path(file.filename).name
            if not filename.lower().endswith('.pdf'):
                raise ValueError(f"File {filename} is not a PDF file")
            
            save_path = upload_dir / f"{doc_id}_{filename}"
            
            # Read and save file content
            content = await file.read()
            if not content:
                raise ValueError(f"File {filename} is empty")
            
            with open(save_path, "wb") as f:
                f.write(content)
            
            saved_files.append(filename)
            
            # Load PDF pages
            try:
                loader = PyPDFLoader(str(save_path))
                documents = loader.load()
            except Exception as e:
                raise ValueError(f"Failed to load PDF {filename}: {str(e)}")
            
            if not documents:
                raise ValueError(f"PDF {filename} contains no readable content")
            
            # Split into chunks
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            chunks = splitter.split_documents(documents)
            
            if not chunks:
                raise ValueError(f"No text chunks extracted from {filename}")
            
            # Prepare data for this file
            start_idx = total_chunks
            texts = [chunk.page_content for chunk in chunks]
            ids = [f"{doc_id}-{start_idx + i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": filename,
                    "doc_id": doc_id,
                    "uploader": uploaded,
                    "page": chunk.metadata.get("page", None),
                    "text": chunk.page_content[:2000]  # store snippet in metadata (avoid huge fields)
                }
                for chunk in chunks
            ]
            
            all_chunks.extend(chunks)
            all_texts.extend(texts)
            all_ids.extend(ids)
            all_metadatas.extend(metadatas)
            total_chunks += len(chunks)
        
        if not all_texts:
            raise ValueError("No text content extracted from uploaded files")
        
        # Get embeddings in thread
        try:
            embeddings = await asyncio.to_thread(embed_model.embed_documents, all_texts)
        except Exception as e:
            raise ValueError(f"Failed to generate embeddings: {str(e)}")
        
        # Upsert to Pinecone - run in thread to avoid blocking
        def upsert():
            try:
                vectors = list(zip(all_ids, embeddings, all_metadatas))
                index.upsert(vectors=vectors)
            except Exception as e:
                raise ValueError(f"Failed to upsert vectors to Pinecone: {str(e)}")
        
        await asyncio.to_thread(upsert)
        
        # Save report metadata in MongoDB
        try:
            reports_collection.insert_one({
                "doc_id": doc_id,
                "filename": saved_files[0] if len(saved_files) == 1 else saved_files,  # Single file or list
                "uploader": uploaded,
                "num_chunks": total_chunks,
                "uploaded_at": time.time()
            })
        except Exception as e:
            # Log error but don't fail the upload if MongoDB write fails
            # The vectors are already in Pinecone
            import logging
            logging.error(f"Failed to save metadata to MongoDB: {str(e)}")
            raise ValueError(f"Failed to save metadata: {str(e)}")
            
    except Exception as e:
        # Clean up saved files on error
        for filename in saved_files:
            try:
                file_path = upload_dir / f"{doc_id}_{filename}"
                if file_path.exists():
                    file_path.unlink()
            except:
                pass
        raise