#!/bin/bash
# Start RAG MCP Server
# This script manages the persistent RAG server Docker container

CONTAINER_NAME="rag-server"
IMAGE_NAME="rag-server:latest"
DATA_DIR="/localdata/brownjer/.rag_data"
HOME_DIR="/localdata/brownjer"

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container '${CONTAINER_NAME}' already exists."
    
    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Container is already running."
        exit 0
    else
        echo "Starting existing container..."
        docker start ${CONTAINER_NAME}
        if [ $? -eq 0 ]; then
            echo "✓ Container started successfully."
        else
            echo "✗ Failed to start container."
            exit 1
        fi
    fi
else
    echo "Creating new RAG server container..."
    
    # Create data directory if it doesn't exist
    mkdir -p ${DATA_DIR}
    
    # Create the container
    docker create \
        --name ${CONTAINER_NAME} \
        -i \
        -v ${HOME_DIR}:${HOME_DIR}:ro \
        -v ${HOME_DIR}:/home/brownjer:ro \
        -v ${DATA_DIR}:/data \
        ${IMAGE_NAME}
    
    if [ $? -ne 0 ]; then
        echo "✗ Failed to create container."
        exit 1
    fi
    
    echo "✓ Container created successfully."
    
    # Start the container
    echo "Starting container..."
    docker start ${CONTAINER_NAME}
    
    if [ $? -eq 0 ]; then
        echo "✓ Container started successfully."
    else
        echo "✗ Failed to start container."
        exit 1
    fi
fi

echo ""
echo "RAG Server is ready!"
echo "To stop:    docker stop ${CONTAINER_NAME}"
echo "To restart: docker restart ${CONTAINER_NAME}"
echo "To remove:  docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME}"
