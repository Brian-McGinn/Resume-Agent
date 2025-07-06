FROM nvcr.io/nvidia/base/ubuntu:22.04_20240212

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND noninteractive

# Install required ubuntu packages for setting up python 3.10
RUN apt update && \
    apt install -y curl software-properties-common libgl1 libglib2.0-0 && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && apt install -y python3.10 && \
    apt-get clean

# Install pip for python3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

RUN rm -rf /var/lib/apt/lists/*

# Uninstall build packages
RUN apt autoremove -y curl software-properties-common

WORKDIR /tmp/demo

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 3003

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# python3.10 main.py
ENTRYPOINT ["python3.10", "main.py"]