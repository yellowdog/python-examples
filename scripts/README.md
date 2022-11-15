# YellowDog Python Scripts

<!--ts-->
* [YellowDog Python Scripts](#yellowdog-python-scripts)
* [Overview](#overview)
* [Installation](#installation)
   * [Initial Installation](#initial-installation)
   * [Update](#update)
* [Usage](#usage)
* [Configuration](#configuration)
   * [Naming Restrictions](#naming-restrictions)
   * [Common Properties](#common-properties)
      * [Mustache Template Directives in Common Properties](#mustache-template-directives-in-common-properties)
         * [Default Mustache Directives](#default-mustache-directives)
         * [User-Defined Mustache Directives](#user-defined-mustache-directives)
      * [Specifying Common Properties using the Command Line or Environment Variables](#specifying-common-properties-using-the-command-line-or-environment-variables)
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
      * [Mustache Template Directives in Work Requirement Properties](#mustache-template-directives-in-work-requirement-properties)
   * [Worker Pool Properties](#worker-pool-properties)
      * [Automatic Properties](#automatic-properties-1)
      * [Worker Pool JSON File Structure](#worker-pool-json-file-structure)
      * [Examples](#examples-1)
         * [TOML Properties in the workerPool Section](#toml-properties-in-the-workerpool-section)
* [Command List](#command-list)
   * [yd-submit](#yd-submit)
   * [yd-provision](#yd-provision)
   * [yd-cancel](#yd-cancel)
   * [yd-abort](#yd-abort)
   * [yd-download](#yd-download)
   * [yd-delete](#yd-delete)
   * [yd-shutdown](#yd-shutdown)
   * [yd-terminate](#yd-terminate)

<!-- Added by: pwt, at: Fri Nov  4 13:29:59 GMT 2022 -->

<!--te-->

# Overview

This repository contains a set of command line Python scripts for interacting with the YellowDog Platform. The scripts use the [YellowDog Python SDK](https://docs.yellowdog.co/api/python/api.html), and support:

- **Provisioning** Worker Pools
- **Submitting** Work Requirements
- **Downloading** Results
- **Shutting Down** Worker Pools and **Terminating** Compute Requirements
- **Cancelling** Work Requirements
- **Aborting** running Tasks
- **Deleting** objects in the YellowDog Object Store

The operation of the commands is controlled using TOML configuration files. In addition, Work Requirements and Worker Pools can be defined using JSON files providing extensive configurability.

# Installation

Requirements for installation:

1. Python version 3.7+
2. Git

It's recommended that installation is performed in a Python virtual environment (or similar) to isolate the installation from other Python instances on your system.

At present, the scripts are installed and updated directly from this GitHub repository using `pip`. The installation process will put a number of commands prefixed with `yd-` on the PATH created by your virtual environment.

## Initial Installation

```shell
pip install -U pip wheel
pip install -U git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

## Update

```shell
pip install -U --force-reinstall --no-deps git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

# Usage

Commands are run from the command line. Invoking the command with the `--help` or `-h` option will display the command line options applicable to a given command, e.g.:

```text
% yd-cancel --help
usage: yd-cancel [-h] [--config <config_file.toml>] [--key <app-key>] [--secret <app-secret>] [--namespace <namespace>]
                 [--tag <tag>] [--url <url>] [--mustache-substitution <var1=v1>] [--quiet] [--abort] [--interactive] [--yes]

optional arguments:
  -h, --help            show this help message and exit
  --config <config_file.toml>, -c <config_file.toml>
                        configuration file in TOML format; default is 'config.toml' in the current directory
  --key <app-key>, -k <app-key>
                        the YellowDog Application key
  --secret <app-secret>, -s <app-secret>
                        the YellowDog Application secret
  --namespace <namespace>, -n <namespace>
                        the namespace to use when creating and identifying entities
  --tag <tag>, -t <tag>
                        the tag to use for tagging and naming entities
  --url <url>, -u <url>
                        the URL of the YellowDog Platform API
  --mustache-substitution <var1=v1>, -m <var1=v1>
                        user-defined Mustache substitution; can be used multiple times
  --quiet, -q           suppress (non-error, non-interactive) status and progress messages
  --abort, -a           abort all running tasks with immediate effect
  --interactive, -i     list, and interactively select, items to act on
  --yes, -y             perform destructive actions without requiring user confirmation
```

# Configuration

By default, the operation of all commands is configured using a TOML configuration file.

The configuration file has three possible sections:

1. A `common` section that contains required security properties for interacting with the YellowDog platform, sets the Namespace in which YellowDog assets and objects are created, and a Tag that is used for tagging and naming assets and objects.
2. A `workRequirement` section that defines the properties of Work Requirements to be submitted to the YellowDog platform.
3. A `workerPool` section that defines the properties of Provisoned Worker Pools to be created using the YellowDog platform. 

There is a documented template TOML file provided in [config.toml.template](config.toml.template).

The configuration filename can be supplied in three different ways:

1. On the command line, using the `--config` or `-c` options, e.g.:<br>`yd-submit -c jobs/config_1.toml`
2. Using the `YD_CONF` environment variable, e.g.: <br>`export YD_CONF="jobs/config_1.toml"`
3. If neither of the above is supplied, the commands look for a `config.toml` file in the current directory

The options above are shown in order of precedence, i.e., a filename supplied on the command line supersedes one set in `YD_CONF`, which supersedes the default.

## Naming Restrictions

All names used within the YellowDog Platform must comply with the following restrictions:

- Names can only contain the following: lowercase letters, digits, hyphens and underscores (note that spaces are not permitted)
- Names must start with a letter
- Names must end with a letter or digit
- Name length must be <= 60 characters

These restrictions apply to Namespaces, Tags, Work Requirements, Task Groups, Tasks, Worker Pools, and Compute Requirements.

(The restrictions also apply to entities that are currently used indirectly by these scripts: Usernames, Credentials, Keyrings, Compute Sources and Compute Templates).

## Common Properties

The `[common]` section of the configuration file contains the following properties:

| Property    | Description                                                                         |
|:------------|:------------------------------------------------------------------------------------|
| `key`       | The **key** of the YellowDog Application under which the commands will run          |
| `secret`    | The **secret** of the YellowDog Application under which the commands will run       |
| `namespace` | The **namespace** to be used to manage resources                                    |
| `tag`       | The **tag** to be used for tagging resources and naming objects                     |
| `url`       | The **URL** of the YellowDog Platform API endpoint, if the default isn't to be used |

An example `common` section is shown below:

```toml
[common]
    key = "asdfghjklzxcvb-1234567"
    secret = "qwertyuiopasdfghjklzxcvbnm1234567890qwertyu"
    namespace = "project-x"
    tag = "testing-{{username}}"
    url = "https://portal.yellowdog.co/api"
```

The indentation is optional in TOML files and is for readability only.

### Mustache Template Directives in Common Properties

Note the use of `{{username}}` in the value of the `tag` property: this is a **Mustache** template directive that can optionally be used to insert the login username of the user running the commands. So, for username `abc`, the `tag` would be set to `testing-abc`. This can be helpful to disambiguate multiple users running with the same configuration data.

Mustache directives can be used within the `namespace` and `tag` values in the `common` section (or when supplied as command line options or environment variables).

#### Default Mustache Directives

| Directive      | Description                                                    | Example of Substitution |
|:---------------|:---------------------------------------------------------------|:------------------------|
| `{{username}}` | The current user's login username, lower case, spaces replaced | jane_smith              |
| `{{date}}`     | The current date (UTC): YYYYMMDD                               | 20221027                |
| `{{time}}`     | The current time (UTC): HHMMSS                                 | 163026                  |
| `{{datetime}}` | Concatenation of the date and time above, with a '-' separator | 20221027-163026         |
| `{{random}}`   | A random, three digit hexadecimal number (lower case)          | a1c                     |

For the `date`, `time` and `random` directives, the same values will be used for the duration of a command -- i.e., if `{{time}}` is used within multiple properties, the same value will be used for each substitution.

#### User-Defined Mustache Directives

Additional (static) Mustache directives can be supplied using command line options or by setting environment variables prefixed with `YD_SUB_`.

The **command line** option is `--mustache-substitution` (or `-m`). For example, `yd-submit -m project_code=pr-213-a -m run_id=1234` will establish two new Mustache directives `{{project_code}}` and `{{run_id}}`, which will be substituted by `pr-213-a` and `1234` respectively.

For **environment variables**, setting the variable `YD_SUB_project_code="pr-213-a"` will create a new Mustache directive `{{project_code}}`, which will be substituted by `pr-213-a`.

Directives set on the command line take precedence over directives set in environment variables.

This method can be used to override the default directives, e.g., setting `-m username="other-user"` will override the default `{{username}}` directive.

### Specifying Common Properties using the Command Line or Environment Variables

All the common properties can be set using command line options, or in environment variables.

The **command line options** are as follows:

- `--key` or `-k`
- `--secret` or `-s`
- `--namespace` or `-n`
- `--tag` or `-t`
- `--url` or `-u`

These options can also be listed by running a command with the `--help` or `-h` option.

The **environment variables** are as follows:

- `YD_KEY`
- `YD_SECRET`
- `YD_NAMESPACE`
- `YD_TAG`
- `YD_URL`

When setting the value of the above properties, a property set on the command line takes precedence over one set via an environment variable, and both take precedence over a value set in a configuration file.

If all the required common properties are set using the command line or environment variables, then the entire `common` section of the TOML file can be omitted.

## Work Requirement Properties

The `workRequirement` section of the configuration file is optional. It's used only by the `yd-submit` command, and controls the Work Requirement that is submitted to the Platform.

The details of a Work Requirement to be submitted can be captured entirely within the TOML configuration file for simple examples. More complex examples capture the Work Requirement in a combination of the TOML file plus a JSON document, or in a JSON document only.

### Work Requirement JSON File Structure

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

To specify the file containing the JSON document, either populate the `workRequirementData` property in the `workRequirement` section of the TOML configuration file with the JSON filename, or specify it on the command line using the `--work-requirement` or `-r` options (which will override any value set in the TOML file), e.g.

`yd-submit --config myconfig.toml --work-requirement my_workreq.json`

### Property Inheritance

To simplify and optimise the definition of Work Requirements, there is a property inheritance mechanism. Properties that are set at a higher level in the hierarchy are inherited at lower levels, unless explicitly overridden.

This means that a property set in the `workRequirement` section of the TOML file can be inherited successively by the Work Requirement, Task Groups and Tasks in the JSON document (assuming the property is valid at each level).  Hence, Tasks inherit from Task Groups, which inherit from the Work Requirement in the JSON document, which inherits from the `workRequirement` properties in the TOML file.

Overridden properties are also inherited. E.g., if a property is set at the Task Group level, it will be inherited by the Tasks in that Task Group unless explicitly overridden.

### Work Requirement Property Dictionary

The following table outlines all the properties available for defining Work Requirements, and the levels at which they are allowed to be used. So, for example, the `provider` property can be set in the TOML file, at the Work Requirement Level or at the Task Group Level, but not at the Task level, and property `dependentOn` can only be set at the Task Group level.

All properties are optional except for **`taskType`** (or **`TaskTypes`**).

| Property Name         | Description                                                                                                                                                              | TOML | WR  | Task Grp | Task |
|:----------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----|:----|:---------|:-----|
| `arguments`           | The list of arguments to be passed to the Task when it is executed. E.g.: `[1, "Two"]`.                                                                                  | Yes  | Yes | Yes      | Yes  |
| `autoFail`            | If true, the Task Group will be failed automatically if any contained tasks fail. Default:`true`.                                                                        | Yes  | Yes | Yes      |      |
| `captureTaskOutput`   | Whether the console output of a Task's process should be uploaded to the YellowDog Object Store on Task completion. Default: `true`.                                     | Yes  | Yes | Yes      | Yes  |
| `completedTaskTtl`    | The time (in minutes) to live for completed Tasks. If set, Tasks that have been completed for longer than this period will be deleted. E.g.: `10.0`.                     | Yes  | Yes | Yes      |      |
| `dependentOn`         | The name of another Task Group within the same Work Requirement that must be successfully completed before the Task Group is started. E.g. `"TG_1"`.                     |      |     | Yes      |      |
| `dockerEnvironment`   | The environment to be passed in to a Docker container. E.g., JSON: `{"VAR_1": "abc", "VAR_2": "def"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                           | Yes  | Yes | Yes      | Yes  |
| `dockerPassword`      | The password for DockerHub, used by the `docker` Task Type. E,g., `"my_password"`.                                                                                       | Yes  | Yes | Yes      | Yes  |
| `dockerUsername`      | The username for DockerHub, used by the `docker` Task Type. E,g., `"my_username"`.                                                                                       | Yes  | Yes | Yes      | Yes  |
| `environment`         | The environment variables to set for a Task when it's executed. E.g., JSON: `{"VAR_1": "abc", "VAR_2": "def"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                  | Yes  | Yes | Yes      | Yes  |
| `exclusiveWorkers`    | If true, then do not allow claimed Workers to be shared with other Task Groups; otherwise, Workers can be shared. Default:`false`.                                       | Yes  | Yes | Yes      |      |
| `executable`          | The executable to run when a bash or Docker Task is executed. For the `bash` Task Type, this is the name of the Bash script. For `docker`, the name of the container.    | Yes  | Yes | Yes      | Yes  |
| `flattenInputPaths`   | Determines whether input object paths should be flattened (i.e., directory structure removed) when downloaded to a node. Default: `false`.                               | Yes  | Yes | Yes      | Yes  |
| `fulfilOnSubmit`      | Indicates if the Work Requirement should be fulfilled when it is submitted, rather than being allowed to wait in PENDING status. Default:`false`.                        | Yes  | Yes |          |      |
| `inputs`              | The list of input files to be uploaded to the YellowDog Object Store, and downloaded to the node on which a Task will execute. E.g. `["a.sh", "b.sh"]`.                  | Yes  | Yes | Yes      | Yes  |
| `instanceTypes`       | The machine instance types that can be used to execute Tasks. E.g., `["t3.micro", "t3a.micro"]`.                                                                         | Yes  | Yes | Yes      |      |
| `intermediateInputs`  | A list of output files from the execution of a previous Task to be downloaded for use by the current Task. E.g.: `["Task_Group_1/Task_1/results.txt"]`.                  |      |     | Yes      | Yes  |
| `maximumTaskRetries`  | The maximum number of times a Task can be retried after it has failed. E.g.: `5`.                                                                                        | Yes  | Yes | Yes      | Yes  |
| `maxWorkers`          | The maximum number of Workers that can be claimed for the associated Task Group. E.g., `10`.                                                                             | Yes  | Yes | Yes      |      |
| `minWorkers`          | The minimum number of Workers that the associated Task Group requires. This many workers must be claimed before the associated Task Group will start working. E.g., `1`. | Yes  | Yes | Yes      |      |
| `name`                | The name of the Work Requirement, Task Group or Task. E.g., `"wr_name"`. Note that the `name` property is not inherited.                                                 | Yes  | Yes | Yes      | Yes  |
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

### Automatic Properties

In addition to the inheritance mechanism, some properties are set automatically by the `yd-submit` command, as a usage convenience.

#### Work Requirement, Task Group and Task Naming

- The **Work Requirement** name is automatically set using a concatenation of the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `mytag_221024-155524-40a`.
- **Task Group** names are automatically created for any Task Group that is not explicitly named, using names of the form `task_group_1` (or `task_group_01`, etc., for larger numbers of Task Groups).
- **Task** names are automatically created for any Task that is not explicitly named, using names of the form `task_1` (or `task_01`, etc., for larger numbers of Tasks). The Task counter resets for each different Task Group.

#### Task Types

- If `taskType` is set only at the TOML file level, then `taskTypes` is automatically populated for Task Groups, unless overridden.
- If `taskType` is set at the Task level, then `taskTypes` is automatically populated for Task Groups level using the accumulated Task Types from the Tasks, unless overridden.
- If `taskTypes` is set at the Task Group Level, and has only one Task Type entry, then `taskType` is automatically set at the Task Level using the single Task Type, unless overridden.

### Examples

#### TOML Properties in the `workRequirement` Section

Here's an example of the `workRequirement` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workRequirement]
    arguments = [1, "TWO"]
    autoFail = false
    captureTaskOutput = true
    completedTaskTtl = 10
    dockerEnvironment = {MY_DOCKER_VAR = 100}
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
    name = "my-work-requirement"
    outputs = ["results.txt"]
    priority = 0.0
    providers = ["AWS"]
    ram = [0.5, 2.0]
    regions = ["eu-west-2"]
    taskCount = 100
    taskType = "docker"
    tasksPerWorker = 1
    vcpus = [1, 4]
    workerTags = ["tag-{{username}}"]
#   workRequirementData = "work_requirement.json"
```

#### JSON Properties at the Work Requirement Level

Showing all possible properties at the Work Requirement level:

```json
{
  "arguments": [1, "TWO"],
  "autoFail": false,
  "captureTaskOutput": true,
  "completedTaskTtl": 10,
  "dockerEnvironment": {"MY_DOCKER_VAR": 100},
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
  "name": "my-work-requirement",
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

#### JSON Properties at the Task Group Level

Showing all possible properties at the Task Group level:

```json
{
  "taskGroups": [
    {
      "arguments": [1, "TWO"],
      "autoFail": false,
      "captureTaskOutput": true,
      "completedTaskTtl": 10,
      "dockerEnvironment": {"MY_DOCKER_VAR": 100},
      "dockerPassword": "myPassword",
      "dockerUsername": "myUsername",
      "environment": {"MY_VAR": 100},
      "exclusiveWorkers": false,
      "executable": "my-container",
      "inputs": ["app/main.py", "app/requirements.txt"],
      "instanceTypes": ["t3a.micro", "t3.micro"],
      "intermediateInputs": [],
      "maximumTaskRetries": 0,
      "maxWorkers": 1,
      "minWorkers": 1,
      "name": "first-task-group",
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
      "name": "second-task-group",
      "dependentOn": "first-task-group",
      "tasks": [
        {}
      ]
    }
  ]
}
```

#### JSON Properties at the Task Level

Showing all possible properties at the Task level:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": [],
          "captureTaskOutput": true,
          "dockerEnvironment": {"MY_DOCKER_VAR": 100},
          "dockerPassword": "myPassword",
          "dockerUsername": "myUsername",
          "environment": {"MY_VAR": 100},
          "executable": "my-container",
          "inputs": ["app/main.py", "app/requirements.txt"],
          "intermediateInputs": [],
          "name": "my-task",
          "outputs": ["results.txt"],
          "taskType": "docker"
        }
      ]
    }
  ]
}
```

### Mustache Template Directives in Work Requirement Properties

Mustache template directives can be used within any property value in TOML configuration files or Work Requirement JSON files. See the description [above](#mustache-template-directives-in-common-properties) for more details on Mustache directives. This is a powerful feature that allows Work Requirements to be parameterised by supplying values on the command line.

To suppress all Mustache processing within a Work Requirement JSON file, `yd-submit` can be run with the `--no-mustache` option. All mustache directives will be ignored, i.e., the {{foobar}} form will remain in the Work Requirement.

## Worker Pool Properties

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

### Automatic Properties

The name of the Worker Pool, if not supplied, is automatically generated using a concatenation of `WP_`, the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `wp_mytag_221024T155524-b0a`.

### Worker Pool JSON File Structure

**Experimental Feature**

It's also possible to capture a Worker Pool definition as a JSON document. The JSON filename can be supplied either using the command line with the `--worker-pool` or `-p` parameter with `yd-provision`, or by populating the `workerPoolData` property in the TOML configuration file with the JSON filename. Command line specification takes priority over TOML specification. The JSON specification allows the creation of **Advanced Worker Pools**, with different node types and the ability to specify Node Actions.

When using a JSON document to specify the Worker Pool, the schema of the document is identical to that expected by the YellowDog API for Worker Provisioning.

Examples will be provided at a later date.

### Examples

#### TOML Properties in the `workerPool` Section

Here's an example of the `workerPool` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workerPool]
    autoShutdown = true
    autoShutdownDelay = 10
    autoscalingIdleDelay = 3
    maxNodes = 1
    minNodes = 1
    name = "my-worker-pool"
    nodeBootTimeLimit = 5
    targetInstanceCount = 1
    templateId = "ydid:crt:000000:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    workerTag = "tag-{{username}}"
    workersPerNode = 1
#   workerPoolData = "worker_pool.json"
```

# Command List

Help is available for all commands by invoking a command with the `--help` or `-h` option. Some command line parameters are common to all commands, while others are command-specific.

All destructive commands require user confirmation before taking effect. This can be suppressed using the `--yes` or `-y` option, in which case the command will proceed without confirmation.

Some commands support the `--interactive` or `-i` option, allowing user selections to be made. E.g., this can be used to select which object paths to delete.

The `--quiet` or `-q` option reduces the command output down to essential messages only. So, for example, `yd-delete -yq` would delete all matching object paths silently.

If you encounter an error it can be useful for support purposes to see the full Python stack trace. This can be enabled by running the command using the `--stack-trace` option.

## yd-submit

The `yd-submit` command submits a new Work Requirement, according to the Work Requirement definition found in the `workRequirement` section of the TOML configuration file and/or the specification found in a Work Requirement JSON document supplied using the `--work-requirement` option.

Once submitted, the Work Requirement will appear in the **Work** tab in the YellowDog Portal.

The Work Requirement's progress can be tracked to completion by using the `--follow` (or `-f`) option when invoking `yd-submit`: the command will report on Tasks as they conclude and won't return until the Work Requirement has finished.

## yd-provision

The `yd-provision` command provisions a new Worker Pool according to the specifications in the `workerPool` section of the TOML configuration file and/or in the specification found in a Worker Pool JSON document supplied using the `--worker-pool` option.

Once provisioned, the Worker Pool will appear in the **Workers** tab in the YellowDog Portal, and its associated Compute Requirement will appear in the **Compute** tab.

## yd-cancel

The `yd-cancel` command cancels any active Work Requirements, including any pending Task Groups and the Tasks they contain. 

The `namespace` and `tag` values in the `config.toml` file are used to identify which Work Requirements to cancel.

By default, any Tasks that are currently running on Workers will continue to run to completion or until they fail. Tasks can be instructed to abort immediately by supplying the `--abort` or `-a` option to `yd-cancel`.

## yd-abort

The `yd-abort` command is used to abort Tasks that are currently running. The user interactively selects the Work Requirements to target, and then which Tasks within those Work Requirements to abort. The Work Requirements are not cancelled as part of this process.

The `namespace` and `tag` values in the `config.toml` file are used to identify which Work Requirements to list for selection.

## yd-download

The `yd-download` command downloads any objects created in the YellowDog Object Store.

The `namespace` and `tag` values are used to determine which objects to download. Objects will be downloaded to a directory with the same name as `namespace`. If a directory already exists, a new directory with name `<namespace>.01` (etc.) will be created.

## yd-delete

The `yd-delete` command deletes any objects created in the YellowDog Object Store.

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete.

## yd-shutdown

The `yd-shutdown` command shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

## yd-terminate

The `yd-terminate` command immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.
