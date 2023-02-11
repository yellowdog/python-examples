# YellowDog Python Example Scripts

<!--ts-->
* [YellowDog Python Example Scripts](#yellowdog-python-example-scripts)
* [Overview](#overview)
* [YellowDog Prerequisites](#yellowdog-prerequisites)
* [Script Installation with Pip](#script-installation-with-pip)
* [Script Installation with Pipx](#script-installation-with-pipx)
* [Usage](#usage)
* [Configuration](#configuration)
* [Naming Rules](#naming-rules)
* [Common Properties](#common-properties)
   * [Specifying Common Properties using the Command Line or Environment Variables](#specifying-common-properties-using-the-command-line-or-environment-variables)
   * [Mustache Template Directives in Common Properties](#mustache-template-directives-in-common-properties)
* [Mustache Template Directives](#mustache-template-directives)
   * [Default Mustache Directives](#default-mustache-directives)
   * [User-Defined Mustache Directives](#user-defined-mustache-directives)
* [Work Requirement Properties](#work-requirement-properties)
   * [Work Requirement JSON File Structure](#work-requirement-json-file-structure)
   * [Property Inheritance](#property-inheritance)
   * [Work Requirement Property Dictionary](#work-requirement-property-dictionary)
   * [Automatic Properties](#automatic-properties)
      * [Work Requirement, Task Group and Task Naming](#work-requirement-task-group-and-task-naming)
      * [Task Types](#task-types)
         * [Bash Tasks](#bash-tasks)
         * [Docker Tasks](#docker-tasks)
         * [Bash &amp; Docker without Automatic Processing](#bash--docker-without-automatic-processing)
      * [Task Counts](#task-counts)
   * [Examples](#examples)
      * [TOML Properties in the workRequirement Section](#toml-properties-in-the-workrequirement-section)
      * [JSON Properties at the Work Requirement Level](#json-properties-at-the-work-requirement-level)
      * [JSON Properties at the Task Group Level](#json-properties-at-the-task-group-level)
      * [JSON Properties at the Task Level](#json-properties-at-the-task-level)
   * [Mustache Directives in Work Requirement Properties](#mustache-directives-in-work-requirement-properties)
      * [Task and Task Group Naming](#task-and-task-group-naming)
   * [Dry-Running Work Requirement Submissions](#dry-running-work-requirement-submissions)
      * [Submitting 'Raw' JSON Work Requirement Specifications](#submitting-raw-json-work-requirement-specifications)
   * [File Storage Locations and File Usage](#file-storage-locations-and-file-usage)
      * [Files Uploaded to the Object Store from Local Storage](#files-uploaded-to-the-object-store-from-local-storage)
         * [Files in the inputs List](#files-in-the-inputs-list)
         * [Files in the uploadFiles List](#files-in-the-uploadfiles-list)
      * [File Dependencies Using verifyAtStart and verifyWait](#file-dependencies-using-verifyatstart-and-verifywait)
      * [Files Downloaded to a Node for use in Task Execution](#files-downloaded-to-a-node-for-use-in-task-execution)
      * [Files Uploaded from a Node to the Object Store after Task Execution](#files-uploaded-from-a-node-to-the-object-store-after-task-execution)
      * [Files Downloaded from the Object Store to Local Storage](#files-downloaded-from-the-object-store-to-local-storage)
   * [Specifying Work Requirements using CSV Data](#specifying-work-requirements-using-csv-data)
      * [Work Requirement CSV Data Example](#work-requirement-csv-data-example)
      * [CSV Mustache Substitutions](#csv-mustache-substitutions)
      * [Property Inheritance](#property-inheritance-1)
      * [Multiple Task Groups using Multiple CSV Files](#multiple-task-groups-using-multiple-csv-files)
      * [Using CSV Data with Simple, TOML-Only Work Requirement Specifications](#using-csv-data-with-simple-toml-only-work-requirement-specifications)
      * [Inspecting the Output of CSV Variable Substitution](#inspecting-the-output-of-csv-variable-substitution)
* [Worker Pool Properties](#worker-pool-properties)
   * [Automatic Properties](#automatic-properties-1)
   * [TOML Properties in the workerPool Section](#toml-properties-in-the-workerpool-section)
   * [Worker Pool Specification Using JSON Documents](#worker-pool-specification-using-json-documents)
      * [Worker Pool JSON Examples](#worker-pool-json-examples)
      * [TOML Properties Inherited by Worker Pool JSON Specifications](#toml-properties-inherited-by-worker-pool-json-specifications)
   * [Mustache Directives in Worker Pool Properties](#mustache-directives-in-worker-pool-properties)
   * [Dry-Running Worker Pool Provisioning](#dry-running-worker-pool-provisioning)
* [Jsonnet Support](#jsonnet-support)
   * [Jsonnet Installation](#jsonnet-installation)
   * [Mustache Substitutions in Jsonnet Files](#mustache-substitutions-in-jsonnet-files)
   * [Checking Jsonnet Processing](#checking-jsonnet-processing)
   * [Jsonnet Example](#jsonnet-example)
* [Command List](#command-list)
   * [yd-submit](#yd-submit)
   * [yd-provision](#yd-provision)
   * [yd-cancel](#yd-cancel)
   * [yd-abort](#yd-abort)
   * [yd-download](#yd-download)
   * [yd-delete](#yd-delete)
   * [yd-upload](#yd-upload)
   * [yd-shutdown](#yd-shutdown)
   * [yd-instantiate](#yd-instantiate)
   * [yd-terminate](#yd-terminate)

<!-- Added by: pwt, at: Sun Feb  5 11:34:08 GMT 2023 -->

<!--te-->

# Overview

This repository contains a set of example Python scripts for interacting with the YellowDog Platform. The scripts use the **[YellowDog Python SDK](https://docs.yellowdog.co/api/python/index.html)**, the code for which can be found [on GitHub](https://github.com/yellowdog/yellowdog-sdk-python-public).

This documentation should be read in conjunction with the main **[YellowDog Documentation](https://docs.yellowdog.co)**, which provides a comprehensive description of the concepts and operation of the YellowDog Platform.

The scripts are intended to be helpful starting points for experimenting with the YellowDog Platform. They are not assured to be of production quality nor to represent a standard or recommended method for using YellowDog.

The scripts provide commands for:

- **Provisioning** Worker Pools
- **Submitting** Work Requirements
- **Uploading** files to the YellowDog Object Store
- **Instantiating** Compute Requirements
- **Downloading** Results from the YellowDog Object Store
- **Shutting Down** Worker Pools and **Terminating** Compute Requirements
- **Cancelling** Work Requirements
- **Aborting** running Tasks
- **Deleting** objects in the YellowDog Object Store

The operation of the commands is controlled using TOML configuration files. In addition, Work Requirements and Worker Pools can be defined using JSON files providing extensive configurability.

# YellowDog Prerequisites

To submit **Work Requirements** to YellowDog for processing by Configured Worker Pools (on-premise) and/or Provisioned Worker Pools (cloud-provisioned resources), you'll need:

1. A YellowDog Platform Account.


2. An Application Key & Secret: in the **Accounts** section under the **Applications** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be displayed once).


To create **Provisioned Worker Pools**, you'll need:

3. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required. The Application must be granted access to the Keyring.


4. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) to match the Work Requirements to be submitted.

To set up **Configured Worker Pools**, you'll need:

5. A Configured Worker Pool Token: from the **Workers** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/workers), use the **+Add Configured Worker Pool** button to create a new Worker Pool and generate a token.


6. Obtain the YellowDog Agent and install/configure it on your on-premise systems using the Token above.

# Script Installation with Pip

Python version 3.7 or later is required. It's recommended that installation is performed in a Python virtual environment (or similar) to isolate the installation from other Python environments on your system.

Installation and subsequent update are via `pip` and PyPI using: 

```shell
pip install -U yellowdog-python-examples
```

If you're interested in including **Jsonnet** support, please see the [Jsonnet Support](#jsonnet-support) section below.

# Script Installation with Pipx

The commands can also be installed using **[pipx](https://pypa.github.io/pipx/)**.

This method requires Python 3.7+ and pipx to be installed. To install:
```shell
pipx install yellowdog-python-examples
```

To update:
```shell
pipx upgrade yellowdog-python-examples
```

# Usage

Both of the installation methods above will install a number of **`yd-`** commands on your PATH.

Commands are run from the command line. Invoking the command with the `--help` or `-h` option will display the command line options applicable to a given command, e.g.:

```text
% yd-cancel --help
usage: yd-cancel [-h] [--config <config_file.toml>] [--key <app-key>] [--secret <app-secret>]
                 [--namespace <namespace>] [--tag <tag>]
                 [--url <url>] [--mustache <var1=v1>] [--quiet] [--abort] [--interactive] [--yes] [--debug]

YellowDog example utility for cancelling Work Requirements

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
  --mustache <var1=v1>, -m <var1=v1>
                        user-defined Mustache substitution; can be supplied multiple times
  --quiet, -q           suppress (non-error, non-interactive) status and progress messages
  --abort, -a           abort all running tasks with immediate effect
  --interactive, -i     list, and interactively select, items to act on
  --yes, -y             perform destructive actions without requiring user confirmation
  --debug               print a stack trace (etc.) on error
```

# Configuration

By default, the operation of all commands is configured using a TOML configuration file.

The configuration file has three possible sections:

1. A `common` section that contains required security properties for interacting with the YellowDog platform, sets the Namespace in which YellowDog assets and objects are created, and a Tag that is used for tagging and naming assets and objects.
2. A `workRequirement` section that defines the properties of Work Requirements to be submitted to the YellowDog platform.
3. A `workerPool` section that defines the properties of Provisoned Worker Pools to be created using the YellowDog platform. 

There is a documented template TOML file provided in [config.toml.template](config.toml.template), containing the main properties that can be configured.

The configuration filename can be supplied in three different ways:

1. On the command line, using the `--config` or `-c` options, e.g.:<br>`yd-submit -c jobs/config_1.toml`
2. Using the `YD_CONF` environment variable, e.g.: <br>`export YD_CONF="jobs/config_1.toml"`
3. If neither of the above is supplied, the commands look for a `config.toml` file in the current directory

The options above are shown in order of precedence, i.e., a filename supplied on the command line supersedes one set in `YD_CONF`, which supersedes the default.

# Naming Rules

All entity names used within the YellowDog Platform must comply with the following restrictions:

- Names can only contain the following: lowercase letters, digits, hyphens and underscores (note that spaces are not permitted)
- Names must start with a letter
- Names must end with a letter or digit
- Name length must be <= 60 characters

These restrictions apply to entities including Namespaces, Tags, Work Requirements, Task Groups, Tasks, Worker Pools, and Compute Requirements, and also apply to entities that are currently used indirectly by these scripts, including Usernames, Credentials, Keyrings, Compute Sources and Compute Templates.

# Common Properties

The `[common]` section of the configuration file can contain the following properties:

| Property    | Description                                                                         |
|:------------|:------------------------------------------------------------------------------------|
| `key`       | The **key** of the YellowDog Application under which the commands will run          |
| `secret`    | The **secret** of the YellowDog Application under which the commands will run       |
| `namespace` | The **namespace** to be used to manage resources                                    |
| `tag`       | The **tag** to be used for tagging resources and naming objects                     |
| `url`       | The **URL** of the YellowDog Platform API endpoint, if the default isn't to be used |
| `mustache`  | A dictionary containing **Mustache substitutions** (see the Mustache section below) |

An example `common` section is shown below:

```toml
[common]
    key = "asdfghjklzxcvb-1234567"
    secret = "qwertyuiopasdfghjklzxcvbnm1234567890qwertyu"
    namespace = "project-x"
    tag = "testing-{{username}}"
```

The indentation is optional in TOML files and is for readability only.

## Specifying Common Properties using the Command Line or Environment Variables

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

## Mustache Template Directives in Common Properties

Note the use of `{{username}}` in the value of the `tag` property: this is a **Mustache** template directive that can optionally be used to insert the login username of the user running the commands. So, for username `abc`, the `tag` would be set to `testing-abc`. This can be helpful to disambiguate multiple users running with the same configuration data.

Mustache substitutions are discussed below.

# Mustache Template Directives

Mustache template substitutions provide a powerful way of introducing variable values into TOML configuration files, Work Requirement JSON definitions, and Worker Pool JSON definitions. They can be included in the value of any property in each of these objects, including in values within lists (e.g., for the `arguments` property) and arrays (e.g., the `environment` property).

Mustache substitutions are expressed using `{{variable}}` notation, where the expression is replaced by the value of `variable`.

Substitutions can also be performed for non-string (number and boolean) values using the `num:` and `bool:` prefixes within the Mustache directive:

- Define the Mustache directive using one of the following patterns: `"{{num:my_int}}"`, `"{{num:my_float}}"`, `"{{bool:my_bool}}"`
- Variable definitions supplied on the command line would then be of the form: `-m my_int=5 -m my_float=2.5 -m my_bool=true`
- In the processed JSON or TOML, these values would become `5`, `2.5` and `true`, respectively, converted from strings to their correct JSON types

## Default Mustache Directives

The following substitutions are automatically provided:

| Directive      | Description                                                    | Example of Substitution |
|:---------------|:---------------------------------------------------------------|:------------------------|
| `{{username}}` | The current user's login username, lower case, spaces replaced | jane_smith              |
| `{{date}}`     | The current date (UTC): YYYYMMDD                               | 20221027                |
| `{{time}}`     | The current time (UTC): HHMMSS                                 | 163026                  |
| `{{datetime}}` | Concatenation of the date and time above, with a '-' separator | 20221027-163026         |
| `{{random}}`   | A random, three digit hexadecimal number (lower case)          | a1c                     |

For the `date`, `time`, `datetime` and `random` directives, the same values will be used for the duration of a command -- i.e., if `{{time}}` is used within multiple properties, the same value will be used for each substitution.

## User-Defined Mustache Directives

Arbitrary Mustache directives can be supplied using command line options, by setting environment variables prefixed with `YD_SUB_`, or by including the directives in the `[common]` section of the TOML configuration file.

1. The **command line** option is `--mustache-substitution` (or `-m`). For example, `yd-submit -m project_code=pr-213-a -m run_id=1234` will establish two new Mustache directives `{{project_code}}` and `{{run_id}}`, which will be substituted by `pr-213-a` and `1234` respectively.


2. For **environment variables**, setting the variable `YD_SUB_project_code="pr-213-a"` will create a new Mustache directive `{{project_code}}`, which will be substituted by `pr-213-a`.


3. For **setting within the TOML file**, include a **`mustache`** table in the `[common]` section of the file. E.g., `mustache = {project_code = "pr-213a", run_id = "1234"}`.

Directives set on the command line take precedence over directives set in environment variables, and both of them take precedence over directives set in a TOML file.

This method can be used to override the default directives, e.g., setting `-m username="other-user"` will override the default `{{username}}` directive.

# Work Requirement Properties

The `workRequirement` section of the configuration file is optional. It's used only by the `yd-submit` command, and controls the Work Requirement that is submitted to the Platform.

The details of a Work Requirement to be submitted can be captured entirely within the TOML configuration file for simple examples. More complex examples capture the Work Requirement in a combination of the TOML file plus a JSON document, or in a JSON document only.

## Work Requirement JSON File Structure

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

## Property Inheritance

To simplify and streamline the definition of Work Requirements, there is a property inheritance mechanism. Properties that are set at a higher level in the hierarchy are inherited at lower levels, unless explicitly overridden.

This means that a property set in the `workRequirement` section of the TOML file can be inherited successively by the Work Requirement, Task Groups and Tasks in the JSON document (assuming the property is valid at each level).  Hence, Tasks inherit from Task Groups, which inherit from the Work Requirement in the JSON document, which inherits from the `workRequirement` properties in the TOML file.

Overridden properties are also inherited. E.g., if a property is set at the Task Group level, it will be inherited by the Tasks in that Task Group unless explicitly overridden.

## Work Requirement Property Dictionary

The following table outlines all the properties available for defining Work Requirements, and the levels at which they are allowed to be used. So, for example, the `provider` property can be set in the TOML file, at the Work Requirement Level or at the Task Group Level, but not at the Task level, and property `dependentOn` can only be set at the Task Group level.

All properties are optional except for **`taskType`** (or **`taskTypes`**).

| Property Name              | Description                                                                                                                                                              | TOML | WR  | TGrp | Task |
|:---------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----|:----|:-----|:-----|
| `arguments`                | The list of arguments to be passed to the Task when it is executed. E.g.: `[1, "Two"]`.                                                                                  | Yes  | Yes | Yes  | Yes  |
| `captureTaskOutput`        | Whether the console output of a Task's process should be uploaded to the YellowDog Object Store on Task completion. Default: `true`.                                     | Yes  | Yes | Yes  | Yes  |
| `completedTaskTtl`         | The time (in minutes) to live for completed Tasks. If set, Tasks that have been completed for longer than this period will be deleted. E.g.: `10.0`.                     | Yes  | Yes | Yes  |      |
| `csvFile`                  | The name of the CSV file used to derive Task data. An alternative to `csvFiles` that can be used when there's only a single CSV file. E.g. `"file.csv".                  | Yes  |     |      |      |
| `csvFiles`                 | A list of CSV files used to derive Task data. E.g. `["file.csv", "file_2.csv:2]`.                                                                                        | Yes  |     |      |      |
| `dependentOn`              | The name of another Task Group within the same Work Requirement that must be successfully completed before the Task Group is started. E.g. `"task_group_1"`.             |      |     | Yes  |      |
| `dockerEnvironment`        | The environment to be passed to a Docker container. Only used by the `docker` Task Type. E.g., JSON: `{"VAR_1": "abc"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.         | Yes  | Yes | Yes  | Yes  |
| `dockerPassword`           | The password for DockerHub, only used by the `docker` Task Type. E,g., `"my_password"`.                                                                                  | Yes  | Yes | Yes  | Yes  |
| `dockerUsername`           | The username for DockerHub, only used by the `docker` Task Type. E,g., `"my_username"`.                                                                                  | Yes  | Yes | Yes  | Yes  |
| `environment`              | The environment variables to set for a Task when it's executed. E.g., JSON: `{"VAR_1": "abc", "VAR_2": "def"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                  | Yes  | Yes | Yes  | Yes  |
| `exclusiveWorkers`         | If true, then do not allow claimed Workers to be shared with other Task Groups; otherwise, Workers can be shared. Default:`false`.                                       | Yes  | Yes | Yes  |      |
| `executable`               | The 'executable' to run when a Bash or Docker Task is executed. Bash script for Bash, container image for Docker. Optional: omit to suppress automatic processing.       | Yes  | Yes | Yes  | Yes  |
| `finishIfAllTasksFinished` | If true, the Task Group will finish automatically if all contained tasks finish. Default:`true`.                                                                         | Yes  | Yes | Yes  |      |
| `finishIfAnyTaskFailed`    | If true, the Task Group will be failed automatically if any contained tasks fail. Default:`false`.                                                                       | Yes  | Yes | Yes  |      |
| `flattenInputPaths`        | Determines whether input object paths should be flattened (i.e., directory structure removed) when downloaded to a node. Default: `false`.                               | Yes  | Yes | Yes  | Yes  |
| `flattenUploadPaths`       | Ignore local directory paths when uploading files to the Object Store; place in `<namespace>:<work-req-name>/`. Default: `false`.                                        | Yes  | Yes |      |      |
| `fulfilOnSubmit`           | Indicates if the Work Requirement should be fulfilled when it is submitted, rather than being allowed to wait in PENDING status. Default:`false`.                        | Yes  | Yes |      |      |
| `inputs`                   | The list of input files to be uploaded to the YellowDog Object Store, and required by the Task (implies `verifyAtStart`). E.g. `["a.sh", "b.sh"]`.                       | Yes  | Yes | Yes  | Yes  |
| `instanceTypes`            | The machine instance types that can be used to execute Tasks. E.g., `["t3.micro", "t3a.micro"]`.                                                                         | Yes  | Yes | Yes  |      |
| `maximumTaskRetries`       | The maximum number of times a Task can be retried after it has failed. E.g.: `5`.                                                                                        | Yes  | Yes | Yes  |      |
| `maxWorkers`               | The maximum number of Workers that can be claimed for the associated Task Group. E.g., `10`.                                                                             | Yes  | Yes | Yes  |      |
| `minWorkers`               | The minimum number of Workers that the associated Task Group requires. This many workers must be claimed before the associated Task Group will start working. E.g., `1`. | Yes  | Yes | Yes  |      |
| `name`                     | The name of the Work Requirement, Task Group or Task. E.g., `"wr_name"`. Note that the `name` property is not inherited.                                                 | Yes  | Yes | Yes  | Yes  |
| `outputs`                  | The files to be uploaded to the YellowDog Object Store by a Worker node on completion of the Task. E.g., `["results_1.txt", "results_2.txt"]`.                           | Yes  | Yes | Yes  | Yes  |
| `priority`                 | The priority of Work Requirements and Task Groups. Higher priority acquires Workers ahead of lower priority. E.g., `0.0`.                                                | Yes  | Yes | Yes  |      |
| `providers`                | Constrains the YellowDog Scheduler only to execute tasks from the associated Task Group on the specified providers. E.g., `["AWS", "GOOGLE"]`.                           | Yes  | Yes | Yes  |      |
| `ram`                      | Range constraint on GB of RAM that are required to execute Tasks. E.g., `[2.5, 4.0]`.                                                                                    | Yes  | Yes | Yes  |      |
| `regions`                  | Constrains the YellowDog Scheduler only to execute Tasks from the associated Task Group in the specified regions. E.g., `["eu-west-2]`.                                  | Yes  | Yes | Yes  |      |
| `taskBatchSize`            | Determines the batch size used to add Tasks to Task Groups. Default is 2,000.                                                                                            | Yes  |     |      |      |
| `taskCount`                | The number of times to execute the Task. Can be set in the TOML file or in any JSON Work Requirement or Task Group definition. Note: no inheritance from TOML to JSON.   | Yes  | Yes | Yes  |      |
| `taskData`                 | The data to be passed to the Worker when the Task is started. E.g., `"mydata"`. Becomes file `taskdata.txt` in the Task's working directory when The Task executes.      | Yes  | Yes | Yes  | Yes  |
| `taskDataFile`             | Populate the `taskData` property above with the contents of the specified file. E.g., `"my_task_data_file.txt"`.                                                         | Yes  | Yes | Yes  | Yes  |
| `taskName`                 | The name to use for the Task. Only usable in the TOML file. Mostly useful in conjunction with CSV Task data. E.g., `"my_task_number_{{task_number}}"`.                   | Yes  |     |      |      |
| `taskGroupName`            | The name to use for the Task Group. Only usable in the TOML file. E.g., `"my_tg_number_{{task_group_number}}"`.                                                          | Yes  |     |      |      |
| `taskType`                 | The Task Type of a Task. E.g., `"docker"`.                                                                                                                               | Yes  |     |      | Yes  |
| `taskTypes`                | The list of Task Types required by the range of Tasks in a Task Group. E.g., `["docker", bash"]`.                                                                        |      | Yes | Yes  |      |
| `tasksPerWorker`           | Determines the number of Worker claims based on splitting the number of unfinished Tasks across Workers. E.g., `1`.                                                      | Yes  | Yes | Yes  |      |
| `uploadFiles`              | The list of files to be uploaded to the YellowDog Object Store. E.g., (JSON): `[{"localPath": file_1.txt", "uploadPath": "file_1.txt"}]`.                                | Yes  | Yes | Yes  | Yes  |
| `vcpus`                    | Range constraint on number of vCPUs that are required to execute Tasks E.g., `[2.0, 4.0]`.                                                                               | Yes  | Yes | Yes  |      |
| `verifyAtStart`            | A list of files required by a Task. Must be present when the Task is ready to start or the Task will fail. E.g.: `["task_group_1/task_1/results.txt"]`.                  | Yes  | Yes | Yes  | Yes  |
| `verifyWait`               | A list of files required by a Task. The Task will wait until the files are available before starting. E.g.: `["task_group_1/task_1/results.txt"]`.                       | Yes  | Yes | Yes  | Yes  |
| `workerTags`               | The list of Worker Tags that will be used to match against the Worker Tag of a candidate Worker. E.g., `["tag_x", "tag_y"]`.                                             | Yes  | Yes | Yes  |      |
| `workRequirementData`      | The name of the file containing the JSON document in which the Work Requirement is defined. E.g., `"test_workreq.json"`.                                                 | Yes  |     |      |      |

## Automatic Properties

In addition to the inheritance mechanism, some properties are set automatically by the `yd-submit` command, as a usage convenience if they're not explicitly provided.

### Work Requirement, Task Group and Task Naming

- The **Work Requirement** name is automatically set using a concatenation of the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `mytag_221024-155524-40a`.
- **Task Group** names are automatically created for any Task Group that is not explicitly named, using names of the form `task_group_1` (or `task_group_01`, etc., for larger numbers of Task Groups). Task Group numbers can also be included in user-defined Task Group names using the `{{task_group_number}}` Mustache substitution discussed below.
- **Task** names are automatically created for any Task that is not explicitly named, using names of the form `task_1` (or `task_01`, etc., for larger numbers of Tasks). The Task counter resets for each different Task Group. Task numbers can also be included in user-defined Task names using the `{{task_number}}` Mustache substitution discussed below.

### Task Types

- If `taskType` is set only at the TOML file level, then `taskTypes` is automatically populated for Task Groups, unless overridden.
- If `taskType` is set at the Task level, then `taskTypes` is automatically populated for the Task Groups level using the accumulated Task Types from the Tasks included in each Task Group, unless overridden.
- If `taskTypes` is set at the Task Group Level, and has only one Task Type entry, then `taskType` is automatically set at the Task Level using the single Task Type, unless overridden.

For the **`bash`** and **`docker`** task types, some automatic processing will be performed if the **`executable`** property is set.

#### Bash Tasks

For the **`bash`** Task Type, the script nominated in the `executable` property is automatically added to the `inputs` list (if not already present). This means the script file will be uploaded to the Object Store, and made a requirement of the Task when it runs.

For example (in TOML form):
```toml
taskType = "bash"
inputs = []
executable = "my_bash_script.sh"
arguments = ["1", "2", "3"]
```
is equivalent to:
```toml
taskType = "bash"
inputs = ["my_bash_script.sh"]
arguments = ["my_bash_script.sh", "1", "2", "3"]
```
(For completeness, note that this is also equivalent to:
```toml
taskType = "bash"
uploadFiles = [{localPath = "my_bash_script.sh", uploadPath = "my_bash_script.sh"}]
verifyAtStart = ["my_bash_script.sh"]
flattenInputPaths = true
arguments = ["my_bash_script.sh", "1", "2", "3"]
```
The use of `uploadFiles` and `verifyAtStart` is discussed [below](#file-storage-locations-and-file-usage).)

#### Docker Tasks

For the **`docker`** Task Type, the variables supplied in the `dockerEnvironment` property are unpacked into the argument list as `--env` entries, the Docker container name supplied in the `executable` property is then added to the arguments list, followed by the arguments supplied in the `arguments` property. The `dockerUsername` and `dockerPassword` properties, if supplied, are added to the `environment` property.

For example:
```toml
taskType = "docker"
executable = "my_dockerhub_repo/my_container_image"
dockerEnvironment = { E1 = "EeeOne"}
dockerUsername = "my_user"
dockerPassword = "my_password"
arguments = ["1", "2", "3"]
```
is equivalent to the following being sent for processing by the `docker` Task Type, the YellowDog version of which will log in to the Docker repo (if required) then issue a `docker run` command with the arguments supplied:
```toml
taskType = "docker"
arguments = ["--env TASK_NAME=<task_name> --env E1=EeeOne", "my_dockerhubrepo/my_container_image", "1", "2", "3"]
environment = {DOCKER_USERNAME = "my_user", DOCKER_PASSWORD = "my_password"}
```

#### Bash & Docker without Automatic Processing

If the `executable` property is not supplied, the automatic processing above for `bash` and `docker` taskTypes is not applied.

### Task Counts

This property will expand the number of Tasks to match `taskCount`.

The `taskCount` property can be set in the `workRequirement` section of the `config.toml` file, or in the Work Requirement or `taskGroup` sections of a JSON Work Requirement definition. 

In the former case, the `taskCount` applies only to the `Task` specified within the `config.toml` file and is not inherited by JSON Work Requirement specifications.

In the latter case, the `taskCount` applies to the Task specified within the Task Group, and there must be zero or one Task(s) listed within the group or `taskCount` is ignored.

## Examples

### TOML Properties in the `workRequirement` Section

Here's an example of the `workRequirement` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workRequirement]
    arguments = ["1", "TWO"]
    captureTaskOutput = true
    completedTaskTtl = 10
    csvFile = "file1.csv"
    csvFiles = ["file1.csv", "file3.csv:3"]
    dockerEnvironment = {MY_DOCKER_VAR = 100}
    dockerPassword = "myPassword"
    dockerUsername = "myUsername"
    environment = {MY_VAR = 100}
    exclusiveWorkers = false
    executable = "my-container"
    finishIfAllTasksFinished = true
    finishIfAnyTaskFailed = false
    flattenInputPaths = false
    flattenUploadPaths = false
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
    taskBatchSize = 1000
    taskCount = 100
    taskData = "my_data_string"
    taskDataFile = "my_data_file.txt"
    taskName = "my_task_number_{{task_number}}"
    taskGroupName = "my_task_group_number_{{task_group_number}}"
    taskType = "docker"
    tasksPerWorker = 1
    uploadFiles = [{localPath = "file_1.txt", uploadPath = "file_1.txt"}]
    vcpus = [1, 4]
    verifyAtStart = ["ready_results.txt"]
    verifyWait = ["wait_for_results.txt"]
    workerTags = ["tag-{{username}}"]
    workRequirementData = "work_requirement.json"
```

### JSON Properties at the Work Requirement Level

Showing all possible properties at the Work Requirement level:

```json
{
  "arguments": [1, "TWO"],
  "captureTaskOutput": true,
  "completedTaskTtl": 10,
  "dockerEnvironment": {"MY_DOCKER_VAR": 100},
  "dockerPassword": "myPassword",
  "dockerUsername": "myUsername",
  "environment": {"MY_VAR": 100},
  "exclusiveWorkers": false,
  "executable": "my-container",
  "finishIfAllTasksFinished": true,
  "finishIfAnyTaskFailed": false,
  "flattenInputPaths": false,
  "flattenUploadPaths": false,
  "fulfilOnSubmit": false,
  "inputs": ["app/main.py", "app/requirements.txt"],
  "instanceTypes": ["t3a.micro", "t3.micro"],
  "maxWorkers": 1,
  "maximumTaskRetries": 0,
  "minWorkers": 1,
  "name": "my-work-requirement",
  "outputs": ["results.txt"],
  "priority": 0.0,
  "providers": ["AWS"],
  "ram": [0.5, 2],
  "regions": ["eu-west-2"],
  "taskCount": 100,
  "taskData": "my_task_data_string",
  "taskDataFile": "my_data_file.txt",
  "taskTypes": ["docker"],
  "tasksPerWorker": 1,
  "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
  "vcpus": [1, 4],
  "verifyAtStart": ["ready_results.txt"],
  "verifyWait": ["wait_for_results.txt"],
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

### JSON Properties at the Task Group Level

Showing all possible properties at the Task Group level:

```json
{
  "taskGroups": [
    {
      "arguments": [1, "TWO"],
      "captureTaskOutput": true,
      "completedTaskTtl": 10,
      "dockerEnvironment": {"MY_DOCKER_VAR": 100},
      "dockerPassword": "myPassword",
      "dockerUsername": "myUsername",
      "environment": {"MY_VAR": 100},
      "exclusiveWorkers": false,
      "executable": "my-container",
      "finishIfAllTasksFinished": true,
      "finishIfAnyTaskFailed": false,
      "flattenInputPaths": false,
      "inputs": ["app/main.py", "app/requirements.txt"],
      "instanceTypes": ["t3a.micro", "t3.micro"],
      "maximumTaskRetries": 0,
      "maxWorkers": 1,
      "minWorkers": 1,
      "name": "first-task-group",
      "outputs": ["results.txt"],
      "priority": 0.0,
      "providers": ["AWS"],
      "ram": [0.5, 2],
      "regions": ["eu-west-2"],
      "taskCount": 5,
      "taskData": "my_task_data_string",
      "taskDataFile": "my_data_file.txt",
      "taskTypes": ["docker"],
      "tasksPerWorker": 1,
      "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
      "vcpus": [1, 4],
      "verifyAtStart": ["ready_results.txt"],
      "verifyWait": ["wait_for_results.txt"],
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

### JSON Properties at the Task Level

Showing all possible properties at the Task level:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": [1, 2],
          "captureTaskOutput": true,
          "dockerEnvironment": {"MY_DOCKER_VAR": 100},
          "dockerPassword": "myPassword",
          "dockerUsername": "myUsername",
          "environment": {"MY_VAR": 100},
          "executable": "my-container",
          "flattenInputPaths": false,
          "inputs": ["app/main.py", "app/requirements.txt"],
          "name": "my-task",
          "outputs": ["results.txt"],
          "taskData": "my_task_data_string",
          "taskDataFile": "my_data_file.txt",
          "taskType": "docker",
          "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
          "verifyAtStart": ["ready_results.txt"],
          "verifyWait": ["wait_for_results.txt"]
        }
      ]
    }
  ]
}
```

## Mustache Directives in Work Requirement Properties

Mustache template directives can be used within any property value in TOML configuration files or Work Requirement JSON files. See the description [above](#mustache-template-directives) for more details on Mustache directives. This is a powerful feature that allows Work Requirements to be parameterised by supplying values on the command line, via environment variables or via the TOML file.

### Task and Task Group Naming

The following numbering substitutions are available for use in Task and Task Group naming, i.e., they can be used in the `name` properties for Tasks and Task Groups respectively in JSON Work Requirements. Note that Task Group names cannot use the `{{task_number}}` directive.

| Directive               | Description                                       | Task Group | Task |
|:------------------------|:--------------------------------------------------|:-----------|:-----|
| `{{task_group_count}}`  | The number of Task Groups in the Work Requirement | Yes        | Yes  |
| `{{task_group_number}}` | The current Task Group number                     | Yes        | Yes  |
| `{{task_count}}`        | The number of Tasks in the current Task Group     | Yes        | Yes  |
| `{{task_number}}`       | The current Task number                           |            | Yes  |

Numbers are zero-padded for neat formatting and sorting, e.g., Task number 37 of 1000 Tasks would be substituted as `0037`.

As an example, the following JSON Work Requirement:

```json
{
  "taskGroups": [
    {
      "name": "my_task_group_{{task_group_number}}_a1",
      "executable": "ex1.sh",
      "taskCount": 2,
      "tasks": [
        {
          "name": "my_task_{{task_number}}-of-{{task_count}}"
        }
      ]
    },
    {
      "name": "my_task_group_{{task_group_number}}_b1",
      "executable": "ex2.sh",
      "taskCount": 2,
      "tasks": [
        {
          "name": "my_task_{{task_number}}-of-{{task_count}}"
        }
      ]
    }
  ]
}
```

... would create Task Groups named `my_task_group_1_a1` and `my_task_group_2_b1`, each containing Tasks named `my_task_1-of-2`, `my_task_2-of-2`.

## Dry-Running Work Requirement Submissions

To examine the JSON that will actually be sent to the YellowDog API after all processing, use the `--dry-run` command line option when running `yd-submit`. This will print the fully processed JSON for the Work Requirement. Nothing will be submitted to the Platform.

The dry-run is useful for inspecting the results of all the processing that's been performed. To suppress all output except for the JSON itself, use the `--quiet` (`-q`) command line option.

Note that the generated JSON is a consolidated form of exactly what will be submitted to the API, so will differ in some ways from the JSON form ingested by `yd-submit`. Also, in actual API submissions, the Work Requirement and Task Groups are submitted first, and Tasks are added in subsequent calls, so the unified JSON document is just for convenience.

A simple example of the JSON output is shown below, showing a Work Requirement with a single Task Group, containing a single Task.

`% yd-submit --dry-run --quiet`
```json
{
  "fulfilOnSubmit": false,
  "name": "pyex-bash_230114-095504-53a",
  "namespace": "pyexamples",
  "priority": 0,
  "tag": "pyex-bash",
  "taskGroups": [
    {
      "finishIfAllTasksFinished": true,
      "finishIfAnyTaskFailed": false,
      "name": "task_group_1",
      "priority": 0,
      "runSpecification": {
        "maximumTaskRetries": 0,
        "taskTypes": ["bash"],
        "workerTags": ["pyex-bash"]
      },
      "tasks": [
        {
          "arguments": ["pyex-bash_230114-095504-53a/sleep_script.sh"],
          "environment": {},
          "inputs": [
            {
              "objectNamePattern": "pyex-bash_230114-095504-53a/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_WAIT"
            }
          ],
          "name": "task_01",
          "outputs": [
            {"alwaysUpload": true, "required": false, "source": "PROCESS_OUTPUT"}
          ],
          "taskType": "bash"
        }
      ]
    }
  ]
}
```

### Submitting 'Raw' JSON Work Requirement Specifications

It's possible to use the JSON output of `yd-submit --dry-run` (such as the example above) as a self-contained, fully-specified Work Requirement specification, using the `--json-raw` (or `-j`) command line option, i.e.: `yd-submit --json-raw <filename.json>`.

This will submit the Work Requirement, then add all the specified Tasks.

Mustache directives **can** be used in the raw JSON file, just as in the other Work Requirement JSON examples, but there is no property inheritance, including from the `[workRequirement]` section of the TOML configuration or from Work Requirement properties supplied on the command line.

Note that there is no automatic file upload when using this option, so any files required at the start of the task (specified using `VERIFY_AT_START`) must be present before the Tasks are uploaded, or the Tasks will fail immediately. The `yd-upload` command can be used to upload files beforehand.

## File Storage Locations and File Usage

This section discusses how to upload files from local storage to the YellowDog Object Store, how those files are transferred to Worker Nodes for Task processing, how the results of Task processing are returned by Worker Nodes, and how files are transferred back from the YellowDog Object Store to local storage.

### Files Uploaded to the Object Store from Local Storage

#### Files in the `inputs` List

When a Work Requirement is submitted using `yd-submit`, files are uploaded to the YellowDog Object Store if they're included in the list of files in the `inputs` property. (For the case of the `bash` Task Type, the script specified in the `executable` property is also automatically uploaded as a convenience, even if not included in the `inputs` list.)

Files are uploaded to the Namespace specified in the configuration. Within the Namespace, each Work Requirement has a separate folder that shares the name of the Work Requirement, and in which all files related to the Work Requirement are stored.

1. Files to be uploaded that are in the **same directory as the Work Requirement specification** (the TOML or JSON file) are uploaded to the root of the Work Requirement folder.


2. Files to be uploaded that are in **subdirectories below the Work Requirement specification, or where absolute pathnames are supplied** are placed in the Object Store in directories that mirror their local storage locations.


3. Files to be uploaded that are in **directories relative to the Work Requirement specification, using `..` relative paths** are placed in Object Store directories in which the `..` parts of the pathname are replaced with an integer count of the number of `..` entries (because we can't use the `..` relative form in the Object Store).

Assuming a Namespace called `development` and a Work Requirement named `testrun_221108-120404-7d2`, the following locations are used when uploading files following the patterns above:

```shell
"inputs" : ["file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
"inputs" : ["dev/file_1.txt"] -> development:testrun_221108-120404-7d2/dev/file_1.txt
"inputs" : ["/home/dev/file_1.txt"] -> development:testrun_221108-120404-7d2/home/dev/file_1.txt
"inputs" : ["../dev/file_1.txt"] -> development:testrun_221108-120404-7d2/1/dev/file_1.txt
"inputs" : ["../../dev/file_1.txt"] -> development:testrun_221108-120404-7d2/2/dev/file_1.txt
```

**Using `flattenUploadPaths`**

The `flattenUploadPaths` property can be used to suppress the mirroring of any local directory structure when uploading files to the Object Store. If set to `true`, all files will be uploaded to the root of the Work Requirement folder. For example:

```shell
"inputs" : ["file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
"inputs" : ["dev/file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
"inputs" : ["/home/dev/file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
"inputs" : ["../dev/file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
"inputs" : ["../../dev/file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
```

The property default is `false`. This property **can only be set at the Work Requirement level** and will therefore apply to all Task Groups and Tasks within a Work Requirement.

When files appear in the `inputs` list, they are also automatically added to the list of files required by the relevant Task(s) as `VerifyAtStart` dependencies.

#### Files in the `uploadFiles` List

The `uploadFiles` property allows more flexible control over the files to be uploaded from local storage to the Object Store when `yd-submit` is run. The property can be used at all Work Requirement levels, from the TOML file through to individual Task specifications.

The property is supplied as a list of dictionary items, each of which must include the properties `localPath` and `uploadPath`. 

- `localPath` specifies the pathname of the file on local storage
- `uploadPath` specifies the name and location of the file's destination in the Object Store

For example, in TOML:
```toml
uploadFiles = [
    {localPath = "file_1.txt", uploadPath = "file_1.txt"},
    {localPath = "dir_2/file_2.txt", uploadPath = "::file_2.txt"},
    {localPath = "file_3.txt", uploadPath = "other_namespace::file_3.txt"}
]
```
And in JSON, with the property set at the Task level, the same specification would be:
```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "uploadFiles": [
            {"localPath": "file_1.txt", "uploadPath": "file_1.txt"},
            {"localPath": "dir_2/file_2.txt", "uploadPath": "::file_2.txt"},
            {"localPath": "file_3.txt", "uploadPath": "other_namespace::file_3.txt"}
          ]
        }
      ]
    }
  ]
}
```
The `uploadFiles` property can also be set at the Work Requirement and Task Group levels, and property inheritance operates as normal.

For `uploadPath`, the same `::` naming convention is available as is used in the `verifyAtStart` and `verifyWait` properties discussed below:

- If `::` is not used, then the file is uploaded relative to the current namespace in a directory named after the name of the Work Requirement
- If `::` is used at the start of the `uploadPath`, the file is uploaded relative to the root of the current namespace
- If `<namespace>::` is used at the start of `uploadPath`, the file is uploaded relative to the root of `<namespace>`

Each file specified in the `uploadFiles` lists will only be uploaded once to each unique upload location for any given invocation of `yd-submit`.

If a file in the `uploadFiles` list is required by a Task, it must separately be added to the `verifyAtStart` or `verifyWait` lists discussed below. This is not done automatically. Note also that the `flattenUploadPaths` property is ignored for files in the `uploadFiles` list.

### File Dependencies Using `verifyAtStart` and `verifyWait`

It's possible to make Tasks dependent on the presence of files in the Object Store by using the `verifyAtStart` and `verifyWait` lists. These files are not automatically uploaded when using `yd-submit` so are either uploaded manually (e.g., by using `yd-upload`), or are created as a result of the execution of other Tasks.

Note that a given file can only appear in *one* of the `inputs`, `verifyAtStart` or `verifyWait` lists.

Tasks with `verifyAtStart` dependencies will fail immediately if the required files are not present when the Task is submitted. Tasks with `verifyWait` dependencies will not become `READY` to be scheduled to Workers until the dependencies are satisfied.

When specifying files in the `verifyAtStart` and `verifyWait` lists, as with the `uploadPath` property discussed above, the file locations can be (1) relative to the Work Requirement name in the current namespace (the default), (2) relative to the root of the current namespace, or (3) relative to the root of a different namespace in the user's Account.

1. For files relative to the Work Requirement name in the current namespace, just use the file path, e.g.
```shell
"verifyWait": ["file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
```

2. For files relative to the root of the current namespace, prefix the file path with `::`, e.g.
```shell
"verifyWait": ["::file_1.txt"] -> development:file_1.txt
```

3. For files relative to the root of a different namespace, prefix the file path with the namespace name and `::`, e.g.
```shell
"verifyWait": ["other_namespace::file_1.txt"] -> other_namespace:file_1.txt
```

The use of the three different forms can be mixed within a single list, e.g.:
```shell
"verifyAtStart": ["file_1.txt", "::dir_2/file_2.txt", "other_namespace::dir_3/file_3.txt"]
```

### Files Downloaded to a Node for use in Task Execution

When a Task is executed by a Worker on a Node, its required files are downloaded from the Object Store prior to Task execution. Any file listed in the `inputs` for a Task is assumed to be required, along with any additional files specified in the `verifyAtStart` and `verifyWait` lists. (Note that a file should only appear in one of these three lists, otherwise `yd-submit` will return an error.)

When a Task is started by the Agent, its working directory has a pattern something like:

`/var/opt/yellowdog/yd-agent-4/data/workers/1/ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1`

(`ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1` is an ephemeral directory that is removed after the Task finishes and any outputs have been uploaded.)

Files that are downloaded by the Agent prior to Task execution are located as follows:

1. If the `flattenInputPaths` property is set to `false` for the Task (this is the default), the downloaded objects are placed in subdirectories that mirror those in the Object Store, including the Work Requirement name, situated beneath the working directory.


2. If the `flattenInputPaths` property is set to `true` for the Task, the downloaded objects are all placed directly in root of the Task's working directory.

For example:

```shell
If the required object is: development:testrun_221108-120404-7d2/dev/file_1.txt

then, if flattenInputPaths is false, the file will be found at:
 -> <working_directory>/testrun_221108-120404-7d2/dev/file_1.txt
 
else, if flattenInputPaths is true, the file will be found at:
 -> <working_directory>/file_1.txt 
 
where <working_directory> is:
  /var/opt/yellowdog/yd-agent-4/data/workers/1/ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1/
```

### Files Uploaded from a Node to the Object Store after Task Execution

After Task completion, the Agent will upload specified output files to the Object Store. The files to be uploaded are those listed in the `outputs` property for the Task.

In addition, the console output of the Task is captured in a file called `taskoutput.txt` in the root of the Task's working directory. Whether the `taskoutput.txt` file is uploaded to the Object Store is determined by the `captureTaskOutput` property for the Task, and this is set to 'true' by default.

If Task outputs are created in subdirectories below the Task's working directory, include the directories for files in the `outputs` property. E.g., if a Task creates files `results/openfoam.tar.gz` and `results/openfoam.log`, then specify these for upload in the `outputs` property as follows:

`"outputs": ["results/openfoam.tar.gz", "results/openfoam.log"]`

When output files are uploaded to the Object Store, they are placed in a Task Group and Task specific directory. So, if the Namespace is `development`, the Work Requirement is `testrun_221108-120404-7d2`, the Task Group is `task_group_1` and the Task is `task_1`, then the files above would be uploaded to the Object Store as follows:

```shell
development:testrun_221108-120404-7d2/task_group_1/task_1/results/openfoam.tar.gz
development:testrun_221108-120404-7d2/task_group_1/task_1/results/openfoam.log
development:testrun_221108-120404-7d2/task_group_1/task_1/taskoutput.txt
```

### Files Downloaded from the Object Store to Local Storage

The `yd-download` command will download all objects from the Object Store to a local directory, on a per Work Requirement basis (including any files that have been uploaded). A local directory is created with the same name as the Namespace and containing the Work Requirement directories.

Use the `--interactive` option with `yd-download` to select which Work Requirement(s) to download.

For the example above, `yd-download` would create a directory called `development` in the current working directory, containing something like:

```shell
development
└── testrun_221108-120404-7d2
    ├── bash_script.sh
    ├── file_1.txt
    └── task_group_1
        └── task_1
            ├── results
            │   ├── openfoam.log
            │   └── openfoam.tar.gz
            └── taskoutput.txt
```

Note that everything within the `namespace:work-requirement` directory in the Object Store is downloaded, including any files that were specified in `inputs` and uploaded as part of the Work Requirement submission. Multiple Task Groups, and multiple Tasks will all appear in the directory structure.

If the `development` directory already exists, `yd-download` will try `development.01`, etc., to avoid overwriting previous downloads.

## Specifying Work Requirements using CSV Data

CSV data files can be used to drive the generation of lists of Tasks, as follows:

- A **prototype** Task specification is created within a JSON Work Requirement specification or in the `workRequirement` section of the TOML configuration file
- The prototype task includes one or more Mustache substitutions
- A CSV file is created, with the **headers** (first row) matching the names of the Mustache substitutions in the Task prototype
- Each subsequent row of the CSV file represents a new Task built using the prototype, with the variables substituted by the values in the row
- A Task will be created for each data row

### Work Requirement CSV Data Example

As an example, consider the following JSON Work Requirement `wr.json`:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": ["{{arg_1}}", "{{arg_2}}", "{{arg_3}}"],
          "environment": {"ENV_VAR_1": "{{env_1}}"}
        }
      ]
    }
  ]
}
```

Note that the Task Group must contain only a single Task, acting as the prototype.

Now consider a CSV file `wr_data.csv` with the following contents:

```text
arg_1, arg_2, arg_3, env_1
A,     B,     C,     E-1
D,     E,     F,     E-2
G,     H,     I,     E-3
```

Note that the (optional) leading spaces after each comma are ignored, but trailing spaces are not and will form part of the imported data.

If these files are processed using `yd-submit -r wr.json -v wr_data.csv`, the following expanded list of three Tasks will be created prior to further processing by the `yd-submit` script:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": ["A", "B", "C"],
          "environment": {"ENV_VAR_1": "E-1"}
        },
        {
          "arguments": ["D", "E", "F"],
          "environment": {"ENV_VAR_1": "E-2"}
        },
        {
          "arguments": ["G", "H", "I"],
          "environment": {"ENV_VAR_1": "E-3"}
        }
      ]
    }
  ]
}
```

### CSV Mustache Substitutions

When the CSV file data is processed, the only substitutions made are those which match the Mustache directives in the prototype Task. The CSV file is the **only** source of substitutions used for this processing phase; all other Mustache substitutions (supplied on the command line, in the TOML configuration file, or from environment variables) are ignored -- i.e., they do not override the contents of the CSV file.

All Mustache directives unrelated to the CSV file data are left unchanged, for subsequent processing by `yd-submit`.

If the value to be inserted is a number (an integer or floating point value) or Boolean, the `{{num:my_number_var}}` and `{{bool:my_boolean_var}}` forms can be used in the JSON file, as with their use in other parts of the JSON Work Requirement specification. The substituted value will assume the nominated type rather than being a string.

### Property Inheritance

All the usual property inheritance features operate as normal. Properties are inherited from the `config.toml` file, and from the relevant sections of the JSON Work Requirement file. Any properties set within a Task prototype are copied to all the generated Tasks.

### Multiple Task Groups using Multiple CSV Files

The use of multiple Task Groups is also supported, by using one CSV file per Task Group. Each Task Group must contain only a single prototype Task.

The CSV files are supplied on the command line in the order of the Task Groups to which they apply. For example, if `wr_json` contains two Task Groups, as follows:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": ["{{arg_1}}", "{{arg_2}}", "{{arg_3}}"],
          "environment": {"ENV_VAR_1": "{{env_1}}"}
        }
      ]
    },
    {
      "tasks": [
        {
          "arguments": ["{{arg_1}}", "{{arg_2}}"],
          "environment": {"ENV_VAR_1": "{{env_1}}", "ENV_VAR_2": "{{env_2}}"}
        }
      ]
    }
  ]
}
```

The `yd-submit` command would then be invoked with a separate CSV file for each Task Group, e.g.:

```shell
yd-submit -r wr.json -v wr_data_task_group_1.csv -v wr_data_task_group_2.csv
```

If there are **fewer** CSV files than Task Groups a warning will be printed and, if there are 'n' CSV files, CSV data processing will be applied to the first 'n' Task Groups in the Work Requirement by default, in the order in which the CSV files were supplied. If there are **more** CSV files than Task Groups, an error will be raised and processing will stop.

It is possible to apply CSV files explicitly to specific Task Groups, by using an optional **index postfix** (e.g., `:2`) at the end of each CSV filename. For example, if there are two CSV files to be applied to the second and fourth Task Groups in a JSON Work Requirement, use the following syntax:

```shell
yd-submit -r wr.json -v wr_data_task_group_2.csv:2 -v wr_data_task_group_4.csv:4
```

Alternatively, the **Task Group name** (if supplied in the JSON file) can be used as the postfix. For example, if the Task Groups above are named `tg_two` and `tg_four`, the `yd-submit` command would become:

```shell
yd-submit -r wr.json -v wr_data_task_group_2.csv:tg_two -v wr_data_task_group_4.csv:tg_four
```

Note that only one CSV file can be applied to any given Task Group. A single CSV file can, however, be reused for multiple Task Groups.

### Using CSV Data with Simple, TOML-Only Work Requirement Specifications

It's possible to use TOML exclusively to derive a list of Tasks from CSV data -- i.e., a JSON Work Requirement specification is not required.

To make use of this:

1. Ensure that no JSON Work Requirement document is specified (no `workRequirementData` in the TOML file, or `--work-requirement` on the command line)
2. Insert the required CSV-supplied Mustache substitutions directly into the TOML properties, e.g. `arguments = ["{{arg_1}}", "{{arg_2}}"]`
3. Specify a single CSV file in the `csvFiles` TOML property, e.g. `csvFiles = ["wr_data.csv"]`, or provide the CSV file on the command line `-v wr_data.csv`

When `yd-submit` is run, it will expand the Task list to match the number of data rows in the CSV file.

### Inspecting the Output of CSV Variable Substitution

The `--process-csv-only` (or `-p`) option can be used with `yd-submit` to output the JSON Work Requirement after CSV variable substitutions only, prior to all other substitutions and property inheritance applied by `yd-submit`.

# Worker Pool Properties

The `workerPool` section of the TOML file defines the properties of the Worker Pool to be created, and is used by the `yd-provision` command. The only mandatory property is `templateId`. All other properties have defaults (or are not required).

The following properties are available:

| Property               | Description                                                                                                | Default        |
|:-----------------------|:-----------------------------------------------------------------------------------------------------------|:---------------|
| `autoscalingIdleDelay` | The time in minutes for which a node can be idle before it can be shut down by auto-scaling.               | `10.0` minutes |
| `autoShutdown`         | Whether the Worker Pool is shut down after all nodes have been idle for the `autoShutdownDelay`.           | `true`         |
| `autoShutdownDelay`    | The delay in minutes for which all nodes can be idle before the Worker Pool is shut down.                  | `10.0` minutes |
| `imagesId`             | The images ID to use when booting instances.                                                               |                |
| `instanceTags`         | The dictionary of instance tags to apply to the instances.                                                 |                |
| `minNodes`             | The minimum number of nodes to which the Worker Pool can be scaled down.                                   | `0`            |
| `maxNodes`             | The maximum number of nodes to which the Worker Pool can be scaled up.                                     | `1`            |
| `name`                 | The name of the Worker Pool.                                                                               | Automatic      |
| `nodeBootTimeLimit`    | The time in minutes allowed for a node to boot and register with the platform before it is terminated.     | `10.0` minutes |
| `targetInstanceCount`  | The initial number of nodes to create for the Worker Pool.                                                 | `1`            |
| `templateId`           | The YellowDog Compute Template ID to use for provisioning.                                                 |                |
| `userData`             | User Data to be supplied to instances on boot.                                                             |                |
| `workersPerVCPU`       | The number of Workers to establish per vCPU on each node in the Worker Pool. (Overrides `workersPerNode`.) |                |
| `workersPerNode`       | The number of Workers to establish on each node in the Worker Pool.                                        | `1`            |
| `workerPoolData`       | The name of a file containing a JSON document defining a Worker Pool.                                      |                |
| `workerTag`            | The Worker Tag to publish for the all of the Workers.                                                      |                |

## Automatic Properties

The name of the Worker Pool, if not supplied, is automatically generated using a concatenation of `wp_`, the `tag` property, a UTC timestamp, and three random hex characters: e,g,. `wp_mytag_221024-155524-b0a`.

## TOML Properties in the `workerPool` Section

Here's an example of the `workerPool` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workerPool]
    autoShutdown = true
    autoShutdownDelay = 10
    autoscalingIdleDelay = 3
    imagesId = "ydid:imgfam:000000:41962592-577c-4fde-ab03-d852465e7f8b"
    instanceTags = {}
    maxNodes = 1
    minNodes = 1
    name = "my-worker-pool"
    nodeBootTimeLimit = 5
    targetInstanceCount = 1
    templateId = "ydid:crt:D9C548:465a107c-7cea-46e3-9fdd-15116cb92c40"
    userData = ""
    workerTag = "tag-{{username}}"
    workersPerNode = 1
#   workerPoolData = "worker_pool.json"
```

## Worker Pool Specification Using JSON Documents

It's also possible to capture a Worker Pool definition as a JSON document. The JSON filename can be supplied either using the command line with the `--worker-pool` or `-p` parameter with `yd-provision`, or by populating the `workerPoolData` property in the TOML configuration file with the JSON filename. Command line specification takes priority over TOML specification.

The JSON specification allows the creation of **Advanced Worker Pools**, with different node types and the ability to specify Node Actions.

When using a JSON document to specify the Worker Pool, the schema of the document is identical to that expected by the YellowDog REST API for Worker Pool Provisioning.

### Worker Pool JSON Examples

The example below is of a simple JSON specification of a Worker Pool with one initial node,  shutdown conditions, etc.

```json
{
  "requirementTemplateUsage": {
    "maintainInstanceCount": false,
    "requirementName": "wp_pyex-primes_230113-161528-da0",
    "requirementNamespace": "pyexamples",
    "requirementTag": "pyex-primes",
    "targetInstanceCount": 1,
    "templateId": "ydid:crt:D9C548:465a107c-7cea-46e3-9fdd-15116cb92c40"
  },
  "provisionedProperties": {
    "autoShutdown": true,
    "autoShutdownConditions": [
      {"delay": "PT1H", "type": "co.yellowdog.platform.model.AllWorkersReleasedShutdownCondition"},
      {"delay": "PT1H", "type": "co.yellowdog.platform.model.AllNodesInactiveShutdownCondition"},
      {"delay": "PT1H", "type": "co.yellowdog.platform.model.UnclaimedAfterStartupShutdownCondition"},
      {"delay": "PT1H", "type": "co.yellowdog.platform.model.NodeActionFailedShutdownCondition"}
    ],
    "createNodeWorkers": {"targetCount": 1, "targetType": "PER_VCPU"},
    "maxNodes": 5,
    "minNodes": 0,
    "nodeBootTimeLimit": "PT5M",
    "nodeIdleGracePeriod": "PT3M",
    "nodeIdleTimeLimit": "PT3M",
    "workerTag": "pyex-bash-docker"
  }
}
```

The next example is of a relatively rich JSON specification of an Advanced Worker Pool, from one of the YellowDog demos. It includes node specialisation, and action groups that respond to the `STARTUP_NODES_ADDED` and `NODES_ADDED` events to drive **Node Actions**.

```json
{
  "requirementTemplateUsage": {
    "maintainInstanceCount": false,
    "targetInstanceCount": 6,
    "templateId": "ydid:crt:D9C548:a7eda287-f9d6-4bc8-b2dc-455344057257",
    "requirementName": "wp_pyex-slurm_230113-165615-2b7",
    "requirementNamespace": "pyexamples",
    "requirementTag": "pyex-slurm"
  },
  "provisionedProperties": {
    "autoShutdown": true,
    "createNodeWorkers": {"targetCount": 0, "targetType": "PER_NODE"},
    "nodeConfiguration": {
      "nodeTypes": [
        {"name": "slurmctld", "count": 1},
        {"name": "slurmd", "min": 5, "slotNumbering": "REUSABLE"}
      ],
      "nodeEvents": {
        "STARTUP_NODES_ADDED": [
          {
            "actions": [
              {
                "action": "WRITE_FILE",
                "path": "nodes.json",
                "content": "{\n  \"nodes\": [\n{{#otherNodes}}\n    {\n      \"name\": \"slurmd{{details.nodeSlot}}\",\n      \"ip\": \"{{details.privateIpAddress}}\"\n    }{{^-last}},{{/-last}}\n{{/otherNodes}}\n  ]\n}",
                "nodeTypes": ["slurmctld"]
              },
              {
                "action": "RUN_COMMAND",
                "path": "start_simple_slurmctld",
                "arguments": ["nodes.json"],
                "environment": {"EXAMPLE": "FOO"},
                "nodeTypes": ["slurmctld"]
              }
            ]
          },
          {
            "actions": [
              {
                "action": "RUN_COMMAND",
                "path": "start_simple_slurmd",
                "arguments": ["{{nodesByType.slurmctld.0.details.privateIpAddress}}", "{{node.details.nodeSlot}}"],
                "nodeTypes": ["slurmd"]
              }
            ]
          },
          {
            "actions": [
              {
                "action": "CREATE_WORKERS",
                "totalWorkers": 1,
                "nodeTypes": ["slurmctld"]
              }
            ]
          }
        ],
        "NODES_ADDED": [
          {
            "actions": [
              {
                "action": "WRITE_FILE",
                "path": "nodes.json",
                "content": "{\n  \"nodes\": [\n{{#filteredNodes}}\n    {\n      \"name\": \"slurmd{{details.nodeSlot}}\",\n      \"ip\": \"{{details.privateIpAddress}}\"\n    }{{^-last}},{{/-last}}\n{{/filteredNodes}}\n  ]\n}",
                "nodeTypes": ["slurmctld"]
              },
              {
                "action": "RUN_COMMAND",
                "path": "add_nodes",
                "arguments": ["nodes.json"],
                "nodeTypes": ["slurmctld"]
              }
            ]
          },
          {
            "actions": [
              {
                "action": "RUN_COMMAND",
                "path": "start_simple_slurmd",
                "arguments": ["{{nodesByType.slurmctld.0.details.privateIpAddress}}", "{{node.details.nodeSlot}}"],
                "nodeIdFilter": "EVENT",
                "nodeTypes": ["slurmd"]
              }
            ]
          }
        ]
      }
    },
    "workerTag": "pyex-slurm-cluster"
  }
}
```

### TOML Properties Inherited by Worker Pool JSON Specifications

When a JSON Worker Pool specification is used, the following properties from the `config.toml` file can be inherited:

- `name`: Mapped to `requirementName` in JSON. This will be generated automatically if not supplied in either the TOML file or the JSON specification.
- `requirementNamespace`
- `requirementTag`
- `targetInstanceCount`
- `templateId`
- `userData`
- `workerTag`
- `imagesId`
- `instanceTags`

Properties set in the JSON file override those set in the TOML file.

## Mustache Directives in Worker Pool Properties

Mustache template directives can be used within any property value in TOML configuration files or Worker Pool JSON files. See the description [above](#mustache-template-directives) for more details on Mustache directives. This is a powerful feature that allows Worker Pools to be parameterised by supplying values on the command line, via environment variables, or via the TOML file.

An important distinction **only** when using Mustache directives within Worker Pool JSON documents is that each directive **must be preceded by a `__` (double underscore)** to disambiguate it from Mustache directives that are to be passed directly to the API. For example, use: `__{{username}}` to apply a substitution for the `username` default substitution.

## Dry-Running Worker Pool Provisioning

To examine the JSON that will actually be sent to the YellowDog API after all processing, use the `--dry-run` command line option when running `yd-provision`. This will print the JSON specification for the Worker Pool. Nothing will be submitted to the platform.

The generated JSON is produced after all processing (incorporating `config.toml` properties, Mustache substitutions, etc.) has been concluded, so the dry-run is useful for inspecting the results of all the processing that's been performed.

To suppress all output except for the JSON itself, use the `--quiet` (`-q`) command line option.

The JSON dry-run output could itself be used by `yd-provision`, if captured in a file, e.g.:

```shell
yd-provision --dry-run -q > my_worker_pool.json
yd-provision -p my_worker_pool.json
```

# Jsonnet Support

In all circumstances where JSON files are used by the Python Examples scripts,  **[Jsonnet](https://jsonnet.org)** files cab be used instead. This allows the use of Jsonnet's powerful JSON extensions, including comments, variables, functions, etc.

A simple usage example might be:

```shell
yd-submit --work-requirement my_work_req.jsonnet
```

The use of the filename extension `.jsonnet` will invoke Jsonnet evaluation. (Note that a temporary JSON file is created as part of Jsonnet processing, which you may see referred to in error messages: this file will have been deleted before the script stops.)

## Jsonnet Installation

Jsonnet is **not** installed by default when `yellowdog-python-examples` is installed, because the package has binary components which are not available on PyPI for all platforms. If you try to use a Jsonnet file in the absence of Jsonnet, the scripts will print an error message, and suggest an installation mechanism.

To install Jsonnet at the same time as installing or updating the Python Examples scripts, modify the installation as follows to include the `jsonnet` option:

```
pip install -U "yellowdog-python-examples[jsonnet]"
```

To install Jsonnet separately from `yellowdog-python-examples`, try:

```shell
pip install -U jsonnet
```

If this fails, try:

```shell
pip install -U jsonnet-binary
```

If both of these methods fail, you'll need to ensure that the platform on which you're running has the required build tools available, so that the Jsonnet binary components can be built locally. The required build packages vary by platform but usually include general development tools including a C++ compiler, and Python development tools including the Python headers.

Please get in touch with YellowDog if you get stuck.

## Mustache Substitutions in Jsonnet Files

The scripts provide full support for Mustache substitutions in Jsonnet files, using the same rules as for the JSON specifications. Remember that for **Worker Pool** specifications, Mustache substitutions must be prefixed by `__`, e.g. `"__{{username}}}"`.

Mustache processing is performed **before** Jsonnet evaluation into the internal JSON representation.

## Checking Jsonnet Processing

The `dry-run` (`-D`) option of the `yd-submit` and `yd-provision` commands will generate JSON output representing the full processing of the Jsonnet file into what will be submitted to the API. This allows inspection to check that the output matches expectations, prior to submitting to the Platform.

## Jsonnet Example

Here's an example of a Jsonnet file that generates a Work Requirement with four Tasks:

```jsonnet
# Function for synthesising Tasks
local Task(arguments=[], environment={}) = {
    arguments: arguments,
    environment: environment,
    name: "my_task_{{task_number}}"
};

# Work Requirement
{
  "name": "workreq_{{datetime}}",
  "taskGroups": [
    {
      "tasks": [
        Task(["1"], {A: "A_1"}),  # arguments and environment
        Task(["2", "3"], {}),     # arguments and empty environment
        Task(["4"]),              # arguments and default environment
        Task()                    # default arguments and environment
      ]
    }
  ]
}
```

When this is inspected using the `dry-run` option (`yd-submit -Dq -r my_work_req.jsonnet`), this is the processed output:

```json
{
  "fulfilOnSubmit": false,
  "name": "workreq_230114-140645",
  "namespace": "pyexamples",
  "priority": 0,
  "tag": "pyex-bash",
  "taskGroups": [
    {
      "finishIfAllTasksFinished": true,
      "finishIfAnyTaskFailed": false,
      "name": "task_group_1",
      "priority": 0,
      "runSpecification": {
        "maximumTaskRetries": 0,
        "taskTypes": ["bash"],
        "workerTags": ["pyex-bash-docker"]
      },
      "tasks": [
        {
          "arguments": ["workreq_230114-140645/sleep_script.sh", "1"],
          "environment": {"A": "A_1"},
          "inputs": [
            {
              "objectNamePattern": "workreq_230114-140645/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_AT_START"
            }
          ],
          "name": "my_task_1",
          "outputs": [
            {"alwaysUpload": true, "required": false, "source": "PROCESS_OUTPUT"}
          ],
          "taskType": "bash"
        },
        {
          "arguments": ["workreq_230114-140645/sleep_script.sh", "2", "3"],
          "environment": {},
          "inputs": [
            {
              "objectNamePattern": "workreq_230114-140645/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_AT_START"
            }
          ],
          "name": "my_task_2",
          "outputs": [
            {"alwaysUpload": true, "required": false, "source": "PROCESS_OUTPUT"}
          ],
          "taskType": "bash"
        },
        {
          "arguments": ["workreq_230114-140645/sleep_script.sh", "4"],
          "environment": {},
          "inputs": [
            {
              "objectNamePattern": "workreq_230114-140645/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_AT_START"
            }
          ],
          "name": "my_task_3",
          "outputs": [
            {"alwaysUpload": true, "required": false, "source": "PROCESS_OUTPUT"}
          ],
          "taskType": "bash"
        },
        {
          "arguments": ["workreq_230114-140645/sleep_script.sh"],
          "environment": {},
          "inputs": [
            {
              "objectNamePattern": "workreq_230114-140645/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_AT_START"
            }
          ],
          "name": "my_task_4",
          "outputs": [
            {"alwaysUpload": true, "required": false, "source": "PROCESS_OUTPUT"}
          ],
          "taskType": "bash"
        }
      ]
    }
  ]
}
```

# Command List

Help is available for all commands by invoking a command with the `--help` or `-h` option. Some command line parameters are common to all commands, while others are command-specific.

All destructive commands require user confirmation before taking effect. This can be suppressed using the `--yes` or `-y` option, in which case the command will proceed without confirmation.

Some commands support the `--interactive` or `-i` option, allowing user selections to be made. E.g., this can be used to select which object paths to delete.

The `--quiet` or `-q` option reduces the command output down to essential messages only. So, for example, `yd-delete -yq` would delete all matching object paths silently.

If you encounter an error it can be useful for support purposes to see the full Python stack trace. This can be enabled by running the command using the `--debug` option.

## yd-submit

The `yd-submit` command submits a new Work Requirement, according to the Work Requirement definition found in the `workRequirement` section of the TOML configuration file and/or the specification found in a Work Requirement JSON document supplied using the `--work-requirement` option.

Use the `--dry-run` option to inspect the details of the Work Requirement, Task Groups, and Tasks that will be submitted, in JSON format.

Once submitted, the Work Requirement will appear in the **Work** tab in the YellowDog Portal.

The Work Requirement's progress can be tracked to completion by using the `--follow` (or `-f`) option when invoking `yd-submit`: the command will report on Tasks as they conclude and won't return until the Work Requirement has finished.

## yd-provision

The `yd-provision` command provisions a new Worker Pool according to the specifications in the `workerPool` section of the TOML configuration file and/or in the specification found in a Worker Pool JSON document supplied using the `--worker-pool` option.

Use the `--dry-run` option to inspect the details of the Worker Pool specification that will be submitted, in JSON format.

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

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete. Note that it's easy to use `yd-delete` to clear the contents of a namespace by using an empty `tag`, as follows:

```shell
yd-delete -t ""
```

This can be extended to any other namespace by using the `--namespace`/`-n` option.

## yd-upload

The `yd-upload` command uploads files from the local filesystem to the YellowDog Object store. Files are placed in the configured `namespace` within a directory supplied using the (required) `--directory` option, e.g.:

```shell
yd-upload --directory my_work_requirement file_1 file_2 morefiles/file3
```
To suppress the mirroring of the local directory structure within the object store, use the `--flatten-upload-paths` or `-f` option. Note that if this creates mutliple uploaded files with the same path in the Object Store folder, files will be overwritten.

Files in directories may be recursively uploaded using the `--recursive` or `-r` option, e.g.:

```shell
yd-upload --directory my_work_requirement -r mydir myotherdir
```

To upload to other namespaces, use the `--namespace`/`-n` option.

## yd-shutdown

The `yd-shutdown` command shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

## yd-instantiate

The `yd-instantiate` command instantiates a Compute Requirement (i.e., a set of instances that are managed by their creator and do not automatically become part of a YellowDog Worker Pool).

This command uses the data from the `workerPool` configuration section, but only uses the `name`, `templateId`, `targetInstanceCount`, `instanceTags`, `userData`, and `imagesId` properties. In addition, the Boolean property `maintainInstanceCount` (default = `false`) is available for use with `yd-instantiate`.

Compute Requirements can be instantiated directly from JSON (or Jsonnet) specifications, using the `--compute-requirement` (or `-C`) command line option, followed by the filename. The properties listed above will be inherited from the config.toml `workerPool` specification if they are not present in the JSON file. An example JSON specification is shown below:

```json
{
  "imagesId": "ydid:imgfam:000000:41962592-577c-4fde-ab03-d852465e7f8b",
  "instanceTags": {"a1": "one", "a2": "two"},
  "requirementName": "cr_test_{{datetime}}",
  "requirementNamespace": "pyexamples",
  "requirementTag": "pyexamples-test",
  "templateId": "ydid:crt:000000:230e9a42-97db-4d69-aa91-29ff309951b4",
  "userData": "#/bin/bash\n#Other stuff...",
  "targetInstanceCount": 1,
  "maintainInstanceCount": true
}
```

If a Worker Pool is defined, using `workerPoolData` in the configuration file or by using the `--worker-pool` (or `-p`) option, `yd-instantiate` will extract the Compute Requirement from the Worker Pool specification (ignoring Worker-Pool-specific data), and use that for instantiating the Compute Requirement.

Use the `--dry-run` option to inspect the details of the Compute Requirement specification that will be submitted, in JSON format. The JSON output of this command can be used with the `-C` option above (or with `-p` for Worker Pool specifications).

## yd-terminate

The `yd-terminate` command immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.
