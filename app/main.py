from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
import uuid

# AES Encryption setup
KEY = b'Sixteen byte key'  # 16-byte key for AES-128
BLOCK_SIZE = 16

app = FastAPI()

# Static directory for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Setting up Jinja2 Templates for the frontend
templates = Jinja2Templates(directory="app/templates")


def encrypt_file(file_data):
    cipher = AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(file_data, BLOCK_SIZE))
    return cipher.iv + ct_bytes  # IV is prepended to the encrypted data

def decrypt_file(encrypted_data):
    iv = encrypted_data[:BLOCK_SIZE]
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data[BLOCK_SIZE:]), BLOCK_SIZE)


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    file_location = f"uploads/{uuid.uuid4()}_{file.filename}"
    
    # Encrypt the file before saving it
    file_data = await file.read()
    encrypted_data = encrypt_file(file_data)
    
    with open(file_location, "wb") as f:
        f.write(encrypted_data)
    
    download_link = f"/download/{file_location.split('/')[-1]}"
    return templates.TemplateResponse("upload_success.html", {
        "request": request,
        "filename": file.filename,
        "download_link": download_link
    })


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    encrypted_file_path = f"uploads/{file_name}"
    
    if os.path.exists(encrypted_file_path):
        with open(encrypted_file_path, "rb") as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_file(encrypted_data)
        decrypted_file_path = f"downloads/decrypted_{file_name}"
        
        with open(decrypted_file_path, "wb") as f:
            f.write(decrypted_data)
        
        return FileResponse(decrypted_file_path, filename=f"decrypted_{file_name}")
    return {"error": "File not found!"}
