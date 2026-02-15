from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from pykeepass import create_database
import tempfile

# Initialize FastAPI
app: FastAPI = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/json")
def get_json_template():
    # Example template
    template_data: list = [
        {"title": "Google", "username": "user@gmail.com", "password": "password123", "url": "https://google.com"},
        {"title": "Github", "username": "devuser", "password": "gitpassword", "url": "https://github.com"}
    ]
    return template_data

@app.post("/upload")
async def upload_json(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"message": "Invalid JSON"})

    # Create KDBX in memory (via temp file)
    fd, tmp_path = tempfile.mkstemp(suffix=".kdbx")
    os.close(fd)

    try:
        # Default password for the generated KDBX
        db_password: str = "password"
        kp = create_database(tmp_path, password=db_password)

        for item in data:
            kp.add_entry(kp.root_group, item.get("title", "Untitled"),
                         item.get("username", ""),
                         item.get("password", ""),
                         url=item.get("url", ""))

        kp.save()

        background_tasks.add_task(os.remove, tmp_path)
        return FileResponse(tmp_path, filename="imported.kdbx", media_type="application/octet-stream")
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return JSONResponse(status_code=500, content={"message": str(e)})

# Serve static files
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
