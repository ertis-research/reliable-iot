FROM python:3.4.10

RUN mkdir -p /usr/src/IoT_Monitor

WORKDIR /usr/src/IoT_Monitor  # specifying the working dir inside the container

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

#WE RUN OUR APP
RUN chmod +x ./start.sh
CMD ["./start.sh"]
