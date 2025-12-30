#!/bin/bash
# Reset demo to clean state - restore code and clear agent outputs

cd "$(dirname "$0")"

# Restore calculator files from git
git checkout HEAD -- calculator.py test_calculator.py

# Clean enhancement directories - keep only the .md spec files
for dir in enhancements/*/; do
    find "$dir" -mindepth 1 -maxdepth 1 ! -name "*.md" -exec rm -rf {} +
done

echo "Demo reset complete"
