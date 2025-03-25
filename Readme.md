# Metadata Extraction API

## Overview

This project provides a **REST API** to extract **contract metadata** such as:
- Award Criteria
- Solvency Criteria
- Special Execution Conditions

The extraction is based on **text documents** using **OpenAI's GPT-4o-mini** model.  
The API processes **raw text** input and returns a structured JSON output with the extracted information.

---

## ✅ Features

- 📡 **REST API** for contract metadata extraction.
- 🤖 Powered by **OpenAI GPT-4o-mini**.
- 📄 Supports **plain text** as input.
- 🧠 Automatic extraction of 3 categories:
  - **Award Criteria**
  - **Solvency Criteria**
  - **Special Execution Conditions**
- 📜 Logging system.
- 🐳 **Dockerized** for easy deployment.

---

## 📂 Project Structure

```
.
├── app
│   ├── main.py               # Main Flask application
│   └── requirements.txt      # Python dependencies
├── .env                      # Environment variables (API key)
├── .gitignore                # Git ignore file
├── Dockerfile                # Docker build file
├── docker-compose.yml        # Docker Compose setup
└── README.md                 # This documentation
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-repo/metadata-extraction-api.git
cd metadata-extraction-api
```

### 2️⃣ Set OpenAI API Key

Create a `.env` file in the root directory and add your OpenAI API key:

```ini
OPENAI_API_KEY=sk-your-api-key
```

You can obtain an API key by registering at **[OpenAI's API platform](https://platform.openai.com/signup/)**.

---

## 🐳 Run with Docker

### 1️⃣ Build the Docker Image

```bash
docker build -t metadata-api .
```

### 2️⃣ Run the API in a Container

```bash
docker run -p 5000:5000 --env-file .env metadata-api
```

### 3️⃣ Run with Docker Compose (recommended)

```bash
docker-compose up --build
```

This will expose the API at `http://localhost:5000/extract_metadata`.

---

## 🚀 API Usage

### Endpoint

```
POST /extract_metadata
```

### Request Body (JSON)

| Field  | Type   | Description               |
|--------|--------|---------------------------|
| `text` | string | **Plain text content** to analyze |

### Example Request (cURL)

```bash
curl -X POST "http://localhost:5000/extract_metadata" -H "Content-Type: application/json" -d '{
  "text": "This contract is awarded based on financial and technical criteria..."
}'
```

### Example Response (JSON)

```json
{
  "criterios_adjudicacion": "Award criteria extracted...",
  "criterios_solvencia": "Solvency criteria extracted...",
  "condiciones_especiales": "Special conditions extracted..."
}
```

---

## ⚠️ Input Format Requirements

- The `text` field must contain **plain text**.
- The API **automatically processes large text inputs** by splitting them into smaller sections before analysis.

---

## 📜 Logging

- Logs are printed directly to the console when running the container.
- You can extend logging to file inside `app/main.py` if needed.

---

## 🛑 Stopping and Removing Containers

To stop and remove the containers:

```bash
docker-compose down
```

To prune unused images and containers:

```bash
docker system prune -a
```

---

## ✅ Example `.env` file

```ini
OPENAI_API_KEY=sk-your-openai-api-key
```

---

## 🚀 Run without Docker (Optional)

If you want to run it locally without Docker:

### 1️⃣ Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r app/requirements.txt
```

### 3️⃣ Run the Flask App

```bash
python app/main.py
```

API will be available at `http://localhost:5000/extract_metadata`.

---

This version is optimized for **direct text-based metadata extraction** and supports **large text inputs** efficiently. 🚀

## Acknowledgements

This work has received funding from the NextProcurement European Action (grant agreement INEA/CEF/ICT/A2020/2373713-Action 2020-ES-IA-0255).

<p align="center">
  <img src="static/Images/eu-logo.svg" alt="EU Logo" height=100 width="200" style="margin-right: -27px;">
  <img src="static/Images/nextprocurement-logo.png" alt="Next Procurement Logo" height=100 width="200">
</p>