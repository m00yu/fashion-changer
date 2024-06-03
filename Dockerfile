FROM python:3.9-slim
RUN apt-get update -y
RUN apt-get install -y libgl1-mesa-glx
#RUN apt-get install -y libglib2.0-0
RUN pip3 install --no-cache-dir fastapi==0.110.3
RUN pip3 install --no-cache-dir torch==2.3.0
RUN pip3 install --no-cache-dir torchvision==0.18.0
RUN pip3 install --no-cache-dir torchaudio==2.3.0
RUN pip3 install --no-cache-dir jinja2==3.1.4
RUN pip3 install --no-cache-dir python-multipart==0.0.9
RUN pip3 install --no-cache-dir opencv-python-headless
RUN pip3 install --no-cache-dir uvicorn
RUN pip3 install --no-cache-dir gdown

RUN mkdir /workspace/
COPY . /workspace/

WORKDIR /workspace

ENTRYPOINT ["uvicorn"]
CMD ["--host=0.0.0.0", "main:app"] 
