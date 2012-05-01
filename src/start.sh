#! /bin/sh

# Parameter 1: Lat   52.235524
# Parameter 2: Lng   10.542667
# Parameter 3: Count 10

python GCGetData.py -u USERNAME -p PASSWORD -c $3 $1,$2  > /tmp/gc-$1-$2.gpx

