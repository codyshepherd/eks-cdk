import os

from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk import core


class EksCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ami_id = os.environ.get('EKS_AMI_ID', 'ami-00a2e2e342bef0e5e')
        k8s_version = os.environ.get('EKS_K8S_VERSION', '1.16')
        name_id = f'eks-cdk-cluster-{k8s_version}'.replace('.', '-')
        capacity = os.environ.get('EKS_CAPACITY', '10')
        # template_url = os.environ.get('EKS_VPC_TEMPLATE', 'https://amazon-eks.s3.us-west-2.amazonaws.com/cloudformation/2020-05-08/amazon-eks-vpc-private-subnets.yaml')
        nodegroup_template_url = os.environ.get('EKS_NODEGROUP_TEMPLATE', 'https://amazon-eks.s3.us-west-2.amazonaws.com/cloudformation/2020-05-08/amazon-eks-nodegroup.yaml')
        ssh_key = os.environ.get('AWS_SSH_KEY', 'personal-us-west-2')

        # The code that defines your stack goes here

        '''
        # Role
        role = iam.Role(self, name_id,
                        assumed_by='eks.amazonaws.com'
                        external_id=name_id+'-eks-role',
                        )
        '''

        cluster_k8s_version = eks.KubernetesVersion.V1_16
        if k8s_version == "1.15":
            cluster_k8s_version = eks.KubernetesVersion.V1_15
        elif k8s_version == "1.14":
            cluster_k8s_version = eks.KubernetesVersion.V1_14

        # Role
        eks_role = iam.Role(self, name_id+'-role',
                            assumed_by=iam.ServicePrincipal('eks.amazonaws.com'),
                            role_name="EksRole")
        eks_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKSClusterPolicy'))
        eks_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEKSServicePolicy'))

        # Cluster
        cluster = eks.Cluster(self, name_id,
                              default_capacity=0,
                              cluster_name=name_id+'-cluster',
                              masters_role=iam.AccountRootPrincipal(),
                              role=eks_role,
                              version=cluster_k8s_version,
                              vpc_subnets=[ec2.SubnetType.PUBLIC,]
                              )

        # Node Group w/ ubuntu ami

        cfn.CfnStack(self, name_id+'-nodes',
                     template_url=nodegroup_template_url,
                     parameters={
                        'ClusterName': cluster.cluster_name,
                        'ClusterControlPlaneSecurityGroup': cluster.connections.security_groups[0].security_group_id,
                        'NodeGroupName': name_id+'-nodegroup',
                        'NodeAutoScalingGroupMinSize': capacity,
                        'NodeAutoScalingGroupDesiredCapacity': capacity,
                        'NodeAutoScalingGroupMaxSize': capacity,
                        'NodeInstanceType': 'm5.large',
                        'NodeImageId': ami_id,
                        'KeyName': ssh_key,
                        'VpcId': cluster.vpc.vpc_id,
                        'Subnets': ','.join([x.subnet_id for x in cluster.vpc.public_subnets]),
                     },
                     )
        '''
        nodes = eks.Nodegroup(self, name_id+'-nodes',
                              cluster,
                              ami_type=ami,
                              desired_size=10,
                              max_size=capacity,
                              min_size=capacity,
                              nodegroup_name=name_id+'-nodes',
                              release_version=k8s_version,
                              #TODO: remote_access=NodegroupRemoteAccess
                              )
        '''
