import sys
import os
from pathlib import Path
try:
	import tomllib
except ImportError:
	import tomli as tomllib

import gzip
import pyzstd as zstd
import shutil
import subprocess

import argparse

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

if __name__ == "__main__":
  
  parser = argparse.ArgumentParser(prog='download_graphs', 
  description="""
downloads a graph specified in a toml file, 
to a specified directory, can specify download source (-d) and size (-s).\n
source can be test, hprc, or gont.\n
size can be smoke, mini, med, or big.\n
if source and size are BOTH specified, it will take the intersection for both conditions, which may result in no files being downloaded.
  """)
	
  parser.add_argument('toml')
  parser.add_argument('output')
  parser.add_argument('-s', '--size')
  parser.add_argument('-d', '--download_src')
  
  args = parser.parse_args()
  args_dict = vars(args)

  graphs_toml = args_dict['toml']
  output = args_dict['output']
  size = args_dict['size'] or 'all'
  src = args_dict['download_src'] or 'all'


  # Parse the GFA URLs from graphs.toml
  with open(graphs_toml, "rb") as f:
    toml_graphs = tomllib.load(f)

  # The following variables extract specific sections of the graphs.toml file. If you are 
  # using standard GFA files for your test, no need to modify these

  hprc_dict = dict(toml_graphs["hprc"])
 
  test_dict = dict(toml_graphs["test"]) 

  gont_dict = dict(toml_graphs["1000gont"])
 
  sizes = {}

  sizes['smoke'] = [test_dict["k"]]
 
  sizes['mini'] = [test_dict["lpa"], test_dict["chr6c4"], hprc_dict["chrM"]]

  sizes['med'] = [hprc_dict["chr20"], hprc_dict["chrX"], gont_dict["chr16"]]

  sizes['big'] = [hprc_dict["chrY"], hprc_dict["chr1"], hprc_dict["chr10"]]
  
  web_files = []

  size_cond = lambda x: (size == 'all') or (x in sizes[size])

  if src == 'all' or src == 'hprc':
    for key, url in hprc_dict.items():
      if size_cond(url):
        web_files.append(url)
  
  if src == 'all' or src == 'gont':
    for key, url in gont_dict.items():
      if size_cond(url):
        web_files.append(url)

  if src == 'all' or src == 'test':
    for key, url in test_dict.items():
      if size_cond(url):
        web_files.append(url)


  for web_file in web_files:
    # get the end file name, get the last element after splitting it on /
    target = web_file.split("/")[-1]
      
    # if the target doesn't even contain .gfa, just append it and move on
    if ".gfa" not in target:
        target += ".gfa"
    # if the target does contain .gfa, simply truncate it to the last occurrence of that file extension
    else:
        i = target.rfind(".gfa")
        target = target[:i+4]
    
    # prepend the output directory to the target name
    target = output + "/" + target

    # download the file
    download_file(target, web_file)
