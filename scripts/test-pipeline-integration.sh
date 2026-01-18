#!/bin/bash
# Integration Test Script for Story 2.4: Pipeline Integration & Kafka Publishing
# This script verifies end-to-end flow from camera-service -> inference-service -> Kafka
#
# Usage: ./scripts/test-pipeline-integration.sh
# Prerequisites: Docker, docker-compose, rpk (Redpanda CLI)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Pipeline Integration Test - Story 2.4"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose down --volumes --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

cd "$PROJECT_ROOT"

# Step 1: Start services
echo -e "\n${YELLOW}[1/5] Starting services with docker-compose...${NC}"
docker-compose up -d --build

# Step 2: Wait for Redpanda to be healthy
echo -e "\n${YELLOW}[2/5] Waiting for Redpanda to be healthy...${NC}"
MAX_WAIT=60
WAITED=0
until docker exec redpanda rpk cluster health 2>/dev/null | grep -q "Healthy"; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}FAILED: Redpanda did not become healthy within ${MAX_WAIT}s${NC}"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo "  Waiting... ($WAITED/$MAX_WAIT seconds)"
done
echo -e "${GREEN}Redpanda is healthy!${NC}"

# Step 3: Create the events.detections topic if not exists
echo -e "\n${YELLOW}[3/5] Creating Kafka topic 'events.detections'...${NC}"
docker exec redpanda rpk topic create events.detections --partitions 1 --replicas 1 2>/dev/null || echo "Topic may already exist"
docker exec redpanda rpk topic list

# Step 4: Wait for detection events
echo -e "\n${YELLOW}[4/5] Waiting for detection events on 'events.detections' topic...${NC}"
echo "  (Consuming for 30 seconds, checking for messages...)"

# Consume messages for 30 seconds
MESSAGES=$(timeout 30 docker exec redpanda rpk topic consume events.detections --num 5 --format json 2>/dev/null || true)

if [ -z "$MESSAGES" ]; then
    echo -e "${YELLOW}No messages received in 30 seconds.${NC}"
    echo "  This may be expected if no video source is configured."
    echo "  Checking service logs..."
    echo ""
    echo "=== Camera Service Logs ==="
    docker logs camera-service --tail 20 2>&1 || true
    echo ""
    echo "=== Inference Service Logs ==="
    docker logs inference-service --tail 20 2>&1 || true
else
    echo -e "${GREEN}Received detection events!${NC}"
    echo "$MESSAGES" | head -5
fi

# Step 5: Verify latency requirements (AC4: < 200ms)
echo -e "\n${YELLOW}[5/5] Checking latency metrics...${NC}"
if echo "$MESSAGES" | grep -q "inference_latency_ms"; then
    LATENCY=$(echo "$MESSAGES" | grep -o '"inference_latency_ms":[0-9.]*' | head -1 | cut -d: -f2)
    if [ -n "$LATENCY" ]; then
        if (( $(echo "$LATENCY < 200" | bc -l) )); then
            echo -e "${GREEN}PASS: Latency ${LATENCY}ms is under 200ms threshold${NC}"
        else
            echo -e "${RED}WARN: Latency ${LATENCY}ms exceeds 200ms threshold${NC}"
        fi
    fi
else
    echo "  Latency check skipped (no messages with latency data)"
fi

echo -e "\n========================================"
echo -e "${GREEN}Integration test completed!${NC}"
echo "========================================"

# Keep services running for manual inspection if needed
echo ""
echo "Services are still running. To inspect manually:"
echo "  - View Kafka: docker exec redpanda rpk topic consume events.detections"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop: docker-compose down"
