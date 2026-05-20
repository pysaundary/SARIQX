#!/bin/bash

echo "🧹 SARIQX Log Janitor Active: Searching for all .log files..."

# Check if there are any log files at all
if [ -z "$(find . -type f -name "*.log")" ]; then
    echo "✨ Clear sky! No .log files found in any directory."
    exit 0
fi

# Print the files being deleted so you know exactly what is being wiped out
echo "🔥 Wiping out the following log files:"
find . -type f -name "*.log" -print

# Mathematically execute the deletion boundary
find . -type f -name "*.log" -delete

echo "✅ Boom! Saare gande logs poori tarah saaf ho gaye hain."