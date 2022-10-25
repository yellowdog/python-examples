# YellowDog Python Scripts

<!--ts-->
* [YellowDog Python Scripts](#yellowdog-python-scripts)
   * [Overview](#overview)
   * [Installation](#installation)
      * [Initial Installation](#initial-installation)
      * [Update](#update)
   * [Usage](#usage)
   * [Configuration](#configuration)
      * [Common Properties](#common-properties)
      * [Work Requirement Properties](#work-requirement-properties)
         * [Work Requirement JSON File Structure](#work-requirement-json-file-structure)
         * [Property Inheritance](#property-inheritance)
         * [Work Requirement Property Dictionary](#work-requirement-property-dictionary)
         * [Automatic Properties](#automatic-properties)
            * [Work Requirement, Task Group and Task Naming](#work-requirement-task-group-and-task-naming)
            * [Task Types](#task-types)
         * [Examples](#examples)
            * [TOML Properties in the workRequirement Section](#toml-properties-in-the-workrequirement-section)
            * [JSON Properties at the Work Requirement Level](#json-properties-at-the-work-requirement-level)
            * [JSON Properties at the Task Group Level](#json-properties-at-the-task-group-level)
            * [JSON Properties at the Task Level](#json-properties-at-the-task-level)
      * [Worker Pool Properties](#worker-pool-properties)
         * [Automatic Properties](#automatic-properties-1)
         * [Worker Pool JSON File Structure](#worker-pool-json-file-structure)
         * [Examples](#examples-1)
            * [TOML Properties in the workerPool Section](#toml-properties-in-the-workerpool-section)
   * [Command List](#command-list)
      * [yd-submit](#yd-submit)
      * [yd-provision](#yd-provision)
      * [yd-cancel](#yd-cancel)
      * [yd-download](#yd-download)
      * [yd-delete](#yd-delete)
      * [yd-shutdown](#yd-shutdown)
      * [yd-terminate](#yd-terminate)

<!-- Added by: pwt, at: Tue Oct 25 15:55:14 BST 2022 -->

<!--te-->

## Overview

This repository contains a set of command line Python scripts for interacting with the YellowDog Platform. The scripts use the [YellowDog Python SDK](https://docs.yellowdog.co/api/python/api.html), and support:

- **Provisioning** Worker Pools
- **Submitting** Work Requirements
- **Downloading** Results
- **Shutting Down** Worker Pools and **Terminating** Compute Requirements
- **Cancelling** Work Requirements
- **Deleting** objects in the YellowDog Object Store

The operation of the commands is controlled using TOML configuration files. In addition, Work Requirements and Worker Pools can be defined using JSON files providing extensive configurability.

## Installation

Requirements for installation:

1. Python version 3.7+
2. Git

It's recommended that installation is performed in a Python virtual environment (or similar) to isolate the installation from other Python instances on your system.

At present, the scripts are installed and updated directly from this GitHub repository using `pip`. The installation process will put a number of commands prefixed with `yd-` on the PATH created by your virtual environment.

### Initial Installation

```shell
pip install -U pip wheel
pip install -U git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

### Update

```shell
pip install -U --force-reinstall --no-deps git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

## Usage

Commands are run from the command line. Invoking the command with the `--help` or `-h` option will display the command line options applicable to a given command, e.g.:

```shell
% yd-cancel --help
usage: yd-cancel [-h] [--config CONFIG_FILE.toml]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_FILE.toml, -c CONFIG_FILE.toml
                        script configuration file in TOML format; (default is 'config.toml' in the current directory)
```

## Configuration

The operation of all commands is configured using a TOML file. The file has a mandatory `common` section, and optional `workRequirement` and `workerPool` sections. There is a documented template TOML file provided in [config.toml.template](config.toml.template).

The configuration can be supplied to commands in three different ways:

1. On the command line, using the `--config` or `-c` options, e.g.:<br>`yd-submit -c jobs/config_1.toml`
2. Using the `YD_CONF` environment variable, e.g.: <br>`export YD_CONF="jobs/config_1.toml"`
3. Using the default filename of `config.toml` in the current directory

The options above are shown in order of precedence, i.e., a filename supplied on the command line supersedes one set in `YD_CONF`, which supersedes the default.

### Common Properties

The `[common]` section of the configuration file contains the following mandatory properties:

| Property    | Description                                                                   |
|:------------|:------------------------------------------------------------------------------|
| `key`       | The **key** of the YellowDog Application under which the commands will run    |
| `secret`    | The **secret** of the YellowDog Application under which the commands will run |
| `namespace` | The **namespace** to be used to manage resources                              |
| `tag`       | The **tag** to be used for tagging resources and naming objects               |

An example `common` section is shown below:

```toml
[common]
    key = "asdfghjklzxcvb-1234567"
    secret = "qwertyuiopasdfghjklzxcvbnm1234567890qwertyu"
    namespace = "PROJECT-X"
    tag = "TESTING-{{username}}"
```

The indentation is optional in TOML files and is for readability only.

Note the use of `{{username}}` in the value of the `tag` property: this is a **Mustache** template directive that can optionally be used to insert the login username of the user running the commands. So, for username `abc`, the `tag` would be set to `TESTING-ABC`. This can be helpful to disambiguate multiple users running with the same configuration data. The Mustache directive can also be used within the `namespace` value.

### Work Requirement Properties

The `workRequirement` section of the configuration file is optional. It's used only by the `yd-submit` command, and controls the Work Requirement that is submitted to the Platform.

The details of a Work Requirement to be submitted can be captured entirely within the TOML configuration file for simple examples. More complex examples capture the Work Requirement in a combination of the TOML file plus a JSON document, or in a JSON document only.

#### Work Requirement JSON File Structure

Work Requirements are represented in JSON documents using a containment hierarchy of a **Work Requirement** containing a **list of Task Groups**, containing a **list of Tasks**.

A very simple example document is shown below with a top-level Work Requirement containing two Task Groups each containing two Tasks, each with a different set of arguments to be passed to the Task.

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": [1, 2, 3]
        },
        {
          "arguments": [4, 5, 6]
        }
      ]
    },
    {
      "tasks": [
        {
          "arguments": [7, 8, 9]
        },
        {
          "arguments": [10, 11, 12]
        }
      ]
    }
  ]
}

```

To specify the file containing the JSON document, either populate the `workRequirementData` property in the `workRequirement` section of the TOML configuration file with the JSON filename, or specify it on the command line using the `--work-req` or `-r` options (which will override any value set in the TOML file), e.g.

`yd-submit --config myconfig.toml --work-req my_workreq.json`

#### Property Inheritance

To simplify and optimise the definition of Work Requirements, there is a property inheritance mechanism. Properties that are set at a higher level in the hierarchy are inherited at lower levels, unless explicitly overridden.

This means that a property set in the `workRequirement` section of the TOML file can be inherited successively by the Work Requirement, Task Groups and Tasks in the JSON document (assuming the property is valid at each level).  Hence, Tasks inherit from Task Groups, which inherit from the Work Requirement in the JSON document, which inherits from the `workRequirement` properties in the TOML file.

Overridden properties are also inherited. E.g., if a property is set at the Task Group level, it will be inherited by the Tasks in that Task Group unless explicitly overridden.

#### Work Requirement Property Dictionary

The following table outlines all the properties available for defining Work Requirements, and the levels at which they are allowed to be used. So, for example, the `provider` property can be set in the TOML file, at the Work Requirement Level or at the Task Group Level, but not at the Task level, and Property `dependentOn` can only be set at the Task Group level.

All properties are optional except for **`taskType`** (or **`TaskTypes`**) and **`executable`**. Note that the currently supported Task Types are `bash` and `docker`.

| Property Name         | Description                                                                                                                                                              | TOML | WR  | Task Grp | Task |
|:----------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----|:----|:---------|:-----|
| `arguments`           | The list of arguments to be passed to the Task when it is executed. E.g.: `[1, "Two"]`.                                                                                  | Yes  | Yes | Yes      | Yes  |
| `autoFail`            | If true, the Task Group will be failed automatically if any contained tasks fail. Default:`true`.                                                                        | Yes  | Yes | Yes      |      |
| `captureTaskOutput`   | Whether the console output of a Task's process should be uploaded to the YellowDog Object Store on Task completion. Default: `true`.                                     | Yes  | Yes | Yes      | Yes  |
| `completedTaskTtl`    | The time (in minutes) to live for completed Tasks. If set, Tasks that have been completed for longer than this period will be deleted. E.g.: `10.0`.                     | Yes  | Yes | Yes      |      |
| `dependentOn`         | The name of another Task Group within the same Work Requirement that must be successfully completed before the Task Group is started. E.g. `"TG_1"`.                     |      |     | Yes      |      |
| `dockerPassword`      | The password for DockerHub, used by the `docker` Task Type. E,g., `"my_password"`.                                                                                       | Yes  | Yes | Yes      | Yes  |
| `dockerUsername`      | The username for DockerHub, used by the `docker` Task Type. E,g., `"my_username"`.                                                                                       | Yes  | Yes | Yes      | Yes  |
| `environment`         | The environment variables to set for a Task when it's executed. E.g., JSON: `{"VAR_1": "abc", "VAR_2": "def"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                  | Yes  | Yes | Yes      | Yes  |
| `exclusiveWorkers`    | If true, then do not allow claimed Workers to be shared with other Task Groups; otherwise, Workers can be shared. Default:`false`.                                       | Yes  | Yes | Yes      |      |
| `executable`          | The executable to run when the Task is executed. For the `bash` Task Type, this is the name of the Bash script. For `docker`, the name of the container.                 | Yes  | Yes | Yes      | Yes  |
| `fulfilOnSubmit`      | Indicates if the Work Requirement should be fulfilled when it is submitted, rather than being allowed to wait in PENDING status. Default:`false`.                        | Yes  | Yes |          |      |
| `inputs`              | The list of input files to be uploaded to the YellowDog Object Store, and downloaded to the node on which a Task will execute. E.g. `["a.sh", "b.sh"]`.                  | Yes  | Yes | Yes      | Yes  |
| `instanceTypes`       | The machine instance types that can be used to execute Tasks. E.g., `["t3.micro", "t3a.micro"]`.                                                                         | Yes  | Yes | Yes      |      |
| `intermediateFiles`   | A list of output files from the execution of a previous Task to be downloaded for use by the current Task. E.g.: `["Task_Group_1/Task_1/results.txt"]`.                  |      |     | Yes      | Yes  |
| `maximumTaskRetries`  | The maximum number of times a Task can be retried after it has failed. E.g.: `5`.                                                                                        | Yes  | Yes | Yes      | Yes  |
| `maxWorkers`          | The maximum number of Workers that can be claimed for the associated Task Group. E.g., `10`.                                                                             | Yes  | Yes | Yes      |      |
| `minWorkers`          | The minimum number of Workers that the associated Task Group requires. This many workers must be claimed before the associated Task Group will start working. E.g., `1`. | Yes  | Yes | Yes      |      |
| `name`                | The name of the Work Requirement, Task Group or Task. E.g., `"NAME"`. Note that the `name` property is not inherited.                                                    | Yes  | Yes | Yes      | Yes  |
| `outputs`             | The files to be uploaded to the YellowDog Object Store by a Worker node on completion of the Task. E.g., `["results_1.txt", "results_2.txt"]`.                           | Yes  | Yes | Yes      | Yes  |
| `priority`            | The priority of Work Requirements and Task Groups. Higher priority acquires Workers ahead of lower priority. Note: not inherited by Task Group from WR. E.g., `0.0`.     | Yes  | Yes | Yes      |      |
| `providers`           | Constrains the YellowDog Scheduler only to execute tasks from the associated Task Group on the specified providers. E.g., `["AWS", "GOOGLE"]`.                           | Yes  | Yes | Yes      |      |
| `ram`                 | Range constraint on GB of RAM that are required to execute Tasks. E.g., `[2.5, 4.0]`.                                                                                    | Yes  | Yes | Yes      |      |
| `regions`             | Constrains the YellowDog Scheduler only to execute Tasks from the associated Task Group in the specified regions. E.g., `["eu-west-2]`.                                  | Yes  | Yes | Yes      |      |
| `tasksPerWorker`      | Determines the number of Worker claims based on splitting the number of unfinished Tasks across Workers. E.g., `1`.                                                      | Yes  | Yes | Yes      |      |
| `taskCount`           | The number of times to execute the Task. Only used when a JSON Work Requirement document is not provided. E.g., `1`.                                                     | Yes  |     |          |      |
| `taskType`            | The Task Type of a Task. E.g., `"docker"`.                                                                                                                               | Yes  |     |          | Yes  |
| `taskTypes`           | The list of Task Types required by the range of Tasks in a Task Group. E.g., `["docker", bash"]`.                                                                        |      | Yes | Yes      |      |
| `vcpus`               | Range constraint on number of vCPUs that are required to execute Tasks E.g., `[2.0, 4.0]`.                                                                               | Yes  | Yes | Yes      |      |
| `workerTags`          | The list of Worker Tags that will be used to match against the Worker Tag of a candidate Worker. E.g., `["tag_x", "tag_y"]`.                                             | Yes  | Yes | Yes      |      |
| `workRequirementData` | The name of the file containing the JSON document in which the Work Requirement is defined. E.g., `"test_workreq.json"`.                                                 | Yes  |     |          |      |

#### Automatic Properties

In addition to the inheritance mechanism, some properties are set automatically by the `yd-submit` command, as a usage convenience.

##### Work Requirement, Task Group and Task Naming

- The **Work Requirement** name is automatically set using a concatenation of `WR_`, the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `WR_MYTAG_221024T155524-40A`.
- **Task Group** names are automatically created for any Task Group that is not explicitly named, using names of the form `TaskGroup_1` (or `TaskGroup_01`, etc., for larger numbers of Task Groups).
- **Task** names are automatically created for any Task that is not explicitly named, using names of the form `Task_1` (or `Task_01`, etc., for larger numbers of Tasks). The Task counter resets for each different Task Group.

##### Task Types

- If `taskType` is set only at the TOML file level, then `taskTypes` is automatically populated for Task Groups, unless overridden.
- If `taskType` is set at the Task level, then `taskTypes` is automatically populated for Task Groups level using the accumulated Task Types from the Tasks, unless overridden.
- If `taskTypes` is set at the Task Group Level, and has only one Task Type entry, then `taskType` is automatically set at the Task Level using the single Task Type, unless overridden.

#### Examples

##### TOML Properties in the `workRequirement` Section

Here's an example of the `workRequirement` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workRequirement]
    arguments = [1, "TWO"]
    autoFail = false
    captureTaskOutput = true
    completedTaskTtl = 10
    dockerPassword = "myPassword"
    dockerUsername = "myUsername"
    environment = {MY_VAR = 100}
    exclusiveWorkers = false
    executable = "my-container"
    fulfilOnSubmit = false
    inputs = [
        "../app/main.py",
        "../app/requirements.txt"
    ]
    instanceTypes = ["t3a.micro", "t3.micro"]
    maxWorkers = 1
    maximumTaskRetries = 0
    minWorkers = 1
    name = "My-Work-Requirement"
    outputs = ["results.txt"]
    priority = 0.0
    providers = ["AWS"]
    ram = [0.5, 2.0]
    regions = ["eu-west-2"]
    taskCount = 100
    taskType = "docker"
    tasksPerWorker = 1
    vcpus = [1, 4]
    workerTags = ["TAG-{{username}}"]
#   workRequirementData = "work_requirement.json"
```

##### JSON Properties at the Work Requirement Level

Showing all possible properties at the Work Requirement level:

```json
{
  "arguments": [1, "TWO"],
  "autoFail": false,
  "captureTaskOutput": true,
  "completedTaskTtl": 10,
  "dockerPassword": "myPassword",
  "dockerUsername": "myUsername",
  "environment": {"MY_VAR": 100},
  "exclusiveWorkers": false,
  "executable": "my-container",
  "fulfilOnSubmit": false,
  "inputs": ["app/main.py", "app/requirements.txt"],
  "instanceTypes": ["t3a.micro", "t3.micro"],
  "maxWorkers": 1,
  "maximumTaskRetries": 0,
  "minWorkers": 1,
  "name": "My-Work-Requirement",
  "outputs": ["results.txt"],
  "priority": 0,
  "providers": ["AWS"],
  "ram": [0.5, 2],
  "regions": ["eu-west-2"],
  "taskTypes": ["docker"],
  "tasksPerWorker": 1,
  "vcpus": [1, 4],
  "workerTags": [],
  "taskGroups": [
    {
      "tasks": [
        {}
      ]
    }
  ]
}
```

##### JSON Properties at the Task Group Level

Showing all possible properties at the Task Group level:

```json
{
  "taskGroups": [
    {
      "arguments": [1, "TWO"],
      "autoFail": false,
      "captureTaskOutput": true,
      "completedTaskTtl": 10,
      "dependentOn": "First-Task-Group",
      "dockerPassword": "myPassword",
      "dockerUsername": "myUsername",
      "environment": {"MY_VAR": 100},
      "exclusiveWorkers": false,
      "executable": "my-container",
      "inputs": ["app/main.py", "app/requirements.txt"],
      "instanceTypes": ["t3a.micro", "t3.micro"],
      "maximumTaskRetries": 0,
      "maxWorkers": 1,
      "minWorkers": 1,
      "name": "My-Task-Group",
      "outputs": ["results.txt"],
      "priority": 0,
      "providers": ["AWS"],
      "ram": [0.5, 2],
      "regions": ["eu-west-2"],
      "taskTypes": ["docker"],
      "tasksPerWorker": 1,
      "vcpus": [1, 4],
      "workerTags": [],
      "tasks": [
        {}
      ]
    },
    {
      "name": "Second-Task-Group",
      "dependentOn": "First-Task-Group",
      "tasks": [
        {}
      ]
    }
  ]
}
```

##### JSON Properties at the Task Level

Showing all possible properties at the Task level:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": [],
          "captureTaskOutput": true,
          "dockerPassword": "myPassword",
          "dockerUsername": "myUsername",
          "environment": {"MY_VAR": 100},
          "executable": "my-container",
          "inputs": ["app/main.py", "app/requirements.txt"],
          "intermediateInputs": [],
          "name": "My-Task",
          "outputs": ["results.txt"],
          "taskType": "docker"
        }
      ]
    }
  ]
}
```

### Worker Pool Properties

The `workerPool` section of the TOML file defines the properties of the Worker Pool to be created, and is used by the `yd-provision` command. The only mandatory property is the `templateId`. All other properties have defaults (or are not required).

The following properties are available:

| Property               | Description                                                                                            | Default        |
|:-----------------------|:-------------------------------------------------------------------------------------------------------|:---------------|
| `autoscalingIdleDelay` | The time in minutes for which a node can be idle before it can be shut down by auto-scaling.           | `10.0` minutes |
| `autoShutdown`         | Whether the Worker Pool is shut down after all nodes have been idle for the `autoShutdownDelay`.       | `true`         |
| `autoShutdownDelay`    | The delay in minutes for which all nodes can be idle before the Worker Pool is shut down.              | `10.0` minutes |
| `minNodes`             | The minimum number of nodes to which the Worker Pool can be scaled down.                               | `0`            |
| `maxNodes`             | The maximum number of nodes to which the Worker Pool can be scaled up.                                 | `1`            |
| `name`                 | The name of the Worker Pool.                                                                           | Automatic      |
| `nodeBootTimeLimit`    | The time in minutes allowed for a node to boot and register with the platform before it is terminated. | `10.0` minutes |
| `targetInstanceCount`  | The initial number of nodes to create for the Worker Pool.                                             | `1`            |
| `templateId`           | The YellowDog Compute Template ID to use for provisioning.                                             |                |
| `workersPerNode`       | The number of Workers to establish on each node in the Worker Pool.                                    | `1`            |
| `workerPoolData`       | The name of a file containing a JSON document defining a Worker Pool.                                  |                |
| `workerTag`            | The Worker Tag to publish for the all of the Workers.                                                  |                |

#### Automatic Properties

The name of the Worker Pool, if not supplied, is automatically generated using a concatenation of `WP_`, the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `WP_MYTAG_221024T155524-40A`.

#### Worker Pool JSON File Structure

**Experimental Feature**

It's also possible to capture a Worker Pool definition as a JSON document. The JSON filename can be supplied either using the command line with the `--worker-pool` or `-p` parameter with `yd-provision`, or by populating the `workerPoolData` property in the TOML configuration file with the JSON filename. Command line specification takes priority over TOML specification. The JSON specification allows the creation of **Advanced Worker Pools**, with different node types and the ability to specify Node Actions.

When using a JSON document to specify the Worker Pool, the schema of the document is identical to that expected by the YellowDog API for Worker Provisioning.

Examples will be provided at a later date.

#### Examples

##### TOML Properties in the `workerPool` Section

Here's an example of the `workerPool` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workerPool]
    autoShutdown = true
    autoShutdownDelay = 10
    autoscalingIdleDelay = 3
    maxNodes = 1
    minNodes = 1
    name = "My-Worker-Pool"
    nodeBootTimeLimit = 5
    targetInstanceCount = 1
    templateId = "ydid:crt:000000:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    workerTag = "TAG-{{username}}"
    workersPerNode = 1
#   workerPoolData = "worker_pool.json"
```

## Command List

### yd-submit

The `yd-submit` command submits a new Work Requirement, according to the Work Requirement definition found in the `workRequirement` section of the TOML configuration file and/or the specification found in the Work Requirement JSON document.

Once submitted, the Work Requirement will appear in the **Work** tab in the YellowDog Portal.

The Work Requirement's progress can be tracked to completion by using the `--follow` (or `-f`) option when invoking `yd-submit`.

### yd-provision

The `yd-provision` command provisions a new Worker Pool according to the specifications in the `workerPool` section of the TOML configuration file.

Once provisioned, the Worker Pool will appear in the **Workers** tab in the YellowDog Portal, and its associated Compute Requirement will appear in the **Compute** tab.

### yd-cancel

The `yd-cancel` command cancels any active Work Requirements, including any pending Task Groups and the Tasks they contain. 

The `namespace` and `tag` values in the `config.toml` file are used to identify which Work Requirements to cancel.

### yd-download

The `yd-download` command downloads any objects created in the YellowDog Object Store.

The `namespace` and `tag` values are used to determine which objects to download. Objects will be downloaded to a directory with the same name as `namespace`. If a directory already exists, a new directory with name `<namespace>.01` (etc.) will be created.

### yd-delete

The `yd-delete` command deletes any objects created in the YellowDog Object Store.

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete.

### yd-shutdown

The `yd-shutdown` command shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

### yd-terminate

The `yd-terminate` command immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.