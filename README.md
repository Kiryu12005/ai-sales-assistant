# AI Tea Shop Assistant (RAG Chatbot)

A conversational AI assistant prototype built for an online tea retailer. Customers can ask about tea recommendations, ingredients, and allergens in natural language, and the assistant answers using real product data in the brand's tone of voice.

> **Note:** This was originally scoped for a real business. Company-specific details have been removed, and the product data in this repo (`data/products.json`) is fictional example data.

## Features

- Natural language Q&A about tea recommendations, ingredients, and allergens
- **Retrieval-Augmented Generation (RAG):** relevant products are retrieved from the catalog before generating a response, so answers stay grounded in real product data instead of the model guessing
- Responses written in a consistent, defined brand tone via custom prompt templates
- Real-time chat via WebSockets
- Simple web front-end for testing the assistant in the browser

## Tech Stack

- **Python** (async/await throughout, via `AsyncOpenAI` and FastAPI's async support)
- **FastAPI** for the web API and WebSocket endpoint
- **OpenAI API** (GPT models) for query rewriting, intent detection, and response generation
- **ChromaDB** as the vector store for semantic product retrieval
- **Jinja2** for server-rendered templates
- JSON-based product catalog as the source data, embedded into ChromaDB for retrieval

## Project Structure

```
app/
├── api/
│   ├── core/          # configuration, WebSocket connection management
│   ├── data/           # data access layer (product repository, DB integration)
│   ├── services/       # intent detection, product filtering, prompt building, chat history
│   └── templates/      # web front-end (index.html)
└── webapi_main.py      # application entry point

data/
├── products.sample.json   # example product catalog (fictional data)
└── db/                     # ChromaDB vector store, built automatically from products.json on startup (not included in the repo)
```

## How It Works

1. The user sends a message over a WebSocket connection.
2. `chat_history` rewrites the message into a normalized query and classifies its intent (recommendation, price, ingredients, comparison, cross-sell, ...), also extracting a specific product name if the user refers to one.
3. If the user is clearly still talking about a product mentioned earlier in the conversation, that product is reused directly, skipping a new search.
4. Otherwise, the query is embedded and matched against the ChromaDB vector store (the RAG step), with metadata filtering (e.g. teas vs. accessories) and a result count that depends on the detected intent.
5. `intent_responder` builds the final response from the retrieved product data, the conversation so far, and the brand's tone of voice, then calls the OpenAI API.
6. The response is sent back over the WebSocket and added to the conversation history.
7. Once the conversation gets long, `chat_history` automatically summarizes older messages so the model keeps the relevant context without the prompt growing indefinitely.

## Setup

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy your own OpenAI API key to `.env`.
4. Copy the sample data so the app has a catalog to work with:
   ```
   cp data/products.sample.json data/products.json
   ```
5. Start the app:
   ```
   uvicorn app.api.webapi_main:app --reload
   ```
   The ChromaDB vector store is built automatically from the catalog on startup, no separate step needed.

## Background

This project started as a concept for a small online business that wanted to offer AI-assisted customer support. It was presented to the business but not taken into production. The code remains as a working prototype and portfolio project.