# debian with Python preinstalled
FROM python:3.7-slim-buster

# copy dependency information
COPY requirements.txt /

# install Python packages
RUN /usr/local/bin/python -m pip install --upgrade pip && pip install -r /requirements.txt

# copy sources

COPY model.proto /
COPY license.json /

RUN mkdir /app

WORKDIR /app
COPY server.py /app/

# compile protobuf to workdir
RUN python3 -m grpc_tools.protoc --python_out=. --proto_path=/ --grpc_python_out=. model.proto

EXPOSE 8061

# run server
CMD python3 server.py
