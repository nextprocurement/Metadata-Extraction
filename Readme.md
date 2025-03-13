# Metadata Extraction from documents

## Overview

This project provides an automated pipeline to extract key metadata from legal and administrative documents, focusing on **"Pliego de cláusulas administrativas"**. The system uses **LangChain**, **OpenAI GPT-4o-mini**, and **FAISS** for semantic search and language model-based extraction.

---

## Features

- ✅ Extraction of:
  - **Award Criteria**
  - **Solvency Criteria**
  - **Special Execution Conditions**
- ✅ Uses **GPT-4o-mini** via LangChain.
- ✅ Embedding generation and FAISS vector storage.
- ✅ Automatic retries on rate-limit errors.
- ✅ Logging of all processes and error handling.
- ✅ Results saved in JSON format.


