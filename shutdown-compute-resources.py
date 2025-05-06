import boto3
from botocore.exceptions import ClientError

def stop_ec2_instances(region):
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
        instances = [i["InstanceId"] for r in response["Reservations"] for i in r["Instances"]]
        if instances:
            ec2.stop_instances(InstanceIds=instances)
            print(f"[{region}] ✅ Stopped EC2 instances: {instances}")
        else:
            print(f"[{region}] ℹ️ No standalone EC2 instances to stop.")
    except ClientError as e:
        print(f"[{region}] ❌ Error stopping EC2 instances: {e}")

def set_asg_capacity_to_zero(region):
    asg = boto3.client("autoscaling", region_name=region)
    try:
        groups = asg.describe_auto_scaling_groups()["AutoScalingGroups"]
        if not groups:
            print(f"[{region}] ℹ️ No Auto Scaling Groups found.")
            return

        for group in groups:
            asg.update_auto_scaling_group(
                AutoScalingGroupName=group["AutoScalingGroupName"], MinSize=0, DesiredCapacity=0
            )
            print(f"[{region}] ✅ Set ASG '{group['AutoScalingGroupName']}' capacity to 0")
    except ClientError as e:
        print(f"[{region}] ❌ Error updating ASGs: {e}")

def stop_ecs_tasks(region):
    ecs = boto3.client("ecs", region_name=region)
    try:
        clusters = ecs.list_clusters()["clusterArns"]
        if not clusters:
            print(f"[{region}] ℹ️ No ECS clusters found.")
            return

        for cluster in clusters:
            services = ecs.list_services(cluster=cluster)["serviceArns"]
            if services:
                for service in services:
                    ecs.update_service(cluster=cluster, service=service, desiredCount=0)
                    print(f"[{region}] ✅ Updated ECS service '{service}' to desiredCount 0")
            else:
                print(f"[{region}] ℹ️ No ECS services found in cluster '{cluster}'")
    except ClientError as e:
        print(f"[{region}] ❌ Error stopping ECS tasks: {e}")

def stop_rds_instances(region):
    rds = boto3.client("rds", region_name=region)
    try:
        instances = rds.describe_db_instances()["DBInstances"]
        if not instances:
            print(f"[{region}] ℹ️ No RDS instances found.")
            return

        for instance in instances:
            db_id = instance["DBInstanceIdentifier"]
            if instance.get("ReadReplicaSourceDBInstanceIdentifier"):
                rds.delete_db_instance(DBInstanceIdentifier=db_id, SkipFinalSnapshot=True)
                print(f"[{region}] ✅ Deleted RDS Read Replica: {db_id}")
                waiter = rds.get_waiter('db_instance_deleted')
                waiter.wait(DBInstanceIdentifier=db_id)
                print(f"[{region}] ✅ Waited until RDS Read Replica '{db_id}' is deleted")
            elif instance["DBInstanceStatus"] == "available":
                rds.stop_db_instance(DBInstanceIdentifier=db_id)
                print(f"[{region}] ✅ Stopped RDS instance: {db_id}")
            else:
                print(f"[{region}] ℹ️ RDS instance '{db_id}' is not in a stoppable state.")
    except ClientError as e:
        print(f"[{region}] ❌ Error managing RDS instances: {e}")

def stop_eks_node_groups(region):
    eks = boto3.client("eks", region_name=region)
    try:
        clusters = eks.list_clusters()["clusters"]
        if not clusters:
            print(f"[{region}] ℹ️ No EKS clusters found.")
            return

        for cluster in clusters:
            nodegroups = eks.list_nodegroups(clusterName=cluster)["nodegroups"]
            if nodegroups:
                for ng in nodegroups:
                    eks.update_nodegroup_config(
                        clusterName=cluster,
                        nodegroupName=ng,
                        scalingConfig={"minSize": 0, "desiredSize": 0}
                    )
                    print(f"[{region}] ✅ Updated EKS nodegroup '{ng}' in cluster '{cluster}' to size 0")
            else:
                print(f"[{region}] ℹ️ No node groups found in EKS cluster '{cluster}'")
    except ClientError as e:
        print(f"[{region}] ❌ Error updating EKS node groups: {e}")

def stop_sagemaker_instances(region):
    sm = boto3.client("sagemaker", region_name=region)
    try:
        notebooks = sm.list_notebook_instances()["NotebookInstances"]
        if not notebooks:
            print(f"[{region}] ℹ️ No SageMaker notebook instances found.")
            return

        for nb in notebooks:
            name = nb["NotebookInstanceName"]
            if nb["NotebookInstanceStatus"] == "InService":
                sm.stop_notebook_instance(NotebookInstanceName=name)
                print(f"[{region}] ✅ Stopped SageMaker notebook: {name}")
            else:
                print(f"[{region}] ℹ️ Notebook '{name}' is not running.")
    except ClientError as e:
        print(f"[{region}] ❌ Error managing SageMaker notebooks: {e}")

def shutdown_all():
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "ap-south-1", "ap-northeast-3", "ap-northeast-2", "ap-southeast-1",
        "ap-southeast-2", "ap-northeast-1", "ca-central-1", "eu-central-1",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-south-2", "eu-north-1", "sa-east-1"
    ]

    for region in regions:
        print(f"\n➡️ Checking region: {region}")
        stop_ec2_instances(region)
        set_asg_capacity_to_zero(region)
        stop_ecs_tasks(region)
        stop_rds_instances(region)
        stop_eks_node_groups(region)
        stop_sagemaker_instances(region)
        print(f"✅ **Shutdown completed for region: {region}** ✅")

    print("\n✅ **Shutdown Process Completed for All Regions** ✅")

# ✅ Lambda entry point
def lambda_handler(event, context):
    shutdown_all()
    return {
        "statusCode": 200,
        "body": "Shutdown process completed across all specified regions."
    }
