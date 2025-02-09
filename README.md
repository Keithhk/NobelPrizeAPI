# Nobel Prize Search API

This is a FastAPI-based web application that provides a searchable MongoDB database of Nobel Prize laureates.

## Prerequisites
- Docker and Docker Compose installed on your system.

## Running the Application with Docker

### 1. Clone the Repository
```sh
git clone https://github.com/keithhk/NobelPrizeAPI.git
cd NobelPrizeAPI
```

### 1. Build and Run the Containers
Run the following command to build and start the containers:
```sh
docker compose up
```

### 2. Verify the Setup
Once the containers are running, open your browser and visit:

```sh
http://127.0.0.1:8000/docs
```

### 3. Test the database search
visit the search endpoint and provide a search term. For example:

```sh
http://127.0.0.1:8000/search?query=albret%20einstein
```



