FROM python:alpine3.24

WORKDIR /app

# creating a folder for logs
RUN mkdir -p /opt/logs

#copying files from local machine (for portainer these have to be uploaded via web gui)
COPY . .

#resolving the requirements for the python app (requirements file has to be uploaded
RUN pip install --no-cache-dir -r requirements.txt

#setting the cronjob(s) containing the start of the python app (crontab file has to be uploded too)
RUN crontab crontab

#executing cron in foreground mode
CMD ["crond", "-f"]
