# Diving into Container Insights cost optimizations for Amazon EKS

This project contains the supporting code for the ["Diving into Container Insights cost optimizations for Amazon EKS"](https://aws.amazon.com/blogs/containers/diving-into-container-insights-cost-optimizations-for-amazon-eks/) blog post.

# Getting started

To build and deploy this application, as part of the pre-requisites, you will need:

- weaveworks eksctl
- AWS CLI 2.x
- kubectl
- An EKS cluster with an EC2-backed data plane
- Helm 3
- Python 3.8+
- AWS CDK 2.x Toolkit
- Docker

AWS Cloud9 makes the setup easy. AWS Cloud9 is a cloud-based integrated development environment (IDE) that let you write, run, and debug your code with just a browser. It comes with the AWS tools, Git, and Docker installed.
Create a new [AWS Cloud9 EC2 environment](https://docs.aws.amazon.com/cloud9/latest/user-guide/create-environment-main.html) based on Amazon Linux. It is recommended to select an instance with **at least 2 GiB of RAM** (for example, t3.small).

## Weaveworks eksctl

Download and install the latest *eksctl* binary using the following commands:

```sh
$ curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
$ sudo mv /tmp/eksctl /usr/local/bin
```

You can validate that eksctl has been successfully installed with the following command:

```sh
# The actual version might differ
$ eksctl version
0.137.0
```

## AWS CLI 2.x

You can refer to the [official documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

In Cloud9, to upgrade the *aws CLI* to version 2.x, you can use the following commands:

```sh
$ curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
$ unzip awscliv2.zip
$ sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
$ rm -rf aws
```

You can validate that the aws cli has been successfully upgraded with the following command:

```sh
# The actual version might differ
$ aws --version
aws-cli/2.11.11 Python/3.11.2 Linux/4.14.309-231.529.amzn2.x86_64 exe/x86_64.amzn.2 prompt/off
```

## kubectl

Download and install the kubectl binary for Kubernetes version 1.24 from Amazon S3 using the following commands:

```sh
$ curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.24.9/2023-01-11/bin/linux/amd64/kubectl
$ chmod +x ./kubectl
$ sudo mv ./kubectl /usr/local/bin
```

You can validate that kubectl has been successfully installed with the following command:

```sh
$ kubectl version
Client Version: version.Info{Major:"1", Minor:"24+", GitVersion:"v1.24.9-eks-49d8fe8", GitCommit:"53e5004c71669ab3835f7b9c30f79dee82c30c17", GitTreeState:"clean", BuildDate:"2023-01-09T23:48:25Z", GoVersion:"go1.18.9", Compiler:"gc", Platform:"linux/amd64"}
```

## An EKS cluster with an EC2-backed data plane

**Optionally**, in case you do not have a running cluster, you can create one using *eksctl* and the provided [sample configuration](./deploy/cluster.yaml): 

```sh
$ eksctl create cluster -f deploy/cluster.yaml
```
You can validate that you can access the newly created cluster with the following command:

```sh
$ kubectl cluster-info
Kubernetes control plane is running at https://462641F7621C08A253274xxxxxxxx.gr7.eu-central-1.eks.amazonaws.com
CoreDNS is running at https://462641F7621C08A253274xxxxxxxx.gr7.eu-central-1.eks.amazonaws.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

## Helm 3

Download and install Helm 3 using the following commands:

```sh
$ curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
$ chmod 700 get_helm.sh
$ ./get_helm.sh
```

You can validate that Helm 3 has been successfully installed with the following command:

```sh
# The actual version might differ
$ helm version
version.BuildInfo{Version:"v3.11.1", GitCommit:"293b50c65d4d56187cd4e2f390f0ada46b4c4737", GitTreeState:"clean", GoVersion:"go1.18.10"}
```
## Python 3.8+ environment

Create a python virtual environment, based on python 3.8+ using the following commands:

```sh
# When using AWS Cloud9 you need to make sure to install python 3.8 as python 3.7 is installed by default
$ sudo amazon-linux-extras install python3.8
# Create a new virtual environment
$ python3.8 -m venv .venv
# Activate the newly created virtual environment
$ source .venv/bin/activate
# Upgrade pip
$ pip install --upgrade pip
```

You can validate that the python environment has been successfully installed with the following commands :

```sh
# The actual version might differ
$ python --version 
Python 3.8.16
```

## AWS CDK 2.x Toolkit

Locally install the AWS CDK Toolkit node modules using the following command:

```sh
# Make sure you execute this command from the repository root where the project.json file is located
$ npm install
```

You can validate that the CDK has been successfully installed with the following command:

```sh
$ npx cdk --version
2.60.0 (build 2d40d77)
```

## Docker

Docker is installed by default in Cloud9.
In case you might not be using Cloud9 please refer to the [Docker official documentation](https://docs.docker.com/get-docker/).

# Contributing

Please create a new GitHub issue for any feature requests, bugs, or documentation improvements.

Where possible, please also submit a pull request for the change.
