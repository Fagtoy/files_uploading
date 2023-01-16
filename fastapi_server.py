import asyncio
import io
import os
from datetime import datetime

import aiofiles
from fastapi import FastAPI, File, UploadFile, status, Header
from fastapi.exceptions import HTTPException
from miniopy_async import Minio
from starlette.responses import StreamingResponse

app = FastAPI()

CHUNK_SIZE = 10 * 1024 * 1024  # adjust the chunk size as desired


@app.router.get("/")
async def home():
    return {
        "greeting": "Hello, World!",
        "current_datetime": datetime.utcnow().isoformat(),
    }


# ALLOWS TO CONTINUE UPLOADING A FILE EVEN WHEN THERE WAS AN ERROR BEFORE (NOT RE-UPLOADING THE FULL FILE)
@app.post("/upload_files_by_chunks")
async def upload(identifier: str = Header(...), file: UploadFile = File(...)):
    directory = os.path.join(os.path.abspath("media"), identifier)
    await asyncio.get_event_loop().run_in_executor(None, os.makedirs, directory, 0o777, True)
    filepath = os.path.join(directory, file.filename)
    try:
        async with aiofiles.open(filepath, "ab") as f:
            async for chunk in read_in_chunks_generator(file, filepath):
                await f.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )
    return {"message": f"Successfuly uploaded {file.filename}"}


async def read_in_chunks_generator(file: UploadFile, full_file_path: str):
    try:
        already_written_size = await asyncio.get_event_loop().run_in_executor(None, os.path.getsize, full_file_path)
    except FileNotFoundError:
        already_written_size = 0
    await file.seek(already_written_size)
    while chunk := await file.read(CHUNK_SIZE):
        yield chunk


minio_client = Minio(
    'minio:9000',
    secure=False,
    # Access and secret keys are equivalent to MINIO_ROOT_USER and MINIO_ROOT_PASSWORD in docker-compose
    access_key="MINIOUSER",
    secret_key="MINIOPASSWORD",
)


@app.post("/upload_to_minio")
async def upload_minio(identifier: str = Header(...), file: UploadFile = File(...)):
    if not await minio_client.bucket_exists(bucket_name := f"userfiles-{identifier}"):
        await minio_client.make_bucket(bucket_name)
    return await minio_client.put_object(bucket_name, file.filename, file, -1, part_size=CHUNK_SIZE)


@app.get("/get_from_minio")
async def get_minio(filename: str, identifier: str = Header(...)):
    # original url: http://minio:9000/bucket-name/filename
    # the following solution returns the file from FastAPI and not from Minio directly
    minio_response = await minio_client.get_object(f"userfiles-{identifier}", filename)
    return StreamingResponse(io.BytesIO(await minio_response.read()))
