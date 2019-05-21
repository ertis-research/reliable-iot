FROM python:3.6.7

RUN mkdir -p /usr/src/IoT_Register

WORKDIR /usr/src/IoT_Register # specifying the working dir inside the container

# copy current dir's content to container's WORKDIR root i.e. all the contents of the web app
COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 80

#WE RUN OUR APP
RUN chmod +x ./start.sh
CMD ["./start.sh"]
