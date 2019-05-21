FROM python:3.6.7

RUN mkdir -p /usr/src/IoT_Database

WORKDIR /usr/src/IoT_Database  # specifying the working dir inside the container

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

RUN chmod +x ./start.sh
CMD ["./start.sh"]
