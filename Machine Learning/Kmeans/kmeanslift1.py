##Author : Vipin Das
##Master's in Computer Science with Big Data 
##Simon Fraser University, Burnaby
##Created on : March 20, 2020

from pyspark.sql import SparkSession, functions, types
from pyspark.ml.feature import StandardScaler
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.functions import col, mean, stddev,stddev_pop,avg,max,to_timestamp,udf,desc,min
from pyspark.ml.feature import VectorAssembler, SQLTransformer,StandardScaler

from pyspark.sql import Window
spark = SparkSession.builder.appName('Kmeans-Lift1').getOrCreate()
spark.sparkContext.setLogLevel('WARN')
assert spark.version >= '2.4'  # make sure we have Spark 2.4+

from pyspark.ml import Pipeline
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator


def main(input,model_file):
   # Defining the schema for Lift1 datasets
   def sensor_schema():
        sen_schema = types.StructType([
        types.StructField('timestamp', types.StringType()),
        types.StructField('X', types.DoubleType()),
        types.StructField('Y', types.DoubleType()),
        types.StructField('Z', types.DoubleType()),
        ])
        return sen_schema

   def calc_score(count, min_max_collection):
            min_count = float(min_max_collection[0])
            max_count = float(min_max_collection[1])
            score = (max_count - count) / (max_count - min_count)
            return score


   sens_schema = sensor_schema()
   #Spark read of data
   temp = spark.read.csv(input, schema=sens_schema)

   # Selecting time range from 07/09 to 08/09 . Other data are useless
   temp.createOrReplaceTempView("temp")
   temp = spark.sql("select timestamp,Z from temp where timestamp between '2018-07-09 12:00:00' and '2018-08-09 12:00:00'")

   # The below code is to apply a standard scale to achieve Z normalization. This will ensure to make mean as 0 and standard deviation as 1.
   # UDF for converting column type from vector to double type
   unlist = udf(lambda x: round(float(list(x)[0]),6), types.DoubleType())

   assembler = VectorAssembler(
               inputCols=["Z"],
               outputCol="Zvector")
   tempdata = assembler.transform(temp)
   scaler = StandardScaler(inputCol="Zvector", outputCol="Zscale",withMean=True, withStd=True)
   scalerModel = scaler.fit(tempdata)
   scaledData = scalerModel.transform(tempdata).withColumn("Zscale", unlist("Zscale")).drop("Zvector").cache()
   scaledData.show()

   #Conversion of timestamp string to timestamp type. This is for smoothing purpose
   scaledData = scaledData.withColumn("times", to_timestamp("timestamp", 'yyyy-MM-dd HH:mm:ss')).cache()

   #Obtain moving averages
   movAvg = scaledData.withColumn("movingAverage", avg(scaledData["Zscale"])
             .over( Window.partitionBy(scaledData["times"]).rowsBetween(-3,3))).cache()
   movAvg.show()

   #Round the Zscale value to 0
   movAvg.createOrReplaceTempView("movAvg")
   scaledNorm = spark.sql("select times,Zscale,round(movingAverage,0) as Zround from movAvg").cache()
   scaledNorm.show()

   #Feature transform for K means
   cols = ["Zscale","Zround"]
   ft_assembler = VectorAssembler(inputCols=cols,outputCol="features")
   in_df = ft_assembler.transform(scaledNorm)
   kmeans = KMeans().setK(5).setSeed(1)
   model = kmeans.fit(in_df)

   # Make predictions
   predict = model.transform(in_df).cache()
   predict.show()

   #Evaluate clustering by computing Silhouette score
   evaluator = ClusteringEvaluator()

   silhouette = evaluator.evaluate(predict)
   print("Silhouette with squared euclidean distance = " + str(silhouette))

   #Shows the result
   centers = model.clusterCenters()
   print("Cluster Centers: ")
   for center in centers:
       print(center)

   #Saving the model
   model.write().overwrite().save(model_file)

   #Calculate the total count of each cluster
   count_df = predict.groupBy("prediction").count().cache()
   count_df.show()
    
   #count_df.createOrReplaceTempView("count_df")
   #min_max_list = spark.sql("select min(count) as min,max(count) as max from count_df group by count").collect()[0]
   min_max_list = count_df.agg(min('count'),max('count')).collect()[0]
   print(min_max_list)

   #Calculating the scores
   udf_calc_score = udf(lambda count: calc_score(float(count), min_max_list),types.FloatType())
   anom_score = count_df.withColumn("score",udf_calc_score("count")).cache()
   anom_score.show()

   #Populating scores
   predict = predict.join(anom_score, "prediction").select("times", "Zscale", "Zround", "prediction", "score")
   predict.show()

   #Anomaly detection based om threshold
   anomaly = predict.where(predict["score"] > 0.9999)
   anomaly.show()

   #Writing to a csv file
   anomaly.coalesce(1).orderBy("times").write.csv("kmeansout")



if __name__ == '__main__':
    #input = sys.argv[1]
    #model_file = sys.argv[2]
    #input = 'EDS_1.csv'
    input='EDS_1.csv'
    model_file = 'eds1mod'
    main(input, model_file)



