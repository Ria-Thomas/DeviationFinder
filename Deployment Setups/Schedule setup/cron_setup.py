from crontab import CronTab

# Cron job to trigger the prediction code
cron = CronTab(user=True)
job = cron.new(command='python3 prediction.py')

#This job will run every 2 minutes
job.minute.every(5)

cron.write()

# Enable the job
print (job.enable(True))

print (job.is_valid())
