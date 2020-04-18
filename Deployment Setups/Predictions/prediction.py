import boto3
import json
import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from tensorflow.keras.models import model_from_json


#Storing the history of runs by cron in log file
with open('predlog.txt', 'a') as f:
	f.write('\nStarted on ' + str(datetime.now()))

f.close()

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

#Function to 
def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i:(i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)

#Connecting to dynamo-db 
dynamodb = boto3.resource("dynamodb", region_name='us-east-1', endpoint_url="http://localhost:8000")

#Table that contain input data
table_in = dynamodb.Table('Input')

#Table that memorize the last index being processed for prediction
table_re = dynamodb.Table("Restart")
print(table_in,table_re)

#Table that store output results
table_out = dynamodb.Table('Elevator')

#Total number of lifts
lifts = 16

#Setting threshold and timesteps for LSTM
threshold = 1.5
timesteps = 5

#No:of records to be processed and predicted at each run
num = 3040

#This process runs for all lifts
for i in range(1,lifts):
	print("ID is:",i)

	#Creation of pandas dataframe to create output results
	df_in = pd.DataFrame(columns=['indx','id','time','Z'])

	#Query to retrieve the current index present in restart table
	query_re = table_re.query(
    		KeyConditionExpression=Key('id').eq(i)
    		)
	for ind in query_re["Items"]:
		idx = ind["index"]
		#Logic specific for LSTM
		if idx > 0:
			idx = idx - 5
		print("Index is",idx)

	#Query shall return input values based on lift id and the index obtained from restart table. Each time 1560 records are retrieved for prediction
	query_in = table_in.query(
		    KeyConditionExpression=Key('id').eq(int(i)) & Key('index').between(idx,idx+num) 
		    )

	#Retrieved values from query are stored in table
	for rec in query_in["Items"]:
		idx_val = rec["index"]
		lift_id = rec["id"]
		time = rec["time"]
		#Condition to check for each lift as the vertical movement axis and direction is different in each lifts
		if lift_id == 1 or lift_id == 2 or lift_id == 7 or lift_id == 15 :
			Z = rec["Z"]
		elif lift_id == 3 or lift_id == 5 or lift_id == 11:
			#print("came here")
			Z = rec["X"]
		elif lift_id == 4 or lift_id == 6 or lift_id == 9 or lift_id == 10 or lift_id == 13:
			#print("came here")
			Z = rec["Z"]
			Z = Z * -1
		elif lift_id == 8 or lift_id == 14:
			#print("came here")
			Z = rec["X"]
			Z = Z * -1
		elif lift_id == 12:
			#print("came here")
			Z = rec["Y"]
			Z = Z * -1
		
		df_in = df_in.append({'indx':idx_val,'id':lift_id,'time':time,'Z':Z},ignore_index=True)
	print(df_in.head())
	
	if df_in.empty == False:
		scaler = StandardScaler(with_mean=True,with_std=True)
		df_in['Z_scaled'] = scaler.fit_transform(df_in[['Z']])	

		df_in['movAverage'] = df_in['Z_scaled'].rolling(3).mean()
		df_in.dropna(inplace=True)
		print(df_in)

		#Logic specific for LSTM.This ensures that there are minimum of 5 timesteps available for prediction. Only then we process further
		if len(df_in) > 5:

			test = df_in[['time','movAverage']]
	
			# Setting Time steps for LSTM model
			TIME_STEPS = 5
			X_test, y_test = create_dataset(
			  test[['movAverage']],
			  test.movAverage,
			  TIME_STEPS
			)
	
			X_test = np.reshape(X_test,(X_test.shape[0],X_test.shape[1],1))
		
			# Load the model.
			json_file = open('LSTM_model_T3.json', 'r')
			loaded_model_json = json_file.read()
			json_file.close()
			model = model_from_json(loaded_model_json)
			# load weights into new model
			model.load_weights("LSTM_weights_T3.h5")
			print("Loaded model from disk")
	
			#Predictions
			X_test_pred = model.predict(X_test)
			test_mae_loss = np.mean(np.abs(X_test_pred - X_test), axis=1)
	
			#Anomaly calculation
			test_score_df = pd.DataFrame(index=test[5:].index)
			test_score_df['loss'] = test_mae_loss
			test_score_df['threshold'] = threshold
			test_score_df['anomaly'] = test_score_df.loss > test_score_df.threshold
			test_score_df['movAverage'] = test[5:].movAverage

			anomalies = test_score_df[test_score_df.anomaly == True]
			anomalies.reset_index(inplace=True)
		
			df_in.reset_index(inplace=True)
			test_score_df.reset_index(inplace=True)

			print(test_score_df.head())

			#Final dataset creation
			df_final = pd.merge(df_in,test_score_df,on='index')
			df_final['anomaly']=df_final['anomaly'].astype(int)
			count = len(df_final[df_final['anomaly'] == 1])
			if count < 7:
				print("came here to make it normal")
				df_final['anomaly'] = np.where(df_final['anomaly'] > 0, 0, df_final['anomaly'])

			df_anom = df_final[df_final["anomaly"] == 1]
			print(df_anom.head())
			df_final = df_final[['index','indx','time','Z_scaled','Z','anomaly']]
	
			print(df_final.head())
			df_final.to_csv('Lift1_ssssssssss.csv',index=False)

			#Update the table with last processed index
			response = table_re.get_item(Key={'id': i})
			item = response["Item"]
			item["index"] = idx+num
			table_re.put_item(Item=item)

			#Loading into final table for dashboard
			for j in range(0,len(df_final)):
			    elid = i
			    time = str(df_final["time"][j])
			    accel = Decimal(str(df_final['Z_scaled'][j]))
			    label = int(df_final['anomaly'][j])
			    index = int(df_final['indx'][j])
	
			    table_out.put_item(
	        	   	Item={
        		       	'id': elid,
        		       	'time': time,
        		       	'accel': accel,
			       	'label': label,
        		       	'index': index
        			}
        		     )	


	#Update the table with last processed index
	#response = table_re.get_item(Key={'id': i})
	#item = response["Item"]
	#item["index"] = 0
	#table_re.put_item(Item=item)

#Storing the history of runs by cron in log file
with open('predlog.txt', 'a') as f:
	f.write('\nEnded on ' + str(datetime.now()))

f.close()
 


