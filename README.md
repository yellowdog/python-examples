# Introduction

This repository contains simple example Python scripts for submitting work to the YellowDog Platform, cancelling work, downloading objects and cleaning up the YellowDog Object Store.

It also provides scripts for provisioning Provisioned Worker Pools, shutting down Worker Pools, and terminating the Compute Requirements providing those Worker Pools.

In addition, a template [on-premise configuration](agent/application.yaml.template) is provided to use when deploying the YellowDog agent in Configured Worker Pools.

## Scripts

The Python scripts are contained in the [scripts](/scripts) directory. They use the [YellowDog Python SDK](https://github.com/yellowdog/yellowdog-sdk-python-public)  to interact with the YellowDog Platform.

The instructions below assume that all required files are situated in the [scripts](/scripts) directory and that all commands are run from this directory.

### Script Configuration

Script operation is configured using a simple `TOML` configuration file. A [template configuration file](scripts/config.toml.template) is provided.

The default name for the `TOML` configuration script is `config.toml`. To use alternative `TOML` files, simply supply the filename on the command line using the `--config` (or `-c`) option, e.g.:

`./submit.py --config my_config.toml` or `./submit.py -c my_config.toml`

Alternatively, the name of the configuration file can be set in the environment variable `YD_CONF` and this file will be used by all the scripts.

`export YD_CONF="my_config.toml"`

The environment variable is overridden if a filename is supplied on the command line, i.e., the precedence order is:

`command line > YD_CONF setting > default ('config.toml')`

### Prerequisites

To **submit work requirements** to YellowDog, you'll need the following:

1. A YellowDog Platform Account.


2. Running the scripts requires a Python 3.7+ environment with the required dependencies installed: `pip install -U -r requirements.txt`.


3. In the **Accounts** section under the **Applications** tab of the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be shown once).


4. Copy `config.toml.template` to `config.toml` and in the `common` section populate the `key` and `secret` properties using the values obtained above. These allow the Python scripts to connect to the YellowDog Platform. Modify the `namespace` (for grouping YellowDog objects) and `tag` (used for naming objects) properties as required. In the `workRequirement` section, optionally modify the `workerTags` property to include one or more tags declared by your YellowDog workers.

To **provision worker pools**, you'll also need:

5. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required.


6. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) and Worker Tag required by the Work Requirements to be submitted.


7. In your `config.toml` file, populate the `workerPool` section, including using the `templateId` from the Compute Requirement Template above.

### The `submit.py` script

The script is run using `python submit.py` or `./submit.py`. Its purpose is to submit work to YellowDog in the form of a **Work Requirement**. YellowDog will match the **Task Group** within the Work Requirement to suitable **Workers**, and submit **Tasks** to those Workers.

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
(yellowdog) pwt@pwt-mbp-14 scripts % ./submit.py 
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

The `submit.py` script can be supplied with the `--follow` or `-f` flag, which follows the progress of the Work Requirement to completion, reporting on its progress as it runs.

The agent determines whether a Task has succeeded using the exit code from what it runs. In this case that's the exit code from running the Bash script.

#### Bash Script Arguments and Environment

The Bash script or Docker container can optionally be supplied with command line arguments and environment variables using the `arguments` and `environment` fields in `config.toml`, e.g.:
```toml
arguments = ["foo", "bar=5"]
environment = {E1 = "one", E2 = "two"}
```

#### Multiple Task Executions using Identical `arguments` and `environment` for all Tasks

It's sometimes useful for testing to be able to generate multiple Tasks in a single `submit.py` invocation, e.g., to test operation across multiple simultaneous Workers. This can be done using the `taskCount` property in the `config.toml` file.

#### Multiple Task Executions using Varying `arguments` and `environment` for each Task

To run multiple Tasks with different settings for each Task, the `arguments` and `environment` properties can be set in a JSON file, as shown in the following example:

```json
{
  "task_groups": [
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

### The `cancel.py` script

The script is run using `python cancel.py` or `./cancel.py`. This script cancels any active Work Requirements, including any pending Task Groups and Tasks they contain. 

The `namespace` and `tag` values in the `config.toml` file are used to identify which Work Requirements to cancel.

### The `download.py` script

The script is run using `python download.py` or `./download.py`. This script downloads any objects created in the YellowDog Object Store.

The `namespace` and `tag` values are used to determine which objects to download. Objects will be downloaded to a directory with the same name as `namespace`. If a directory already exists, directories with names `<namespace>.01`, etc., will be created.

### The `delete.py` script

The script is run using `python delete.py` or `./delete.py`. This script deletes any objects created in the YellowDog Object Store.

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete.

### The `provision.py` script

The script is run using `python provision.py` or `./provision.py`. This script provisions a new Worker Pool according to the specifications in the `workerPool` section of the configuration file.

### The `shutdown.py` script

The script is run using `python shutdown.py` or `./shutdown.py`. This script shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

### The `terminate.py` script

The script is run using `python terminate.py` or `./terminate.py`. This script immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.
