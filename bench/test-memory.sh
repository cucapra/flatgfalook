#!/bin/bash

echo "flatgfalook:" >> "$3"
for file in $1/*.gfa; do
	echo "$file:" >> "$3"
	/usr/bin/time -v -a -o "$3" flatgfalook -i "$file" -o "$2"/test_flat.png -x 1000 -y 500
done


echo "gfalook:" >> "$3"
for file in $1/*.gfa; do
	echo "$file:" >> "$3"
	/usr/bin/time -v -a -o "$3" gfalook -i "$file" -o "$2"/test.png -x 1000 -y 500
done


