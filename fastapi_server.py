from fastapi import FastAPI, File, UploadFile, Form, status, Header
from fastapi.exceptions import HTTPException
import aiofiles
import os

app = FastAPI()

CHUNK_SIZE = 1024 * 1024  # adjust the chunk size as desired


# ALLOWS TO CONTINUE UPLOADING A FILE EVEN WHEN THERE WAS AN ERROR BEFORE (NOT RE-UPLOADING THE FULL FILE)
@app.post("/upload_files_by_chunks")
async def upload(identifier: str = Header(...), file: UploadFile = File(...)):
    directory = os.path.join(os.path.abspath("media"), identifier)
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, file.filename)
    try:
        async with aiofiles.open(filepath, "ab") as f:
            async for chunk in read_in_chunks_generator(file, directory):
                await f.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )
    return {"message": f"Successfuly uploaded {file.filename}"}


async def read_in_chunks_generator(file: UploadFile, directory: str):
    chunks_file_path = os.path.join(directory, f"{file.filename.rsplit('.', 1)[0]}.txt")
    try:
        async with aiofiles.open(chunks_file_path) as chunks_file:
            already_read_size = int(await chunks_file.readline())
    except FileNotFoundError:
        already_read_size = 0
    await file.seek(already_read_size)
    async with aiofiles.open(chunks_file_path, "w") as chunks_file:
        while chunk := await file.read(CHUNK_SIZE):
            yield chunk
            already_read_size += CHUNK_SIZE
            await chunks_file.seek(0)
            await chunks_file.write(str(already_read_size))
        await chunks_file.seek(0)
        await chunks_file.write(str(already_read_size))
