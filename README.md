# Introduction

This repository contains simple example Python [scripts](scripts) for submitting work to the YellowDog Platform, cancelling work, downloading objects and cleaning up the YellowDog Object Store.

It also provides scripts for creating Provisioned Worker Pools, shutting down Worker Pools, and terminating the Compute Requirements providing those Worker Pools.

## On Premise

A template [on-premise configuration](agent/application.yaml.template) is provided to use when deploying the YellowDog agent in Configured Worker Pools.

## Scripts

The Python scripts are contained in the [scripts](/scripts) directory. They use the [YellowDog Python SDK](https://github.com/yellowdog/yellowdog-sdk-python-public)  to interact with the YellowDog Platform. See the scripts [README](scripts/README.md) file for more details.

## Prerequisites

To submit **Work Requirements** to YellowDog, you'll need the following:

1. A YellowDog Platform Account.


2. In the **Accounts** section under the **Applications** tab of the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be displayed once).


3. Copy `config.toml.template` to `config.toml` and in the `common` section populate the `key` and `secret` properties using the values obtained above. These allow the Python scripts to connect to the YellowDog Platform. Modify the `namespace` (for grouping YellowDog objects) and `tag` (used for naming objects) properties as required. In the `workRequirement` section, optionally modify the `workerTags` property to include one or more tags declared by your YellowDog workers.

To create **Provisioned Worker Pools**, you'll also need:

4. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required.


5. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) and Worker Tag required by the Work Requirements to be submitted.


6. In your `config.toml` file, populate the `workerPool` section, including using the `templateId` from the Compute Requirement Template above.
