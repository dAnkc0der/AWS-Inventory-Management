import boto3, argparse
from exporters import export_all
from datetime import datetime, UTC, timedelta

def parse_args():
    """
    Parses arguments that can be passes to the terminal without hardcoding
    """
    parser = argparse.ArgumentParser(description="AWS Resource inventory Tool")
    parser.add_argument("--region", default="us-east-1", help="AWS Region to scan")
    parser.add_argument("--output", default="inventory", help="Base filename for output files")
    return parser.parse_args()

def main():
    """
    combines all the functions together
    """
    args = parse_args()
    ec2_client = boto3.client("ec2", region_name=args.region)
    cloudwatch_client = boto3.client("cloudwatch", region_name=args.region)
    ebs = get_ebs_inventory(ec2_client)
    s3_client = boto3.client("s3", region_name=args.region)
    s3_inventory = get_s3_inventory(s3_client)
    rds_client = boto3.client("rds", region_name=args.region)
    rds_inventory = get_rds_inventory(rds_client)
    sg_findings = get_security_group_findings(ec2_client) 
    ec2_inventory = get_ec2_inventory(ec2_client, cloudwatch_client)
    export_all(ec2_inventory, f"{args.output}_ec2")
    export_all(ebs, f"{args.output}_ebs")
    export_all(s3_inventory, f"{args.output}_s3")
    export_all(rds_inventory, f"{args.output}_rds")
    export_all(sg_findings, f"{args.output}_sg")

def get_ec2_inventory(ec2_client, cloudwatch_client):
    """
    Fetch all EC2 and return their details
    Args: ec2_client
    Returns: list[dict]
    """
    ec2_inventory = []
    try:
        instances = ec2_client.describe_instances()
    except Exception as e:
        print(f"Warning: could not fetch EC2 data: {e}")
        return ec2_inventory
    for i in instances["Reservations"]:
        for instance in i["Instances"]:
            instance_id = instance["InstanceId"]
            cpu = get_cpu_utilization(cloudwatch_client, instance_id)
            state = instance["State"]["Name"]
            instance_type = instance["InstanceType"]
            tags = instance.get("Tags", [])
            value = get_name_tag(tags)
            ec2_inventory.append({"InstanceId": instance_id, "State": state, "InstanceType": instance_type, "Name": value, "CPU": cpu})
    return ec2_inventory

def get_ebs_inventory(ec2_client):
    """
    Gathers information about EBS volumes attached to EC2
    Args: ec2_client
    Returns: list[dict]
    """
    ebs = []
    try:
        volumes = ec2_client.describe_volumes()
    except Exception as e:
        print(f"Warning: could not fetch EBS data: {e}")
        return ebs
    for volume in volumes["Volumes"]:
        volumeID = volume["VolumeId"]
        size = volume["Size"]
        state = volume["State"]
        is_attached = (state == "in-use")
        tags = volume.get("Tags", [])
        tag = get_name_tag(tags)
        ebs.append({"VolumeID": volumeID, "Size": size, "State": state, "Name": tag, "Attached": is_attached})
    return ebs

def get_s3_inventory(s3_client):
    """
    Gathers information about S3 buckets
    Args: s3_client
    Returns: list[dict]
    """
    s3_inventory = []
    try:
        response = s3_client.list_buckets()
    except Exception as e:
        print(f"Warning: could not fetch S3 data: {e}")
        return s3_inventory
    for bucket in response["Buckets"]:
        name = bucket["Name"]
        createdAt = bucket["CreationDate"].isoformat()
        s3_inventory.append({"Name": name, "CreationDate": createdAt})
    return s3_inventory

def get_rds_inventory(rds_client):
    """
    Gathers information abut RDS database
    Args: rds_client
    Returns: list[dict]
    """
    rds_inventory = []
    try:
        response = rds_client.describe_db_instances()
    except Exception as e:
        print(f"Warning: could not fetch RDS data: {e}")
        return rds_inventory
    for db in response["DBInstances"]:
        identifier = db["DBInstanceIdentifier"]
        db_class = db["DBInstanceClass"]
        engine = db["Engine"]
        status = db["DBInstanceStatus"]
        tags = db.get("TagList", [])
        tag = get_name_tag(tags)
        rds_inventory.append({"DBInstanceIdentifier": identifier, "DBInstanceClass": db_class, "Engine": engine, "DBInstanceStatus": status, "Name": tag})
    return rds_inventory 

def get_security_group_findings(ec2_client):
    """
    Gathers information about open ports in security group
    Args: ec2_client
    Returns: list[dict]
    """
    sg_inventory = []
    try:
        response = ec2_client.describe_security_groups()
    except Exception as e:
        print(f"Warning: could not fetch Security Group data: {e}")
        return sg_inventory
    for sg in response["SecurityGroups"]:
        for ip in sg["IpPermissions"]:
            for range in ip["IpRanges"]:
                if range["CidrIp"] == "0.0.0.0/0":
                    groupId = sg["GroupId"]
                    groupName = sg["GroupName"]
                    fromPort = ip.get("FromPort", "ALL")
                    toPort = ip.get("ToPort", "ALL")
                    ipProtocol = ip["IpProtocol"]
                    cidrIp = range["CidrIp"]
                    sg_inventory.append({"GroupId": groupId, "GroupName": groupName, "FromPort": fromPort, "ToPort": toPort, "IpProtocol": ipProtocol, "CidrIp": cidrIp})
    return sg_inventory

def get_cpu_utilization(cloudwatch_client, instance_id):
    """
    Gathers information about average CPU for past one hour
    Args: cloudwatch_client, instance_id (str)
    Returns: float (rounded percentage) or "No Data" string if unavailable
    """
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=1)
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,          # one data point covering the whole 1-hour window
            Statistics=["Average"]
        )
    except Exception as e:
        print(f"Warning: could not fetch CPU data for {instance_id}: {e}")
        return "No Data"
    if response["Datapoints"] == []:
        return "No Data"
    else:
        avg = response["Datapoints"][0]["Average"]
        value = round(avg, 2)
    return value
    

def get_name_tag(tags):
    """
    Returns Tag/Name for each resource
    """
    for tag in tags:
        if tag["Key"] == 'Name':
            return tag["Value"]
    return "Unnamed"


if __name__ == "__main__":
    main()