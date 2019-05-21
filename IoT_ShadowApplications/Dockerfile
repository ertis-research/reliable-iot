FROM python:3.6.7

RUN mkdir -p /usr/src/IoT_ShadowApplications

WORKDIR /usr/src/IoT_ShadowApplications  # specifying the working dir inside the container

COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

#WE RUN OUR APP
RUN chmod +x ./start.sh
CMD ["./start.sh"]
