# Introduction

This repository contains simple example Python scripts for submitting work to the YellowDog Platform, cancelling work, downloading objects and cleaning up the YellowDog Object Store.

It also provides scripts for creating Provisioned Worker Pools, shutting down Worker Pools, and terminating the Compute Requirements providing those Worker Pools.

In addition, a template [on-premise configuration](agent/application.yaml.template) is provided to use when deploying the YellowDog agent in Configured Worker Pools.

## Scripts

The Python scripts are contained in the [scripts](/scripts) directory. They use the [YellowDog Python SDK](https://github.com/yellowdog/yellowdog-sdk-python-public)  to interact with the YellowDog Platform.

### Script Installation

**Requirements**:

- Python 3.7 or later (including `pip` for package installation)
- Git

It's recommended that installation is performed in a Python virtualenv (or similar) to isolate the installation from other Python environments.

**Install** the scripts using `pip` as follows:

```shell
pip install -U pip wheel
pip install -U git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

**Update** the scripts using:

```shell
pip install -U --force-reinstall --no-deps git+https://github.com/yellowdog/python-examples#subdirectory=scripts
```

The installation places a number of `yd-*` commands on the PATH of the virtualenv: `yd-delete`, `yd-download`, `yd-provision`, `yd-reformat-json`, `yd-shutdown`, `yd-submit`, `yd-terminate`, `yd-version`, and `yd-which-config`.

### Script Configuration

Script operation is configured using a simple `TOML` configuration file. A [template configuration file](scripts/config.toml.template) is provided.

The default name for the `TOML` configuration script is `config.toml`. To use alternative `TOML` files, simply supply the filename on the command line using the `--config` (or `-c`) option, e.g.:

`yd-submit --config my_config.toml`

Alternatively, the name of the configuration file can be set in the environment variable `YD_CONF` and this file will be used by all the scripts.

`export YD_CONF="my_config.toml"`

The environment variable is overridden if a filename is supplied on the command line, i.e., the precedence order is:

`command line > YD_CONF setting > default ('config.toml')`

### Prerequisites

To **submit work requirements** to YellowDog, you'll need the following:

1. A YellowDog Platform Account.


2. In the **Accounts** section under the **Applications** tab of the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be shown once).


3. Copy `config.toml.template` to `config.toml` and in the `common` section populate the `key` and `secret` properties using the values obtained above. These allow the Python scripts to connect to the YellowDog Platform. Modify the `namespace` (for grouping YellowDog objects) and `tag` (used for naming objects) properties as required. In the `workRequirement` section, optionally modify the `workerTags` property to include one or more tags declared by your YellowDog workers.

To **provision worker pools**, you'll also need:

4. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required.


5. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) and Worker Tag required by the Work Requirements to be submitted.


6. In your `config.toml` file, populate the `workerPool` section, including using the `templateId` from the Compute Requirement Template above.

## Script Details

### yd-submit

The purpose of `yd-submit` is to submit work to YellowDog in the form of a **Work Requirement**. YellowDog will match the **Task Group** within the Work Requirement to suitable **Workers**, and submit **Tasks** to those Workers.

Each submitted Task in this example takes the form of a Bash script that will be collected by the YellowDog agent and run by one of its Worker threads, or a Docker container image to be run.

The console output will be returned to the YellowDog Object Store when the Task is complete.

An example Bash script `test_bash_script.sh` is provided and referred to in `config.toml.template`.

**Important**: The **`application.yaml`** Agent configuration file on the YellowDog worker nodes must provide a `taskType` of `bash` and/or `docker`, to allow Bash Tasks and/or Docker container images to be matched to suitable Workers by the YellowDog scheduler, e.g.:

```yaml
yda.taskTypes:
  - name: "bash"
    run: "/bin/bash"
```

Optionally, a worker tag may also be set. The scheduler will also use this when matching Tasks to Workers -- i.e., if worker tags are specified by the Task, one of those tags must be present in the Worker configuration.

```yaml
yda.workerTag: "MY-TEST"
```

The `workerTags` property in the `TOML` file can be omitted, to avoid `workerTag` matching.

When the script is run, it will report on the work submitted and provide links to the objects created in the YellowDog portal, where Task execution can be tracked, e.g.:

```shell
(yellowdog) pwt@pwt-mbp-14 scripts % yd-submit
2022-07-13 13:08:15 : Loading configuration data from: 'config.toml'
2022-07-13 13:08:15 : ID = BASH-TEST_Task_220713T120815-4F9
2022-07-13 13:08:16 : Uploaded file 'test_bash_script.sh' to YDOS: https://portal.yellowdog.co/#/objects/MY_namespace/BASH-TEST_Task_220713T120815-4F9%2FINPUT%2Ftest_script.sh?object=true
2022-07-13 13:08:16 : Added WORK REQUIREMENT (https://portal.yellowdog.co/#/work/ydid:workreq:000000:14e5ef6d-8015-4b0a-9e1b-e9d517b78a5b)
2022-07-13 13:08:17 : Added Task 'TASK_1' to Work Requirement Task Group 'OUTPUT'
2022-07-13 13:08:17 : Done
(yellowdog) pwt@pwt-mbp-14 scripts %
```

The submitted Work Requirement will appear in the **Work** tab of the YellowDog Portal. From here the Work Requirement, the Task Group and the Tasks can be inspected and managed.

When the Task is complete, the console output `taskoutput.txt` will be available in the `Objects` section of the Portal, in a folder within the specified Namespace.

The `yd-submit` command can be supplied with the `--follow` or `-f` flag, which follows the progress of the Work Requirement to completion, reporting on its progress as it runs.

The agent determines whether a Task has succeeded using the exit code from what it runs. In this case that's the exit code from running the Bash script.

#### Bash Script Arguments and Environment

The Bash script or Docker container can optionally be supplied with command line arguments and environment variables using the `arguments` and `environment` fields in `config.toml`, e.g.:
```toml
arguments = ["foo", "bar=5"]
environment = {E1 = "one", E2 = "two"}
```

#### Multiple Task Executions Using Identical `arguments` and `environment` for all Tasks

It's sometimes useful for testing to be able to generate multiple Tasks in a single `submit.py` invocation, e.g., to test operation across multiple simultaneous Workers. This can be done using the `taskCount` property in the `config.toml` file.

#### Multiple Task Executions Using Varying `arguments` and `environment` for each Task

To run multiple Tasks with different settings for each Task, the `arguments` and `environment` properties can be set in a JSON file, as shown in the following example:

```json
{
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": ["a1", "a2"],
          "environment": {"e1": "E1", "e2": "E2", "e3": "E3"}
        },
        {
          "arguments": ["a3", "a4"],
          "environment": {"e4": "E4", "e5": "E5", "e6": "E6"}
        },
        {
          "arguments": ["a5", "a6"],
          "environment": {"e7": "E7", "e8": "E8", "e9": "E9"}
        }
      ]
    }
  ]
}
```

The name of the JSON file is supplied in the `workRequirementData` property in the `workRequirement` section of the `config.toml` file, or can be supplied on the command line using the `--work-req` or `-r` option. A JSON filename supplied on the command line takes precedence over one set in the `config.toml` file.

When `workRequirementData` is set, values of the `arguments` and `environment` properties in the `config.toml` file are overridden on a per-task basis, and the `taskCount` property is ignored.

### yd-cancel

The `yd-cancel` command cancels any active Work Requirements, including any pending Task Groups and Tasks they contain. 

The `namespace` and `tag` values in the `config.toml` file are used to identify which Work Requirements to cancel.

### yd-download

The `yd-download` command downloads any objects created in the YellowDog Object Store.

The `namespace` and `tag` values are used to determine which objects to download. Objects will be downloaded to a directory with the same name as `namespace`. If a directory already exists, directories with names `<namespace>.01`, etc., will be created.

### yd-delete

The `yd-delete` command deletes any objects created in the YellowDog Object Store.

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete.

### yd-provision

The yd-provision command provisions a new Worker Pool according to the specifications in the `workerPool` section of the configuration file.

### yd-shutdown

The `yd-shutdown` command shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

### yd-terminate

The `yd-terminate` command immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.
