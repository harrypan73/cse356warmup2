#!/bin/bash

# Define a mapping of representation numbers to bitrates
declare -A bitrate_map=(
    ["r1"]="254000"
    ["r2"]="507000"
    ["r3"]="759000"
    ["r4"]="1013000"
    ["r5"]="1254000"
    ["r6"]="1883000"
    ["r7"]="3134000"
    ["r8"]="4952000"
)

# Loop through each generated segment file
for file in chunk_*_r*_*; do
    # Extract the representation identifier (e.g., r1, r2)
    representation=$(echo "$file" | grep -oP '_r\d+_' | grep -oP 'r\d+')
    
    # Extract the segment number from the filename (e.g., _1.m4s -> 1)
    segment_number=$(echo "$file" | grep -oP '_\d+\.m4s' | grep -oP '\d+')
    
    # Get the corresponding bitrate using the mapping
    bitrate=${bitrate_map[$representation]}
    
    # Construct the new filename with the desired format
    new_filename=".chunk_${bitrate}_${segment_number}.m4s"
    
    # Rename the file
    mv "$file" "$new_filename"
done

