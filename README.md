# DiC Assignment 1 

## Group 6
- Theresa Mayer
- Theresa Brucker
- Can Kenan Kandil 
- Jan Tölken
- Thomas Klar

## Usage on the LBD cluster
Setup environment: Make sure your python environment has the mrjob and json packages


To run the job with the full dataset on the cluster using hadoop:
```
python DIC_runner.py --conf-path=./DIC_runner.conf --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviewscombined.json > output.txt
```
You can also use default hadoop configuration, which will be far slower
```
python DIC_runner.py --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviewscombined.json > output.txt
```
For testing, you can run the job using inline runner (the reviews_devset.json file needs to be present in the working directory)
```
python DIC_runner.py -r inline reviews_devset.json > output_devset.txt
```
or alternatively using hadoop:
```
python DIC_runner.py --conf-path=./DIC_runner.conf --hadoop-streaming-jar /usr/lib/hadoop/tools/lib/hadoop-streaming-3.3.6.jar -r hadoop hdfs:///user/dic25_shared/amazon-reviews/full/reviews_devset.json > output_devset.txt
```

## Usage locally
Unless you have hadoop installed, you can only use inline runner. The file reviews_devset.json has to be present in the working directory (or alternatively, the full dataset)
```
python DIC_runner.py -r inline reviews_devset.json > output_devset.txt
```
