#!/bin/bash

echo "=== Testing Batch Python Service ==="
echo ""

echo "1. Testing RetryJob (with automatic retry logic)..."
curl -X POST "http://localhost:8000/jobs/RetryJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
echo ""
echo "Waiting for job to complete..."
sleep 8

echo ""
echo "2. Testing ParameterizedJob (with typed parameters)..."
curl -X POST "http://localhost:8000/jobs/ParameterizedJob/launch" \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2024-01-01", "batch_size": 100, "threshold": 0.95}'
echo ""
echo "Waiting for job to complete..."
sleep 3

echo ""
echo "3. Listing all executions..."
curl -s "http://localhost:8000/executions" | python3 -m json.tool
echo ""

echo ""
echo "4. Getting parameters for ParameterizedJob instance..."
curl -s "http://localhost:8000/instances/2/parameters" | python3 -m json.tool
echo ""

echo ""
echo "5. Getting step details for RetryJob (showing retry_count)..."
curl -s "http://localhost:8000/executions/1/steps" | python3 -m json.tool
echo ""

echo "=== Test Complete ==="
