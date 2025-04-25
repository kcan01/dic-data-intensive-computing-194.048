#!/bin/bash

# This script runs the DIC_runner.py with hadoop streaming
# Outputs the results to output.txt
# Uncomment the command that you want to run

# Run on full dataset, custom hadoop configuration
python DIC_runner.py --conf-path=./DIC_runner.conf --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviewscombined.json > output.txt

# Run on full dataset, default conf
# python DIC_runner.py --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviewscombined.json > output.txt

# Run on small dataset, custom hadoop configuration
# python DIC_runner.py --conf-path=./DIC_runner.conf --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviews_devset.json > output_devset.txt

# Run on small dataset, default conf
# python DIC_runner.py --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviews_devset.json > output_devset.txt

