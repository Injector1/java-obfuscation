FROM gradle:jdk17 AS builder

WORKDIR /app

COPY . .

RUN chmod +x ./gradlew

RUN apt-get update && apt-get install -y python3 python3-pip python3-requests --no-install-recommends && rm -rf /var/lib/apt/lists/*
# RUN pip3 install requests # Replaced by apt-get install python3-requests

CMD ["python3", "run_obfuscator.py"]
