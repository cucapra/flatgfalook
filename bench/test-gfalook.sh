#!/bin/bash

# Use hyperfine to test the runtimes of both gfalook and flatgfalook, a version of gfalook with the FlatGFA data structure grafted in place of the proprietary one

echo \"flatgfalook ${@:1}\"

hyperfine --warmup 10 "flatgfalook $*" "gfalook $*"
