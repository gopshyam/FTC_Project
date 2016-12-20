#! /usr/bin/env python

import boto3
import json

IMAGE_PREFIX = "Replica_image_"

client = boto3.client('ec2')

def delete_instance_by_ip(ip):
    print "DELETING " + ip 
    client_description_response = client.describe_instances(Filters = [{'Name':'private-ip-address', 'Values':[ip]}])
    reservations = client_description_response['Reservations']
    for reservation in reservations:
        if 'PrivateIpAddress' in reservation['Instances'][0].keys() and ip == reservation['Instances'][0]['PrivateIpAddress']:
            instance_id = reservation['Instances'][0]['InstanceId']
            client.terminate_instances(InstanceIds = [instance_id])


def find_most_recent_image():
    response = client.describe_images(Owners=['571106538810'], Filters = [{"Name":"name", "Values":['Replica*']}])
    index = 0
    most_recent_image = None
    images = response['Images']
    for image in images:
        name = image['Name']
        cur_index = int(name.split('_')[-1].strip())
        if cur_index >= index:
            index = cur_index
            most_recent_image = image['ImageId']

    return most_recent_image, index

def create_instance_with_image(image_id):
    response = client.run_instances(InstanceType = 't2.micro', ImageId = image_id, MinCount = 1, MaxCount = 1, KeyName = "shyam_key", SecurityGroupIds = ['sg-5c76a125','sg-1175a268'])


def handle_fault(task_id):
    task_name = "Client" + str(task_no)
    print "STOPPING TASK " + str(task_name)
    response = client.describe_task_definition(taskDefinition = task_name)
    task_arn = response['taskDefinition']['taskDefinitionArn']
    client.stop_task(cluster = "shyam", taskDefinition = task_arn)
    client.run_task(cluster = "shyam", taskDefinition = task_name)

