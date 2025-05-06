import boto3

# Use the sso-admin client to manage permissions and account assignments
sso_admin = boto3.client("sso-admin")

# Static SSO Instance ARN
INSTANCE_ARN = "arn:aws:sso:::instance/ssoins-xx123xxx" #update the sso instance arn

ACCOUNT_ID = "123456789" #update the respective account id and usernames
USERS = [
    "user1@abc.com",  # user1
    "user2@abc.com",
    "user3@abc.com"
]

def lambda_handler(event, context):
    for username in USERS:
        try:
            # Get the permission set ARN (assuming the name is same as username)
            ps_response = sso_admin.list_permission_sets(
                InstanceArn=INSTANCE_ARN
            )

            for ps_name in ps_response["PermissionSets"]:
                ps_details = sso_admin.describe_permission_set(
                    InstanceArn=INSTANCE_ARN,
                    PermissionSetArn=ps_name
                )
                if ps_details["PermissionSet"]["Name"] == username:
                    permission_set_arn = ps_name
                    break
            else:
                print(f"❌ No permission set found for user: {username}")
                continue

            # Get the principal ID
            principal_response = sso_admin.list_account_assignments(
                InstanceArn=INSTANCE_ARN,
                AccountId=ACCOUNT_ID,
                PermissionSetArn=permission_set_arn
            )

            for assignment in principal_response['AccountAssignments']:
                if assignment["PrincipalType"] == "USER":
                    # Use the correct parameters for delete_account_assignment
                    sso_admin.delete_account_assignment(
                        InstanceArn=INSTANCE_ARN,
                        PermissionSetArn=permission_set_arn,
                        PrincipalId=assignment["PrincipalId"],
                        PrincipalType="USER",  # This is already correct
                        TargetId=ACCOUNT_ID,  # AWS account ID as target
                        TargetType="AWS_ACCOUNT"  # Type should be AWS_ACCOUNT
                    )
                    print(f"✅ Removed permission set '{username}' for user ID {assignment['PrincipalId']}")

        except Exception as e:
            print(f"❌ Error removing permission for user {username}: {str(e)}")
