echo "[+] Building Image..."
docker build -t subhomoy/llm-gateway-backend:latest .

echo "[+] Pushing Image to Docker Hub..."
docker push subhomoy/llm-gateway-backend:latest

echo "[+] Finished"