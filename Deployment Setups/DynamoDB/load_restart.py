from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
from decimal import Decimal
import pandas as pd


dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")

table = dynamodb.Table('Restart')

#### Provide the number of lifts for which we shall have an index indicator stored
lifts = 16

# This code shall update Restart table with index as 0 for all 15 lifts to start with
for i in range(0,lifts):
    index = 0
    elid = int(i)

    table.put_item(
           Item={
               'index': index,
               'id': elid
            }
        )


