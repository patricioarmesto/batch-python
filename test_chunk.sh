#!/bin/bash

echo "=== Testing Chunk Processing Feature ==="
echo ""

echo "1. Launching ChunkJob..."
curl -X POST "http://localhost:8000/jobs/ChunkJob/launch" \
     -H "Content-Type: application/json" \
     -d '{}'
echo ""
echo "Waiting for job to complete..."
sleep 2

echo ""
echo "2. Getting execution details..."
curl -s "http://localhost:8000/executions/1" | python3 -m json.tool
echo ""

echo ""
echo "3. Getting step execution with chunk metrics..."
echo "This shows:"
echo "  - read_count: Total items read (50)"
echo "  - write_count: Items written after filtering (25 even squares)"
echo "  - filter_count: Items filtered out (25 odd squares)"
echo "  - commit_count: Number of chunks committed (5 chunks of 10)"
echo ""
curl -s "http://localhost:8000/executions/1/steps" | python3 -m json.tool
echo ""

echo "=== Chunk Processing Test Complete ==="
echo ""
echo "Summary:"
echo "- Read 50 numbers (1-50)"
echo "- Squared each number"
echo "- Filtered out odd squares (kept only even squares)"
echo "- Wrote results in chunks of 10 items"
echo "- Committed after each chunk (5 total commits)"
