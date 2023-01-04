import asyncio
import os
from datetime import datetime

import aiofiles
from blacksheep import Application, json, FromHeader, Request

app = Application()


@app.router.get("/")
async def home():
    return json(
        {
            "greeting": "Hello, World!",
            "current_datetime": datetime.utcnow().isoformat(),
        }
    )


class FromIdentifierHeader(FromHeader[str]):
    name = "ID"


class FromFileNameHeader(FromHeader[str]):
    name = "FileName"


# ALWAYS WOULD RE-UPLOAD THE FILE IF AN ERROR OCCURRED PREVIOUSLY
@app.router.post("/upload_files_by_chunks")
async def upload_files_by_chunk(request: Request, identifier: FromIdentifierHeader, filename: FromFileNameHeader):
    directory = os.path.join(os.path.abspath("media"), identifier.value)
    await asyncio.get_event_loop().run_in_executor(None, os.makedirs, directory, 0o777, True)
    file_path = os.path.join(directory, filename.value)
    async with aiofiles.open(file_path, "ab") as f:
        async for chunk in request.stream():
            await f.write(chunk)
