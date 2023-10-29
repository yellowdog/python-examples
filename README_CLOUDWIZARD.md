# YellowDog Cloud Wizard

<!--ts-->
* [YellowDog Cloud Wizard](#yellowdog-cloud-wizard)
* [Overview](#overview)
* [Quickstart Guide (AWS)](#quickstart-guide-aws)
   * [Creation](#creation)
   * [Removal](#removal)
* [YellowDog Prerequisites](#yellowdog-prerequisites)
* [Details of Operation: AWS](#details-of-operation-aws)
   * [AWS Prerequisites](#aws-prerequisites)
   * [Cloud Wizard Setup](#cloud-wizard-setup)
      * [Network Details](#network-details)
      * [AWS Account Setup](#aws-account-setup)
      * [YellowDog Platform Setup](#yellowdog-platform-setup)
   * [Cloud Wizard Teardown](#cloud-wizard-teardown)
   * [Idempotency](#idempotency)

<!-- Created by https://github.com/ekalinin/github-markdown-toc -->
<!-- Added by: pwt, at: Sat Oct 28 17:06:49 BST 2023 -->

<!--te-->

# Overview

YellowDog Cloud Wizard is an **experimental** utility that automates the process of configuring a cloud provider account for use with YellowDog, and for creating YellowDog resources that work with the account. The goal is to make it quick and easy to get from opening a new cloud provider account to using it productively with YellowDog. 

Cloud Wizard currently supports AWS, but support for other cloud providers is under development.

# Quickstart Guide (AWS)

1. Ensure you have AWS credentials for the root user in your AWS account, or for another user with IAM administration rights. Set the AWS credentials via [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) or via [credential files](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

2. Ensure you've created an **Application** in your YellowDog account, and you've recorded the Application's `Key ID` and `Key Secret`. Set up the following environment variables, inserting your Application key and secret where indicated:

**Linux and macOS**
```commandline
export YD_KEY=<Insert your Application Key ID here>
export YD_SECRET=<Insert your Application Key Secret here>
```
**Windows Command Prompt**
```commandline
set YD_KEY <Insert your Application Key ID here>
set YD_SECRET <Insert your Application Key Secret here>
```

## Creation

Run the Cloud Wizard setup command:

```commandline
yd-cloudwizard --cloud-provider=aws --region-name=eu-west-2 setup
```

Adjust the `--region-name` as required to specify in which region your S3 storage bucket is created. If omitted, the default from your configuration will be used, otherwise the AWS default of `us-east-1` will be used.

Once the command has configured the necessary aspects of your AWS account, it will present a list of AWS Availability Zones. Select the Availability Zone(s) you'd like to use. For example:

```commandline
2023-10-23 10:37:25 : Please select the AWS availability zones for which to create YellowDog Source Templates
2023-10-23 10:37:25 : Displaying matching AWS Availability Zones(s):

    ┌─────┬─────────────────────┬──────────────────────────┬─────────────────────────────┐
    │   # │ Availability Zone   │ Default Subnet ID        │ Default Security Group ID   │
    ├─────┼─────────────────────┼──────────────────────────┼─────────────────────────────┤
    │   1 │ eu-west-1a          │ subnet-0822cd9a5f590a606 │ sg-06092420b42475007        │
    │   2 │ eu-west-1b          │ subnet-0a94cd2ec3e925648 │ sg-06092420b42475007        │
    │   3 │ eu-west-1c          │ subnet-0c6b29562e2c5b44e │ sg-06092420b42475007        │
    │   4 │ eu-west-2a          │ subnet-071832b5cf5c86f78 │ sg-031ed23c7961e3b25        │
    │   5 │ eu-west-2b          │ subnet-0c9dccd7e1ef4ed10 │ sg-031ed23c7961e3b25        │
    │   6 │ eu-west-2c          │ subnet-09b1e54baa4282823 │ sg-031ed23c7961e3b25        │
    └─────┴─────────────────────┴──────────────────────────┴─────────────────────────────┘

2023-10-23 10:37:25 : Please select items (e.g.: 1,2,4-7 / *) or press <Return> to cancel: 1-6
2023-10-23 10:37:35 : Selected item number(s): 1, 2, 3, 4, 5, 6
2023-10-23 10:37:35 : Creating YellowDog Compute Source Templates
```

The command will then proceed to create two YellowDog Compute Source templates for each selected Availability Zone, one for on-demand VMs, one for spot VMs. The command will also create a small selection of Compute Requirement Templates that make use of the Source Templates. All templates created have the prefix `cloudwizard-aws`.

The resources that were created can be inspected in JSON format in the file `cloudwizard-aws-yellowdog-resources.json`.

The Compute Requirement Templates are then available for use in YellowDog provisioning requests via the YellowDog API; note that an `Images ID` must be supplied.

The AWS Key Secret is not displayed during command operation, and is not retained locally, for security reasons. If you wish to display it, use the `--show-secrets` command line option when invoking `yd-cloudwizard`.

At the conclusion of a successful setup, the command will display the YellowDog Keyring name and password. This password will not be displayed again, and is required to claim access to the Keyring on behalf of your YellowDog Portal user account, allowing you to control AWS resources via the Portal.

## Removal

The AWS account settings and YellowDog resources that were created can be entirely removed using the `teardown` operation:

```commandline
yd-cloudwizard --cloud-provider=aws --region-name=eu-west-2 teardown
```

All destructive operations will require user confirmation; to avoid this, use the `--yes`/`-y` command line option.

# YellowDog Prerequisites

You'll need a YellowDog Platform account, and to have created an **Application** via the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications). The Application must belong to a group that has the following permissions at a minimum: `KEYRING_WRITE`, `COMPUTE_SOURCE_TEMPLATE_WRITE` and `COMPUTE_REQUIREMENT_TEMPLATE_WRITE`. If you make the Application a member of the `administrators` group, it will acquire these rights automatically.

The Application's **Key ID** and **Key Secret** need to be available to the Cloud Wizard command either (1) via the environment variables `YD_KEY` and `YD_SECRET`, or (2) they can be set on the command line using the `--key`/`-k` and `--secret`/`-s` options, or (3) they can be set in a `config.toml` configuration file as follows:

```toml
common.key = "<Insert Key ID>"
common.secret = "<Insert Key Secret>"
```

# Details of Operation: AWS

## AWS Prerequisites

You'll need an AWS account along with AWS access keys for the root user or for another user with the rights to manage IAM users and policies. The access keys will need to be accessible to the Cloud Wizard command either via [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html) or via [credential files](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

## Cloud Wizard Setup

The Cloud Wizard command is run using: `yd-cloudwizard --cloud-provider=aws --region-name=eu-west-2 setup`.

Run the command with the `--help`/`-h` option to see the available options.

### Network Details

Cloud Wizard expects to use the default VPC, default subnet(s), and default security group in each AWS region for which your account is enabled. These are set up automatically when you create your AWS account, and must be present for Cloud Wizard to work with your selected regions.

The default **subnets** are provided with a route to a gateway which allows instances to make outbound connections to the Internet. However, no NAT gateway is provided (this is a separately chargeable AWS service), so instances must have public IP addresses to connect to the Internet and specifically to connect back to the YellowDog Platform.

The default **security group** allows unrestricted traffic between instances on the subnet, and allows unrestricted outbound traffic to any address including the public Internet. It allows **no** inbound access from outside the subnet. Hence, if inbound access is required (e.g., SSH access to an instance), this must be added manually to each default security group in each region for which it is required.

Cloud Wizard will interrogate your AWS account to find out which regions are available, and to determine the default security group for the region, and the default subnet for each availability zone within the region. Network details are **only** collected for the regions in which YellowDog supplies default public YellowDog VM images (i.e., AWS AMIs), which are as follows: `eu-west-1`, `eu-west-2`, `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`.

### AWS Account Setup

Cloud Wizard performs the following actions in your AWS account:

1. It creates a new IAM user called `yellowdog-cloudwizard-user`.
2. It creates a new IAM policy called `yellowdog-cloudwizard-policy`, containing the capabilities required for YellowDog to use your AWS account on behalf of `yellowdog-cloudwizard-user`.
3. It attaches the IAM policy to the IAM user.
4. It creates a new access key for the IAM user; note that the secret access key is not displayed by default and will not be recorded other than in the Credential to be created within YellowDog. To display the secret access key, run the Cloud Wizard command with the `--show-secrets` option.
5. It adds the `AWSServiceRoleForEC2Spot` service linked role to the AWS account. This allows spot instances to be provisioned by YellowDog.
6. It creates an S3 storage bucket named `yellowdog-cloudwizard-<aws_user_id>`. The AWS user ID is required to ensure that the bucket name is unique within the AWS region. Adjust the `--region-name` as required to specify in which region your S3 storage bucket is created. If omitted, the default from your configuration will be used, otherwise the AWS default of `us-east-1` will be used.
7. A policy is attached to the bucket allowing the `yellowdog-cloudwizard-user` to access the S3 bucket.

The steps above are essentially an automated version of YellowDog's [AWS account configuration guidelines](https://docs.yellowdog.co/#/knowledge-base/configuring-an-aws-account-for-use-with-yellowdog). Note that the addition of the Service linked role for AWS Fleet is omitted.

Some AWS IAM settings take a little while to percolate through the AWS account. In particular, the `AWSServiceRoleForEC2Spot` service linked role may not take effect immediately, meaning that spot instances cannot be provisioned.

### YellowDog Platform Setup

Cloud Wizard performs the following actions in your YellowDog Platform account:

1. It creates a YellowDog Keyring called `cloudwizard-aws`. The Keyring name and password are displayed at the end of the Cloud Wizard setup process, and the password will not be displayed again. The Keyring name and password are required for your YellowDog Portal user account to be able to claim the Keyring, and use the credential(s) it contains via the Portal.


2. It creates a Credential called `cloudwizard-aws` contained within the `cloudwizard-aws` Keyring, containing the access key created during the AWS account setup described above.


3. It creates a range of Compute Source Templates, two for each AWS availability zone, one for **on-demand** instances and the other for **spot** instances. Each source is given a name with the following pattern: `cloudwizard-aws-eu-west-1a-ondemand`. Instances will use the `cloudwizard-aws/cloudwizard-aws` Credential. Instances will be created with public IP addresses, to permit outbound Internet access. The instance type and Images ID are left as `any`, to be set at higher levels. Any instances created from the source will be tagged with `yd-cloudwizard=yellowdog-cloudwizard-source`.


4. It creates a small range of example Compute Requirement Templates that use the sources above. There are two **static waterfall** provisioning strategy examples, one containing all the on-demand sources, the other containing all the spot sources. Two equivalent templates are created for the **static split** provisioning strategy. All of these templates specify the `t3a.micro` AWS instance type. In addition, an example **dynamic** template is created that will be constrained to AWS instances with 4GB of memory or greater, ordered by lowest cost first. In all cases, no `Images Id` is specified, so this must be supplied at the time of instance provisioning. Each template is given a name such as: `cloudwizard-aws-split-ondemand-t3amicro` or `cloudwizard-aws-dynamic-waterfall-lowestcost`.


5. The Compute Source Template and Compute Requirement Template definitions are saved in a JSON resource specification file called `cloudwizard-aws-yellowdog-resources.json`. This file can be edited (for example, to change the instance types), and used with the `yd-create` command for to update the resources.

6. It creates a Namespace configuration, which maps the YellowDog namespace `cloudwizard-aws` into the S3 storage bucket `yellowdog-cloudwizard-<aws_user_id>`.

## Cloud Wizard Teardown

All settings and resources created by Cloud Wizard can be removed using `yd-cloudwizard --cloud-provider=aws --region-name=eu-west-2 teardown`. All destructive steps will require user confirmation unless the `--yes`/`-y` option is used.

The following actions are taken in the **YellowDog account**:

1. All Compute Source Templates and Compute Requirement Templates with names starting with `cloudwizard-aws` are removed.
2. The `cloudwizard-aws` Keyring is removed.
3. The `cloudwizard-aws` Namespace configuration is removed.

The following actions are taken in the **AWS account**:

1. The access key for `yellowdog-cloudwizard-user` is deleted.
2. The IAM policy `yellowdog-cloudwizard-policy` is detached from the user.
3. The IAM policy `yellowdog-cloudwizard-policy` is deleted.
4. The user `yellowdog-cloudwizard-user` is deleted.
5. The `AWSServiceRoleForEC2Spot` service linked role is removed.
6. The S3 bucket `yellowdog-cloudwizard-<aws_user_id>` is emptied of objects, and removed.

## Idempotency

In general, it's safe to invoke Cloud Wizard multiple times for both setup and teardown operations. Depending on the setting/resource it will be ignored if present, or the user will be asked to confirm deletion/replacement.

If there are multiple invocations of `setup`, then the AWS access key and YellowDog Credential will be updated (at the user's option). Also, the Compute Source and Compute Requirement templates will be updated, and may differ in their contents if different availability zones are selected during each invocation. The resource specification JSON file will be overwritten.
