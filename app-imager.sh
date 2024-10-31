#!/bin/bash

# Generate a unique tag using the current timestamp
TAG=$(date +"%Y%m%d%H%M%S")

echo "[+] Building Image with tag: $TAG..."
docker build -t subhomoy/llm-gateway-backend:$TAG .

echo "[+] Tagging Image as latest..."
docker tag subhomoy/llm-gateway-backend:$TAG subhomoy/llm-gateway-backend:latest

echo "[+] Pushing Image with tag: $TAG to Docker Hub..."
docker push subhomoy/llm-gateway-backend:$TAG

echo "[+] Pushing latest tag to Docker Hub..."
docker push subhomoy/llm-gateway-backend:latest

echo "[+] Finished"
