from celery import Celery

# Configure Celery to use RabbitMQ as the broker

amqpurl = 'amqps://svumkmdp:B29vtha3miLQU56iiH37m_FLi6WvDNnl@cougar.rmq.cloudamqp.com/svumkmdp'
amqpurl = 'redis://:0KuY45rROfxG6qND2CkqhQIEPTKVgkqA@redis-12289.c51.ap-southeast-2-1.ec2.cloud.redislabs.com:12289'
app = Celery('tasks', broker=amqpurl,          backend=amqpurl)

# Define a task


@app.task
def add(x, y):
    return x + y
