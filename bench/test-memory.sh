#!/bin/bash
# usage: test-memory.sh <gfa_dir> <image_output_dir> <results_file>

delim=""

echo "{flatgfalook: [" >> "$3"
for file in $1/*.gfa; do
	echo $delim >> "$3"
	/usr/bin/time --format "{\n\"file\":\"$file\",\n\"command\":\"%C\",\n\"data\":%D,\n\"wall\":\"%E\",\n\"memory\":%M,\n\"sys_sec\":%S,\n\"usr_sec\":%U\n}" -a -o "$3" flatgfalook -i "$file" -o "$2"/test_flat.png -x 1000 -y 500
	delim=","
done
echo "]," >> "$3"

delim= ""

echo "{gfalook:" >> "$3"
for file in $1/*.gfa; do
	echo $delim >> "$3"
	/usr/bin/time --format "{\n\"file\":\"$file\",\n\"command\":\"%C\",\n\"data\":%D,\n\"wall\":\"%E\",\n\"memory\":%M,\n\"sys_sec\":%S,\n\"usr_sec\":%U\n}" -a -o "$3" gfalook -i "$file" -o "$2"/test.png -x 1000 -y 500
	delim=","
done
echo "]}" >> "$3"

