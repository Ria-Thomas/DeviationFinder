from time import sleep
from json import dumps
from kafka import KafkaProducer
import pandas as pd
import json
import csv
import datetime, time, random, threading

rates = [24]

def send_at(rate):
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'], value_serializer=lambda x:dumps(x).encode('utf-8'))
    interval = 1/rate
    i = 0
    while True:
        with open('./Lift_samples/EDS_Lift15_sample.csv') as file:
            reader = csv.DictReader(file, fieldnames = ["timestamp", "X", "Y", "Z"])
            for row in reader:
                row.update({'timestamp': str(datetime.datetime.now(tz=None))})
                row.update({'id': 15})
                row.update({'index': i})
                data = json.loads(json.dumps(row))
                producer.send('lift15',value=data)
                i = i+1
                sleep(interval)


if __name__ == "__main__":
    for rate in rates:
        server_thread = threading.Thread(target=send_at, args=(rate,))
        server_thread.setDaemon(True)
        server_thread.start()

    while 1:
        time.sleep(1)
