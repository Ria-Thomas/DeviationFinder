from __future__ import print_function # Python 2/3 compatibility
import sys
import json
from kafka import KafkaConsumer
from pyspark.sql import SparkSession, types, functions
from pyspark.sql.types import StructType, DoubleType, StringType
from pyspark.sql.functions import *
import boto3
from decimal import Decimal

spark = SparkSession.builder.appName('Kafka Stream').getOrCreate()
assert spark.version >= '2.4'  # make sure we have Spark 2.4+
spark.sparkContext.setLogLevel('WARN')
#creating a boto3 resource to connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
table = dynamodb.Table('Input')

def main():
    #creating a consumer instance for reading the value from producer
    consumer = KafkaConsumer(bootstrap_servers='localhost:9092', auto_offset_reset='earliest', value_deserializer=lambda m: json.loads(m.decode('utf-8')))
    #making the consumer to listen to the desired topic
    consumer.subscribe(['lift12'])
    #getting the json string which is in the value attribute of the message
    for message in consumer:
            #converting values from the kafka producer message to required formats
            index = int(message.value['index'])
            elid = int(message.value['id'])
            time = str(message.value['timestamp'])
            X = Decimal(message.value['X'])
            Y = Decimal(message.value['Y'])
            Z = Decimal(message.value['Z'])
            #writing each entry to the DynamoDB table
            table.put_item(Item={'index': index,'id': elid,'time': time,'X': X,'Y': Y,'Z': Z})



if __name__ == '__main__':
    main()



