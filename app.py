#!/usr/bin/env python3

from aws_cdk import core

from eks_cdk.eks_cdk_stack import EksCdkStack


app = core.App()
EksCdkStack(app, "eks-cdk")

app.synth()
