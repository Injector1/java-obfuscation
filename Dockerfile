FROM gradle:jdk17 AS builder

WORKDIR /app

COPY . .

RUN chmod +x ./gradlew

RUN apt-get update && apt-get install -y python3 python3-pip python3-requests --no-install-recommends && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python3", "run_obfuscator.py"]
