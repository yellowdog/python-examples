# Introduction

This repository contains minimal example Python scripts for submitting work to the YellowDog Platform, cancelling work, and cleaning up the YellowDog Object Store.

It also includes a template [on-premise configuration](agent/application.yaml.template) to use when deploying the YellowDog agent in Configured Worker Pools.

## Scripts

The Python scripts are contained in the [scripts](/scripts) directory. They use the [YellowDog Python SDK](https://github.com/yellowdog/yellowdog-sdk-python-public)  to interact with the YellowDog Platform.

The instructions below assume that all required files are situated in the [scripts](/scripts) directory and that all commands are run from this directory.

Script operation is configured using a simple `TOML` configuration file. A [template configuration file](scripts/config.toml.template) is provided.

The default name for the `TOML` configuration script is `config.toml`. To use alternative `TOML` files, simply supply the filename as the first parameter to the Python script, e.g.:

`./submit.py my_config.toml`

### Prerequisites

1. You'll need a YellowDog Platform Account.


2. Running the scripts requires a Python 3.7+ environment with the required dependencies installed: `pip install -U -r requirements.txt`.


3. In the **Accounts** section under the **Applications** tab of the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be shown once).


4. Copy `config.toml.template` to `config.toml` and populate the `KEY` and `SECRET` fields using the values obtained above. These allow the Python scripts to connect to the YellowDog Platform. Modify `WORKER_TAGS` to include one or more tags declared by your YellowDog workers.

### The `submit.py` script

The script is run using `python submit.py` or `./submit.py`. Its purpose is to submit work to YellowDog in the form of a **Work Requirement**. YellowDog will match the **Task Group** within the Work Requirement to suitable **Workers**, and submit **Tasks** to those Workers.

Each submitted Task in this example takes the form of a Bash script that will be collected by the YellowDog agent and run by one of its Worker threads.

The console output of the script will be returned to the YellowDog Object Store when the Task is complete.

An example Bash script `test_bash_script.sh` is provided and referred to in `config.toml.template`.

**Important**: The **`application.yaml`** Agent configuration file on the YellowDog worker nodes must provide a `taskType` of `bash`, to allow Bash Tasks to be matched to suitable Workers by the YellowDog scheduler.

```yaml
yda.taskTypes:
  - name: "bash"
    run: "/bin/bash"
```

Optionally, a worker tag may also be set. The scheduler will also use this when matching Tasks to Workers -- i.e., if worker tags are specified by the Task, one of those tags must be present in the Worket configuration.

```yaml
yda.workerTag: "BASH-TEST"
```

The `WORKER_TAGS` value in the `TOML` file can be omitted, to avoid `workerTag` matching.

When the script is run, it will report on the work submitted and provide links to the objects created in the YellowDog portal, where Task execution can be tracked, e.g.:

```shell
(yellowdog) pwt@pwt-mbp-14 scripts % ./submit.py 
2022-07-13 13:08:15 : ID = BASH-TEST_Task_220713T120815-4F9
2022-07-13 13:08:16 : Uploaded file 'test_bash_script.sh' to YDOS: https://portal.yellowdog.co/#/objects/HPECIRRUS/BASH-TEST_Task_220713T120815-4F9%2FINPUT%2Ftest_script.sh?object=true
2022-07-13 13:08:16 : Added WORK REQUIREMENT (https://portal.yellowdog.co/#/work/ydid:workreq:000000:14e5ef6d-8015-4b0a-9e1b-e9d517b78a5b)
2022-07-13 13:08:17 : Added Task 'TASK_1' to Work Requirement Task Group 'OUTPUT'
2022-07-13 13:08:17 : Done
(yellowdog) pwt@pwt-mbp-14 scripts %
```

The submitted Work Requirement will appear in the **Work** tab of the YellowDog Portal. From here the Work Requirement, the Task Group and the Tasks can be inspected and managed.

When the Task is complete, the console output will be available in the `Objects` section of the Portal, in Namespace `HPECIRRUS`, in a folder following the naming convention: `BASH-TEST_Task_<UniqueID>/OUTPUT/TASK_<N>`, in file `taskoutput.txt`.

The agent determines whether a Task has succeeded using the exit code from what it runs. In this case that's the exit code from running the Bash script.

**Bash Script Arguments and Environment**

The Bash script can optionally be supplied with command line arguments and environment variables using the `ARGS` and `BASH_ENV` fields in `config.toml`, e.g.:
```toml
ARGS = ["foo", "bar=5"]
BASH_ENV = {E1 = "one", E2 = "two"}
```

**Multiple Bash Script Executions**

It's sometimes useful for testing to be able to generate multiple Tasks in a single `submit.py` invocation, e.g. to test operation across multiple simultaneous Workers. This can be done using the `TASK_COUNT` field in the `config.toml` file. All Tasks will be identical and will be submitted as part of the same Work Requirement.

### The `cancel.py` script

The script is run using `python cancel.py` or `./cancel.py`. This script cancels any active Work Requirements, including any pending and incomplete Tasks they contain. 

The `NAMESPACE` and `NAME_TAG` values in the `config.toml` file are used to identify which Work Requirements to cancel.

### The `delete.py` script

The script is run using `python delete.py` or `./delete.py`. This script cleans up any objects uploaded to the YellowDog Object Store.

The `NAMESPACE` and `NAME_TAG` values in the `config.toml` file are used to identify which objects to delete.
