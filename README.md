# Introduction

This repository contains examples and tools for working with the [**YellowDog Platform**](https://yellowdog.co).

## Prerequisites

To submit **Work Requirements** to YellowDog for processing by Configured Worker Pools (on-premise) and/or Provisioned Worker Pools (cloud-provisioned resources), you'll need:

1. A YellowDog Platform Account.


2. An Application Key & Secret: in the **Accounts** section under the **Applications** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be displayed once).


To create **Provisioned Worker Pools**, you'll need:

3. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required. The Application must be granted access to the Keyring.


4. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) to match the Work Requirements to be submitted.

To set up **Configured Worker Pools**, you'll need:

5. A Configured Worker Pool Token: from the **Workers** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/workers), use the **+Add Configured Worker Pool** button to create a new Worker Pool and generate a token.


6. Obtain the YellowDog agent and install/configure it on your on-premise systems using the Token above.

## Python Scripts/Utilities

The [scripts](/scripts) directory contains Python commands for submitting work to the YellowDog Platform, cancelling work, downloading objects and deleting objects in the YellowDog Object Store.

It also provides commands for creating Provisioned Worker Pools, shutting down Worker Pools, and terminating the Compute Requirements providing those Worker Pools.

The Python scripts use the [YellowDog Python SDK](https://github.com/yellowdog/yellowdog-sdk-python-public) to interact with the YellowDog Platform. See the scripts [README](scripts/README.md) file for more details.

## Resources for Configured Worker Pools (on-Premise Systems)

A template [on-premise configuration](agent/application.yaml.template) is provided to use when deploying the YellowDog agent in Configured Worker Pools on your own hardware.
