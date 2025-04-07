find ./src -type f -name "*.py" | while read file; do lines=$(wc -l < "$file"); if [ "$lines" -gt 300 ]; then echo "$lines $file"; fi; done | sort -nr
