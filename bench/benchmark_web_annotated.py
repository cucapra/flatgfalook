import sys
import os
import json
import subprocess
from pathlib import Path
import time
try:
	import tomllib
except ImportError:
	import tomli as tomllib

import gzip
import pyzstd as zstd
import shutil

# Modify these variables to avoid file conflicts and create unique command names
results = "filesize_benchmark.txt" 
file_test_results = "test_big_10.json"
test_id = "" 
normalization_file = "normalization.toml"
command_1 = "flatgfalook"
command_2 = "gfalook"

# Parse the GFA URLs from graphs.toml
with open("graphs.toml", "rb") as f:
    toml_graphs = tomllib.load(f)

# The following variables extract specific sections of the graphs.toml file. If you are 
# using standard GFA files for your test, no need to modify these

hprc_dict = dict(toml_graphs["hprc"])
 
test_dict = dict(toml_graphs["test"]) 

gont_dict = dict(toml_graphs["1000gont"])
 
smoke_files = [test_dict["k"]]
 
mini_files = [test_dict["lpa"], test_dict["chr6c4"], hprc_dict["chrM"]]

med_files = [hprc_dict["chr20"], hprc_dict["chrX"], gont_dict["chr16"]]

big_files = [hprc_dict["chrY"], hprc_dict["chr1"], hprc_dict["chr10"]]



# Download a GFA file from the internet
def download_file(target_name, web_file):
  print(f"Downloading {web_file} to {target_name}")
  zip_format = None
  temp_name = ""
  if "gfa.gz" in web_file:
    zip_format = "gz"
  elif "gfa.zst" in web_file:
    zip_format = "zst"
  
  if zip_format == "gz":
    temp_name = f"{target_name}.gz"
  elif zip_format == "zst":
    temp_name = f"{target_name}.zst"

  if not Path(target_name).exists():
    if zip_format is not None:
      subprocess.run(["curl", "-o", temp_name, web_file],
              check = True)
      
      if zip_format == "gz":
        with gzip.open(temp_name, "rb") as f_in:
          with open(target_name, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
      elif zip_format == "zst":
        # print("Unzipping using zst")
        with zstd.open(temp_name, "rb") as f_in:
          with open(target_name, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
      subprocess.run(["rm", "-rf", temp_name], check = True) 
    else:
      subprocess.run(["curl", "-o", target_name, web_file],
              check = True) 

# Run a single latency test
# Modify the indicated lines to test your own comamand
def test(command, test_file_name, num_iter):
  if command == command_1:  
    with open(os.devnull, "w") as devnull:
      start_time = time.time()
      for _ in range(num_iter):
        subprocess.run(["flatgfalook", "-i", test_file_name, "-o", "images/test_flat.png", "-x", "1000", "-y", "500"], stdout=devnull,
            stderr=devnull,
            check=True) # Note: Replace with the command you want to test
      end_time = time.time()
      return ((end_time - start_time) * 1000) / num_iter
        
  elif command == command_2: 
    with open(os.devnull, "w") as devnull:
      start_time = time.time()
      for _ in range(num_iter):
        subprocess.run(["gfalook", "-i", test_file_name, "-o", "images/test.png", "-x", "1000", "-y", "500"], stdout=devnull,
            stderr=devnull,
            check=True) # Note: Replace with the command you want to test
      end_time = time.time()
      return ((end_time - start_time) * 1000) / num_iter

  return 0.0
  
# Run the benchmarks across all test files
def benchmark(test_config):
  del_cond = ""
  norm_cond = ""
  num_iter = 0
  iter_count = -1
  
  # Read command-line arguments
  if len(sys.argv) >= 3:
    iter_count = int(sys.argv[2]) # Can be any integer
  
  if len(sys.argv) >= 4:
    del_cond = sys.argv[3] # Can be "del", "_", or not provided

  if len(sys.argv) >= 5:
    norm_cond = sys.argv[4] # Can be "norm", or not provided

  # Choose test file set
  test_files = []
  if "smoke" in test_config:
    test_files = smoke_files
    num_iter = 2
  elif "mini" in test_config:
    test_files = mini_files
    num_iter = 10
  elif "med" in test_config:
    test_files = med_files
    num_iter = 5
  elif "big" in test_config:
    test_files = big_files
    num_iter = 2
  else:
    raise ValueError("Incorrect test config provided")
  
  # Set number of test iterations
  if not iter_count == -1:
   num_iter = iter_count
  
  i = 0
  command_1_time = 0.0
  command_2_time = 0.0
  size_bytes_avg = 0

  file_test_data = []

  # Run a test for each file in the set
  for file in test_files:
    test_file_name = f"tests/{test_config}_{i}_{test_id}.gfa"
    download_file(test_file_name, file)
    #subprocess.run(["fgfa", "-I", test_file_name, "-o", results],
    #              check = True) 
    #size_bytes_avg += os.path.getsize(results)
    curr_file_size = os.path.getsize(test_file_name)
    command_1_curr_time = test(command_1, test_file_name, num_iter)
    command_2_curr_time = test(command_2, test_file_name, num_iter)
    # subprocess.run(["rm", "-rf", results], check = True) 
    file_results = {
      "file": file,
      "test_file": test_file_name,
      "size": curr_file_size,
      command_1: command_1_curr_time,
      command_2: command_2_curr_time
    }
    json.dump(file_results, sys.stdout, indent=4)
    file_test_data.append({
      "file": file,
      "test_file": test_file_name,
      "size": curr_file_size,
      command_1: command_1_curr_time,
      command_2: command_2_curr_time
    })
    command_1_time += command_1_curr_time
    command_2_time += command_2_curr_time 

    # Delete test files if flag set
    if del_cond == "del":
      subprocess.run(["rm", "-rf", test_file_name], check = True) 
    i += 1
  
  with open(file_test_results, "w") as f:
    json.dump(file_test_data, f, indent=4)

  if (norm_cond == "norm"):

    # Write new normalization values
    with open(normalization_file, "w") as f:
      f.write("[normalization_factors]\n")
      f.write(f"{command_1} = {command_1_time}\n")
      f.write(f"{command_2}= {command_2_time}\n")
    return (1.0, size_bytes_avg)
  else:

    # Read normalization values
    with open(normalization_file, "rb") as f:
      data = tomllib.load(f)
    command_1_norm = data["normalization_factors"][command_1]
    command_2_norm = data["normalization_factors"][command_2]

    
    # Normalize values
    command_1_time /= command_1_norm
    command_2_time /= command_2_norm

    # Return the harmonic mean
    size_bytes_avg /= len(test_files)
    return (2 / ((1 / command_1_time) + (1 / command_2_time)), size_bytes_avg / 1000.0)

# Read the desired test file set from command-line input
test_config = ""
if len(sys.argv) >= 2:
  test_config = sys.argv[1] # Can be either "smoke", "mini", "med", or "big"
else:
  raise ValueError("No arguments provided")

bench_results = benchmark(test_config)
          

# Output the benchmark results, either in a Bencher JSON format, or a standard 
# command-line format
# Modify the print statements to print what makes sense for what you're testing
if "bencher" in test_config:
  bencher_json = {
    "FlatGFA Benchmark Results": {
      "Average Execution Latency": {"value": round(bench_results[0], 2)}, 
      "Average File Size": {"value": round(bench_results[1], 2)},
    }
  }
  json.dump(bencher_json, sys.stdout)
else:

  # Only print latency info if flag set
  if "latency" in test_config:
    print(f"Average Execution Latency: {round(bench_results[0], 2)} ms")

  # Only print filesize info if flag set
  elif "filesize" in test_config:
    print(f"Average File Size: {round(bench_results[1], 2)} KB")
  else:
    print(f"Average Execution Latency: {round(bench_results[0], 2)} ms")
    print(f"Average File Size: {round(bench_results[1], 2)} KB")
  

# Command format: python bench/benchmark_web_annotated.py [size](_bencher/_latency/_filesize) [run_count] (del/_) (norm)
# () = optional, [] = replace with value  
 
# Explanation: The user selects the variant of the test they want to run with a flag.
# For example, "python bench/latency_benchmark_web.py mini_latency 10" tests the mini GFA file set on the latency test
# for 10 iterations, while replacing "mini_latency" with "mini_filesize" runs the filesize test instead. 
# Including the "del" flag delete the downloaded GFA files after the test runs
#   (Example usage: "python bench/latency_benchmark_web.py mini_latency 10 del")
# Including the "norm" flag resets the normalization constants. 
#    (Example usage: "python bench/latency_benchmark_web.py mini_latency 10 _ norm")
 
# It's important to list the flags in the correct order, and in the correct position 
