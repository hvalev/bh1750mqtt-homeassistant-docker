FROM python:3.9.5-alpine3.12
COPY requirements.txt bh1750.py bh1750mqtt.py ./
RUN apk add gcc make python3-dev libffi-dev i2c-tools-dev musl-dev && \
    pip3 install -r requirements.txt --no-cache-dir && \
    apk del gcc make python3-dev libffi-dev i2c-tools-dev musl-dev
CMD [ "python3", "-u", "bh1750mqtt.py" ]