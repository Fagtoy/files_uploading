import os

import requests


CHUNK_SIZE = 1000


# HERE IS OUR GENERATOR
def read_in_chunks(file_object, CHUNK_SIZE):
    while True:
        data = file_object.read(CHUNK_SIZE)
        if not data:
            break
        yield data


# END GENERATOR - THE REST IS FOR CONTEXT / DISCUSSION
def upload(file, url):
    content_name = str(file)
    content_path = os.path.abspath(file)
    content_size = os.stat(content_path).st_size
    print(content_name, content_path, content_size)

    file_object = open(content_path, "rb")
    index = 0
    headers = {}

    for chunk in read_in_chunks(file_object, CHUNK_SIZE):
        offset = index + len(chunk)
        headers['Content-Range'] = 'bytes %s-%s/%s' % (index, offset - 1, content_size)
        headers['Authorization'] = 'AUTH_STRING'
        index = offset
        try:

            file = {"file": chunk}
            r = requests.post(url, files=file, headers=headers)
            print(r.json())
            print("r: %s, Content-Range: %s" % (r, headers['Content-Range']))
        except Exception as e:
            print(e)
