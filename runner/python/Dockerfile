FROM python:3.12-slim

RUN pip install --no-cache-dir \
    pandas==2.2.3 \
    numpy==2.1.3 \
    scipy==1.14.1 \
    matplotlib==3.9.3 \
    seaborn==0.13.2 \
    scikit-learn==1.5.2 \
    pyarrow==18.1.0 \
    openpyxl==3.1.5

RUN useradd -m -s /bin/bash runner
USER runner

WORKDIR /home/runner
