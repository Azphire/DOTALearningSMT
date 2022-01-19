#!/bin/bash

# e.g. ./run_test.sh 3_2_10
# Result can be found in "./result/3_2_10.txt"

if [ ! -d result ]; then
mkdir result
fi

> ./result/$1.txt # clear file

for i in $(seq 1 10) # iterate files
do
python stats.py $1 $1-$i.json
done

# Statistics
python -c "import stats; stats.parse_data(\""./result/$1.txt"\")" 

