# Deviation Finder
## An Elevator Anomaly Detection System

The project aimed at designing a system that could collect accelerometer data from elevators and identify anomalies which can then be used to predict which elevators are potentially at-risk of technical issues related to elevator brakes, motor and alignment.

## About the dataset

We had access to around 75 GB of accelerometer data from 15 lifts which was provided by Technical Safety BC. Data collected from the accelerometer was formatted as a csv file with rows representing recordings at each timepoint. 4 columns were included in every file as given below:

 - Timestamp
 - Acceleration - X axis
 - Acceleration - Y axis
 - Acceleration - Z axis

One of the axes denotes vertical movement whereas the other two represents the horizontal movement. The input data was filtered to use data from 2018-07-09 to 2018-08-09. The sign of acceleration values were flipped for a negative vertical axis.
Z-normalization and moving average low-pass filter is applied to remove any structural dissimilarities and noise.

## How to test the code?
< Add steps>

## Folder structure

### EDA
The folder contains exploratory data analysis details for all the 15 lifts. 
The code consists of pre-processing of the accelerometer data and plotting data for different ranges to get an idea of how anomalies and normal patterns look like.

### Lift samples
Sample anomaly files for all lifts for testing

### Feature Engineering
Code using Tsfresh which was used to generate new features to improve model accuracy. This method was explored as acceleration value was the only relevant feature provided.

### Machine Learning
Code for all the machine learning algorithms used as part of the project. This contains training and sample prediction of each model on the input data. The below algorithms were experimented with -

- Standard Anomaly Detection
- Isolation Forest
- K-means
- ANN Autoencoders
- LSTM Autoencoders

### Models
Saved models for the machine learning algorithms used.

### Prediction samples
Screenshots of anomaly detection by using a sample data on all the 5 machine learning algorithms. The blue line represents the actual signal whereas the red points denote the anomalies detected by each model.

### Evaluation metrics
 Details of evaluation for machine learning models. As the input data was not labelled, a subset of data was manually labelled. The same dataset was used by all the models for prediction and F1-score was calculated. The model with maximum F1-score was selected. 
  
### Deployment Setups
This folder consists of details of setting up the real-time streaming system using Amazon Dynamo DB and method to plug in the machine learning model (LSTM Autoencoder) for predictions. 

Detailed deployment steps are given below.
<Add steps>
