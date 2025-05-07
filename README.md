# YellowDog Python Examples Commands

<!--ts-->
* [YellowDog Python Examples Commands](#yellowdog-python-examples-commands)
* [Overview](#overview)
* [YellowDog Prerequisites](#yellowdog-prerequisites)
* [Script Installation with Pip](#script-installation-with-pip)
* [Script Installation with Pipx](#script-installation-with-pipx)
* [Usage](#usage)
* [Configuration](#configuration)
* [Naming Rules](#naming-rules)
* [Common Properties](#common-properties)
   * [Importing common properties](#importing-common-properties)
   * [HTTPS Proxy Support](#https-proxy-support)
   * [Specifying Common Properties using the Command Line or Environment Variables](#specifying-common-properties-using-the-command-line-or-environment-variables)
   * [Variable Substitutions in Common Properties](#variable-substitutions-in-common-properties)
* [Variable Substitutions](#variable-substitutions)
   * [Default Variables](#default-variables)
   * [User-Defined Variables](#user-defined-variables)
      * [Variable Naming](#variable-naming)
      * [Setting Variable Values](#setting-variable-values)
      * [Precedence Order](#precedence-order)
      * [Nested Variables](#nested-variables)
      * [Providing Default Values for User-Defined Variables](#providing-default-values-for-user-defined-variables)
   * [Variable Substitutions in Worker Pool and Compute Requirement Specifications, and in User Data](#variable-substitutions-in-worker-pool-and-compute-requirement-specifications-and-in-user-data)
* [Work Requirement Properties](#work-requirement-properties)
   * [Work Requirement JSON File Structure](#work-requirement-json-file-structure)
   * [Property Inheritance](#property-inheritance)
   * [Work Requirement Property Dictionary](#work-requirement-property-dictionary)
   * [Automatic Properties](#automatic-properties)
      * [Work Requirement, Task Group and Task Naming](#work-requirement-task-group-and-task-naming)
         * [Obtaining Names/Context from Environment Variables at Task Run Time](#obtaining-namescontext-from-environment-variables-at-task-run-time)
      * [Task Types](#task-types)
         * [Bash, Python, PowerShell and cmd/bat Tasks](#bash-python-powershell-and-cmdbat-tasks)
         * [Docker Tasks](#docker-tasks)
         * [Bash, Python, PowerShell, cmd.exe/batch, and Docker without Automatic Processing](#bash-python-powershell-cmdexebatch-and-docker-without-automatic-processing)
      * [Task and Task Group Counts](#task-and-task-group-counts)
   * [Examples](#examples)
      * [TOML Properties in the workRequirement Section](#toml-properties-in-the-workrequirement-section)
      * [JSON Properties at the Work Requirement Level](#json-properties-at-the-work-requirement-level)
      * [JSON Properties at the Task Group Level](#json-properties-at-the-task-group-level)
      * [JSON Properties at the Task Level](#json-properties-at-the-task-level)
   * [Variable Substitutions in Work Requirement Properties](#variable-substitutions-in-work-requirement-properties)
      * [Work Requirement Name Substitution](#work-requirement-name-substitution)
      * [Task and Task Group Name Substitutions](#task-and-task-group-name-substitutions)
   * [Dry-Running Work Requirement Submissions](#dry-running-work-requirement-submissions)
      * [Submitting 'Raw' JSON Work Requirement Specifications](#submitting-raw-json-work-requirement-specifications)
   * [File Storage Locations and File Usage](#file-storage-locations-and-file-usage)
      * [Files Uploaded to the Object Store from Local Storage](#files-uploaded-to-the-object-store-from-local-storage)
         * [Files in the inputs List](#files-in-the-inputs-list)
         * [Files in the uploadFiles List](#files-in-the-uploadfiles-list)
         * [Using Wildcards in the uploadFiles List](#using-wildcards-in-the-uploadfiles-list)
      * [File Dependencies Using verifyAtStart and verifyWait](#file-dependencies-using-verifyatstart-and-verifywait)
      * [Files Uploaded to the Object Store Using inputsOptional](#files-uploaded-to-the-object-store-using-inputsoptional)
      * [Files Downloaded to a Node for use in Task Execution](#files-downloaded-to-a-node-for-use-in-task-execution)
      * [Files Uploaded from a Node to the Object Store after Task Execution](#files-uploaded-from-a-node-to-the-object-store-after-task-execution)
      * [Files Downloaded from the Object Store to Local Storage](#files-downloaded-from-the-object-store-to-local-storage)
   * [Task Execution Context](#task-execution-context)
      * [Task Execution Steps](#task-execution-steps)
      * [The User and Group used for Tasks](#the-user-and-group-used-for-tasks)
      * [Home Directory for yd-agent](#home-directory-for-yd-agent)
      * [Task Execution Directory](#task-execution-directory)
   * [Specifying Work Requirements using CSV Data](#specifying-work-requirements-using-csv-data)
      * [Work Requirement CSV Data Example](#work-requirement-csv-data-example)
      * [CSV Variable Substitutions](#csv-variable-substitutions)
      * [Property Inheritance](#property-inheritance-1)
      * [Multiple Task Groups using Multiple CSV Files](#multiple-task-groups-using-multiple-csv-files)
      * [Using CSV Data with Simple, TOML-Only Work Requirement Specifications](#using-csv-data-with-simple-toml-only-work-requirement-specifications)
      * [Inspecting the Results of CSV Variable Substitution](#inspecting-the-results-of-csv-variable-substitution)
* [Worker Pool Properties](#worker-pool-properties)
   * [Using Textual Names instead of IDs for Compute Requirement Templates and Image Families](#using-textual-names-instead-of-ids-for-compute-requirement-templates-and-image-families)
   * [Automatic Properties](#automatic-properties-1)
   * [TOML Properties in the workerPool Section](#toml-properties-in-the-workerpool-section)
   * [Worker Pool Specification Using JSON Documents](#worker-pool-specification-using-json-documents)
      * [Worker Pool JSON Examples](#worker-pool-json-examples)
      * [TOML Properties Inherited by Worker Pool JSON Specifications](#toml-properties-inherited-by-worker-pool-json-specifications)
   * [Variable Substitutions in Worker Pool Properties](#variable-substitutions-in-worker-pool-properties)
   * [Dry-Running Worker Pool Provisioning](#dry-running-worker-pool-provisioning)
* [Creating, Updating and Removing Resources](#creating-updating-and-removing-resources)
   * [Overview of Operation](#overview-of-operation)
      * [Resource Creation](#resource-creation)
      * [Resource Update](#resource-update)
      * [Resource Removal](#resource-removal)
      * [Resource Matching](#resource-matching)
   * [Resource Specification Definitions](#resource-specification-definitions)
   * [Generating Resource Specifications](#generating-resource-specifications)
   * [Preprocessing Resource Specifications](#preprocessing-resource-specifications)
   * [Keyrings](#keyrings)
   * [Credentials](#credentials)
   * [Compute Source Templates](#compute-source-templates)
   * [Compute Requirement Templates](#compute-requirement-templates)
   * [Image Families](#image-families)
   * [Namespace Storage Configurations](#namespace-storage-configurations)
   * [Configured Worker Pools](#configured-worker-pools)
   * [Allowances](#allowances)
   * [Attribute Definitions](#attribute-definitions)
      * [String Attribute Definitions](#string-attribute-definitions)
      * [Numeric Attribute Definitions](#numeric-attribute-definitions)
   * [Namespace Policies](#namespace-policies)
* [Jsonnet Support](#jsonnet-support)
   * [Jsonnet Installation](#jsonnet-installation)
   * [Variable Substitutions in Jsonnet Files](#variable-substitutions-in-jsonnet-files)
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
      * [Test-Running a Dynamic Template](#test-running-a-dynamic-template)
   * [yd-terminate](#yd-terminate)
   * [yd-list](#yd-list)
   * [yd-resize](#yd-resize)
   * [yd-create](#yd-create)
   * [yd-remove](#yd-remove)
   * [yd-follow](#yd-follow)
   * [yd-start](#yd-start)
   * [yd-hold](#yd-hold)
   * [yd-boost](#yd-boost)
   * [yd-show](#yd-show)
   * [yd-compare](#yd-compare)

<!-- Created by https://github.com/ekalinin/github-markdown-toc -->
<!-- Added by: pwt, at: Wed Feb 26 15:47:37 GMT 2025 -->

<!--te-->

# Overview

This repository contains a set of command line utilities for driving the YellowDog Platform, written in Python. The scripts use the **[YellowDog Python SDK](https://docs.yellowdog.co/#/sdk)**, the code for which can be found [on GitHub](https://github.com/yellowdog/yellowdog-sdk-python-public).


*(Note: these utilities are intended to be a helpful starting point for experimenting with the YellowDog Platform. They are not assured to be of production quality nor do they represent a standard or recommended method for using YellowDog.)*

This documentation should be read in conjunction with the main **[YellowDog Documentation](https://docs.yellowdog.co)**, which provides a comprehensive description of the concepts and operation of the YellowDog Platform.

Template solutions for experimenting with these utilities can be found in the **[python-examples-templates](https://github.com/yellowdog/python-examples-templates)** repository.

The commands provide the following capabilities:

- **Provisioning** Worker Pools with the **`yd-provision`** command
- **Submitting** Work Requirements with the **`yd-submit`** command
- **Starting** HELD Work Requirements and **Holding** (or pausing) RUNNING Work Requirements with the **`yd-start`** and **`yd-hold`** commands
- **Uploading** files to the YellowDog Object Store with the **`yd-upload`** command
- **Instantiating** Compute Requirements with the **`yd-instantiate`** command
- **Downloading** Results from the YellowDog Object Store with the **`yd-download`** command
- **Aborting** running Tasks with the **`yd-abort`** command
- **Cancelling** Work Requirements with the **`yd-cancel`** command
- **Shutting Down** Worker Pools and Nodes with the **`yd-shutdown`** command
- **Terminating** Compute Requirements with the **`yd-terminate`** command
- **Deleting** objects in the YellowDog Object Store with the **`yd-delete`** command
- **Listing** YellowDog items using the **`yd-list`** command
- **Resizing** Worker Pools and Compute Requirements with the **`yd-resize`** command
- **Boosting** Allowances with the **`yd-boost`** command
- **Creating, Updating and Removing** Source Templates, Compute Templates, Keyrings, Credentials, Namespace Storage Configurations, Image Families, Allowances, Configured Worker Pools, User Attributes, and Namespace Policies with the **`yd-create`** and **`yd-remove`** commands
- **Following Event Streams** for Work Requirements, Worker Pools and Compute Requirements with the **`yd-follow`** command
- **Showing** the details of any YellowDog entity using its YellowDog ID with the **`yd-show`** command
- **Comparing** whether worker pools are a match for task groups with the **`yd-compare`** command

The operation of the commands is controlled using TOML configuration files and/or environment variables and command line arguments. In addition, Work Requirements and Worker Pools can be defined using JSON files providing extensive configurability.

Commands are also provided for the semi-automatic setup of cloud provider accounts for use with YellowDog, and the creation of YellowDog assets to work with these cloud provider accounts. Please see **[Cloud Wizard](README_CLOUDWIZARD.md)** for more details.

Run any command with the `--help`/`-h` option to discover the command's options.

# YellowDog Prerequisites

(See also the quick start guides for [Provisioned](https://github.com/yellowdog/python-examples-templates/blob/main/quickstart.md) and [Configured](https://github.com/yellowdog/python-examples-templates/blob/main/quickstart-configured.md) Worker Pools.)

To submit **Work Requirements** to YellowDog for processing by Configured Worker Pools (on-premise) and/or Provisioned Worker Pools (cloud-provisioned resources), you'll need:

1. A YellowDog Platform Account.


2. An Application Key & Secret: in the **Accounts** section under the **Applications** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/account/applications), use the **Add Application** button to create a new Application, and make a note of its **Key** and **Secret** (these will only be displayed once).


To create **Provisioned Worker Pools**, you'll need:

3. A **Keyring** created via the YellowDog Portal, with access to Cloud Provider credentials as required. The Application must be granted access to the Keyring.


4. One or more **Compute Sources** defined, and a **Compute Requirement Template** created. The images used by instances must include the YellowDog agent, configured with the Task Type(s) to match the Work Requirements to be submitted.

To set up **Configured Worker Pools**, you'll need:

5. A Configured Worker Pool Token: from the **Workers** tab in the [YellowDog Portal](https://portal.yellowdog.co/#/workers), use the **+Add Configured Worker Pool** button to create a new Worker Pool and generate a token.


6. Obtain the YellowDog Agent and install/configure it on your on-premise systems using the Token obtained above. See guidance for [Linux](https://github.com/yellowdog/resources/blob/main/agent-install/linux/README.md) and [Windows](https://github.com/yellowdog/resources/blob/main/agent-install/windows/README-CONFIGURED.md).

# Script Installation with Pip

Python version 3.7 or later is required. It's recommended that the installation is performed in a Python virtual environment (or similar) to isolate the installation from other Python environments on your system.

Installation and subsequent update are via `pip` and PyPI using: 

```shell
pip install -U yellowdog-python-examples
```

If you're interested in including **Jsonnet** support, please see the [Jsonnet Support](#jsonnet-support) section below.

# Script Installation with Pipx

The commands can also be installed using **[pipx](https://pypa.github.io/pipx/)**.

This method requires Python 3.7+ and pipx to be installed. Pipx avoids the need manually to create a virtual environment for Python Examples. To install:

```shell
pipx install yellowdog-python-examples
```

To update:
```shell
pipx upgrade yellowdog-python-examples
```

# Usage

Both of the installation methods above will install a number of **`yd-`** commands on your PATH.

Commands are run from the command line. Invoking any command with the `--help` or `-h` option will display the command line options applicable to that command, e.g.:

```text
 % yd-cancel --help
usage: yd-cancel [-h] [--docs] [--config <config_file.toml>] [--key <app-key>]
                 [--secret <app-secret>] [--namespace <namespace>] [--tag <tag>] [--url <url>]
                 [--variable <var1=v1>] [--quiet] [--debug] [--pac] [--abort] [--follow]
                 [--interactive] [--yes]

YellowDog command line utility for cancelling Work Requirements

optional arguments:
  -h, --help            show this help message and exit
  --docs                provide a link to the documentation for this version
  --config <config_file.toml>, -c <config_file.toml>
                        configuration file in TOML format; default is 'config.toml' in the current
                        directory
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
  --variable <var1=v1>, -v <var1=v1>
                        user-defined variable substitutions; can be supplied multiple times
  --quiet, -q           suppress (non-error, non-interactive) status and progress messages
  --debug               print a stack trace (etc.) on error
  --pac                 enable PAC (proxy auto-configuration) support
  --abort, -a           abort all running tasks with immediate effect
  --follow, -f          when using --abort, poll until all Tasks have been aborted
  --interactive, -i     list, and interactively select, items to act on
  --yes, -y             perform destructive actions without requiring user confirmation
```

# Configuration

By default, the operation of all commands is configured using a **TOML** configuration file.

The configuration file has three possible sections:

1. A `common` section that contains required security properties for interacting with the YellowDog platform, sets the Namespace in which YellowDog assets and objects are created, and a Tag that is used for tagging and naming assets and objects.
2. A `workRequirement` section that defines the properties of Work Requirements to be submitted to the YellowDog platform.
3. A `workerPool` section that defines the properties of Provisioned Worker Pools to be created using the YellowDog platform. 

There is a documented template TOML file provided in [config.toml.template](config.toml.template), containing the main properties that can be configured.

The name of the configuration file can be supplied in three different ways:

1. On the command line, using the `--config` or `-c` options, e.g.:<br>`yd-submit -c jobs/config_1.toml`
2. Using the `YD_CONF` environment variable, e.g.: <br>`export YD_CONF="jobs/config_1.toml"`
3. If neither of the above is supplied, the commands look for a `config.toml` file in the current directory

The options above are shown in order of precedence: a filename supplied on the command line supersedes one set in `YD_CONF`, which supersedes the default.

# Naming Rules

All entity names used within the YellowDog Platform must comply with the following rules:

- Names can only contain the following: lowercase letters, digits, hyphens and underscores (note that spaces are not permitted)
- Names must start with a letter
- Names must end with a letter or digit
- Name length must 60 characters or fewer

These restrictions apply to entities including Namespaces, Tags, Work Requirements, Task Groups, Tasks, Worker Pools, and Compute Requirements, and also apply to entities that are currently used indirectly by these scripts, including Usernames, Credentials, Keyrings, Compute Sources and Compute Templates.

Later sections of this document describe variable substitutions implemented with user-defined and CSV-file-defined variables. As a type modifier within these substitution expressions, the `format_name:` option is available, and works in the same manner as `num:`, `bool:`, etc. The `format_name:` modifier will convert the substituted string into one that satisfies YellowDog naming, by switching characters to lower case, etc.

For example, a variable substitution `{{format_name:ligand_name}}`, with variable `ligand_name` set to `DCCCDE_00000s`, would substitute to become `dcccde_00000s`, and would be acceptable for use as a component of a YellowDog name.

# Common Properties

The `[common]` section of the configuration file can contain the following properties:

| Property    | Description                                                                                        |
|:------------|:---------------------------------------------------------------------------------------------------|
| `key`       | The **key** of the YellowDog Application under which the commands will run                         |
| `secret`    | The **secret** of the YellowDog Application under which the commands will run                      |
| `namespace` | The **namespace** to be used for grouping resources                                                |
| `tag`       | The **tag** to be used for tagging resources and naming objects                                    |
| `url`       | The **URL** of the YellowDog Platform API endpoint. Defaults to `https://portal.yellowdog.co/api`. |
| `usePAC`    | Use PAC (proxy autoconfiguration) if set to `true`                                                 |
| `variables` | A table containing **variable substitutions** (see the Variables section below)                    |

An example `common` section is shown below:

```toml
[common]
    key = "asdfghjklzxcvb-1234567"
    secret = "qwertyuiopasdfghjklzxcvbnm1234567890qwertyu"
    namespace = "project-x"
    tag = "testing-{{username}}"
```

Indentation is optional in TOML files and is for readability only.

## Importing `common` properties

The `common` section can import properties from a separate TOML file, using the `importCommon` property. For example, the `key` and `secret` might be in a shared TOML file called `app_credentials.toml`, with the following contents:

```toml
[common]
    key = "asdfghjklzxcvb-1234567"
    secret = "qwertyuiopasdfghjklzxcvbnm1234567890qwertyu"
```

This could be imported into the main configuration as follows:

```toml
[common]
    importCommon = "app_credentials.toml"

    namespace = "project-x"
    tag = "testing-{{username}}"
```

Properties set in the imported file are superseded by any of the same properties that are present in the main configuration file.

## HTTPS Proxy Support

The commands will respect the value of the environment variable `HTTPS_PROXY` if routing through a proxy is required.

In addition, commands can use proxy autoconfiguration (PAC) if the `--pac` command line option is specified, or if the `usePAC` property is set to `true` in the `[common]` section of the `config.toml` file.

## Specifying Common Properties using the Command Line or Environment Variables

All the common properties can be set using command line options, or in environment variables.

The **command line options** are as follows:

- `--key` or `-k`
- `--secret` or `-s`
- `--namespace` or `-n`
- `--tag` or `-t`
- `--url` or `-u`
- `--pac`

These options can also be listed by running a command with the `--help` or `-h` option.

The **environment variables** are as follows:

- `YD_KEY`
- `YD_SECRET`
- `YD_NAMESPACE`
- `YD_TAG`
- `YD_URL`

When setting the value of the above properties, a property set on the command line takes precedence over one set via an environment variable, and both take precedence over a value set in a configuration file.

If all the required common properties are set using the command line or environment variables, then the entire `common` section of the TOML file can be omitted.

## Variable Substitutions in Common Properties

Note the use of `{{username}}` in the value of the `tag` property example above: this is a **variable substitution** that can optionally be used to insert the login username of the user running the commands. So, for username `abc`, the `tag` would be set to `testing-abc`. This can be helpful to disambiguate multiple users running with the same configuration data.

Variable substitutions are discussed in more detail below.

# Variable Substitutions

Variable substitutions provide a powerful mechanism for introducing variable values into TOML configuration files, and JSON/Jsonnet definitions of Work Requirements and Worker Pools. They can be included in the value of any property in any of these objects, including in values within arrays (lists), e.g., for the `arguments` property, and tables (dictionaries), e.g., the `environment` property.

Variable substitutions are expressed using the `{{variable}}` notation, where the expression is replaced by the value of `variable`.

Substitutions can also be performed for non-string (number, boolean, array, and table) values using the `num:`, `bool:`, `array:`, and `table:` prefixes within the variable substitution:

- Define the variable substitution using one of the following patterns: `"{{num:my_int}}"`, `"{{num:my_float}}"`, `"{{bool:my_bool}}"`, `"{{array:my_array}}"`, `"{{table:my_table}}"`
- Variable definitions supplied on the command line would then be of the form, e.g.: 

```shell
 yd-submit -v my_int=5 -v my_float=2.5 -v my_bool=true \
           -v my_array="[1,2,3]" -v my_table="{'A': 100, 'B': 200}"
```

- In the processed JSON (or TOML), these values would become `5`, `2.5`, `true`, `[1,2,3]`, and `{"A": 100, "B": 200}`, respectively, converted from strings to their correct JSON types

## Default Variables

The following substitutions are automatically created and can be used in any section of the configuration file, or in any JSON specification:

| Directive             | Description                                                    | Example of Substitution |
|:----------------------|:---------------------------------------------------------------|:------------------------|
| `{{username}}`        | The current user's login username, lower case, spaces replaced | jane_smith              |
| `{{date}}`            | The current date (UTC): YYYYMMDD                               | 20221027                |
| `{{time}}`            | The current time (UTC): HHMMSSss                               | 16302699                |
| `{{datetime}}`        | Concatenation of the date and time, with a '-' separator       | 20221027-163026         |
| `{{random}}`          | A random, three digit hexadecimal number (lower case)          | a1c                     |
| `{{namespace}}`       | The `namespace` property.                                      | my_namespace            |
| `{{tag}}`             | The `tag` property.                                            | my_tag                  |
| `{{key}}`             | The application `key` property.                                |                         |
| `{{secret}}`          | The application `secret` property.                             |                         |
| `{{url}}`             | The Platform `url` property.                                   |                         |
| `{{config_dir_abs}}`  | The absolute directory path of the configuration file          | /yellowdog/workloads    |
| `{{config_dir_name}}` | The immediate containing directory of the configuration file   | workloads               |

For the `date`, `time`, `datetime` and `random` directives, the same values will be used for the duration of a command -- i.e., if `{{time}}` is used within multiple properties, the identical value will be used for each substitution.

The `config_dir_` substitutions use the name of the directory containing the nominated TOML configuration file, or the invocation directory if no configuration file is supplied.

## User-Defined Variables

User-defined variables can be supplied using an option on the command line, by setting environment variables prefixed with `YD_VAR_`, by using general environment variables, or by including properties in the `[common]` section of the TOML configuration file.

### Variable Naming

User-defined variable names must not include spaces, but are otherwise unconstrained. When enclosing a variable name in curly brackets, don't insert spaces between the variable name and the brackets.

### Setting Variable Values

1. The **command line** option is `--variable` (or `-v`). For example, `yd-submit -v project_code=pr-213-a -v run_id=1234` will establish two new variables that can be used as `{{project_code}}` and `{{run_id}}`, which will be substituted by `pr-213-a` and `1234` respectively.


2. For **environment variables**, setting the variable `YD_VAR_project_code="pr-213-a"` will create a new variable that can be accessed as `{{project_code}}`, which will be substituted by `pr-213-a`. Note that if running on Windows, all environment variable names are case-insensitive and converted to upper case, so choose upper case variable names only.


3. **General (i.e., non-`YD_VAR_`) environment variables** can be used by adding the `env:` prefix before the name of the environment varable in the substitution, e.g.: `{{env:ENV_VAR_NAME}}`. (If you also need to use one of the type prefixes, just do so as follows (e.g.): `{{num:env:COUNT}}`).


4. For **setting within the TOML file**, include a **`variables`** table in the `[common]` section of the file. E.g., `variables = {project_code = "pr-213a", run_id = "1234"}`. Note that this can also use the form:

```toml
[common.variables]
    project_code = "pr-213a"
    run_id = "1234"
```

### Precedence Order

The precedence order for setting variables is:

1. Command line
2. `YD_VAR` environment variables
3. General environment variables
4. TOML file

This method can also be used to override the default variables, e.g., setting `-v username="other-user"` will override the default `{{username}}` variable.

### Nested Variables

In the case of **TOML file properties only**, variable substitutions can be nested.

For example, if one wanted to select a different `templateId` for a Worker Pool depending on the value of a `region` variable, one could use the following:

```toml
[common.variables]
    template_london = "ydid:crt:65EF4F:a4d757cf-b67a-4eb6-bd39-8a6ffd46c8f4"
    template_phoenix = "ydid:crt:65EF4F:e4239dec-78c2-421c-a7f3-71e61b72946f"
    template_frankfurt = "ydid:crt:65EF4F:329602cf-5945-4aad-a288-ea424d64d55e"

[workerPool]
    templateId = "{{template_{{region}}}}"
```

Then, if one used `yd-provision -v region=phoenix`, the `templateId` property would first resolve to `"{{template_pheonix}}"`, and then to `"ydid:crt:65EF4F:e4239dec-78c2-421c-a7f3-71e61b72946f"`.

Nesting can be up to three levels deep including the top level. Note that sequencing of properties in the TOML file does not matter, e.g., variable `{{a}}` can depend on a variable `{{b}}` that is defined after it in the file.

### Providing Default Values for User-Defined Variables

Each variable can be supplied with a default value, to be used if a value is not explicitly provided for that variable name. The syntax for providing a default is:

```
"{{variable_name:=default_value}}" or
"{{num:numeric_variable_name:=default_numeric_value}}" or
"{{bool:boolean_variable_name:=default_boolean_value}}" or
"{{array:array_name:=default_array}}" or
"{{table:table_name:=default_table}}"
```

An empty-string default variable value can be set as follows: `"{{my_variable:=}}"`.

Examples of use in a TOML file:

```toml
name = "{{name:=my_name}}"
taskCount = "{{num:task_count:=5}}"
finishIfAllTasksFinished = "{{bool:fiaft:=true}}"
arguments = "{{array:args:=[1,2,3]}}"
environment = "{{table:env:={'A':100,'B':200}}}"
```

Default values can be used anywhere that variable substitutions are allowed.  In TOML files only, nested variable substitutions can be used inside default values, e.g.:

```toml
name = "{{name_var:={{tag}}-{{datetime}}}}"
```

## Variable Substitutions in Worker Pool and Compute Requirement Specifications, and in User Data

In JSON specifications for Worker Pools and Compute Requirements, variable substitutions can be used, but **they must be prefixed and postfixed by double underscores** `__`, e.g., `__{{username}}__`. This is to disambiguate client-side variable substitutions from server-side Mustache variable processing.

Variable substitutions can also be used within **User Data** to be supplied to instances, for which the same prefix/postfix requirement applies, **including** for User Data supplied directly using the `userData` property in the `workerPool` section of the TOML file.

# Work Requirement Properties

The `workRequirement` section of the configuration file is optional. It's used only by the `yd-submit` command, and controls the Work Requirement that is submitted to the Platform.

The details of a Work Requirement to be submitted can be captured entirely within the TOML configuration file for simple (single Task Group) examples. More complex examples capture the Work Requirement in a combination of the TOML file plus a JSON document, or in a JSON document only.

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

To specify the file containing the JSON document, either populate the `workRequirementData` property in the `workRequirement` section of the TOML configuration file with the JSON filename, or specify it on the command line as a positional argument (which will override the property in the TOML file), e.g.

`yd-submit --config myconfig.toml my_workreq.json`

## Property Inheritance

Work Requirement specification can be simplified substantially by the property inheritance features in `yd-submit`. In general, properties that are set at a higher level in the hierarchy are inherited at lower levels, unless explicitly overridden.

This means that a property set in the `workRequirement` section of the TOML file can be inherited successively by the Work Requirement, Task Groups, and Tasks in the JSON document (assuming the property is available at each level).  Hence, Tasks inherit from Task Groups, which inherit from the Work Requirement in the JSON document, which inherits from the `workRequirement` properties in the TOML file.

Overridden properties are also inherited at lower levels in the hierarchy. E.g., if a property is set at the Task Group level, it will be inherited by the Tasks in that Task Group unless explicitly overridden.

## Work Requirement Property Dictionary

The following table outlines all the properties available for defining Work Requirements, and the levels at which they are allowed to be used. So, for example, the `provider` property can be set in the TOML file, at the Work Requirement Level or at the Task Group Level, but not at the Task level, and property `dependentOn` can only be set at the Task Group level.

All properties are optional except for **`taskType`** (or **`taskTypes`**).

| Property Name               | Description                                                                                                                                                                                                                                | TOML | WR  | TGrp | Task |
|:----------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----|:----|:-----|:-----|
| `addYDEnvironmentVariables` | Automatically add YellowDog environment variables to each Task's environment.                                                                                                                                                              | Yes  | Yes | Yes  | Yes  |
| `alwaysUpload`              | Whether to attempt to upload task outputs on failure. Default: `true`.                                                                                                                                                                     | Yes  | Yes | Yes  | Yes  |
| `arguments`                 | The list of arguments to be passed to the Task when it is executed. E.g.: `[1, "Two"]`.                                                                                                                                                    | Yes  | Yes | Yes  | Yes  |
| `completedTaskTtl`          | The time (in minutes) to live for completed Tasks. If set, Tasks that have been completed for longer than this period will be deleted. E.g.: `10.0`.                                                                                       | Yes  | Yes | Yes  |      |
| `csvFile`                   | The name of the CSV file used to derive Task data. An alternative to `csvFiles` that can be used when there's only a single CSV file. E.g. `"file.csv"`.                                                                                   | Yes  |     |      |      |
| `csvFiles`                  | A list of CSV files used to derive Task data. E.g. `["file.csv", "file_2.csv:2]`.                                                                                                                                                          | Yes  |     |      |      |
| `dependentOn`               | The name of another Task Group within the same Work Requirement that must be successfully completed before the Task Group is started. E.g. `"task_group_1"`.                                                                               |      |     | Yes  |      |
| `dockerEnvironment`         | The environment to be passed to a Docker container. Only used by the `docker` Task Type. E.g., JSON: `{"VAR_1": "abc"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                                                                           | Yes  | Yes | Yes  | Yes  |
| `dockerOptions`             | Additional options to be passed to the docker run command. Only used by the `docker` Task Type. E.g.,`["--runtime nvidia, "--gpus all"]`.                                                                                                  | Yes  | Yes | Yes  | Yes  |
| `dockerPassword`            | The password for the Docker container registry; only used by the `docker` Task Type. E,g., `"my_password"`.                                                                                                                                | Yes  | Yes | Yes  | Yes  |
| `dockerRegistry`            | The Docker container registry against which to run `docker login`. This can be omitted if using the DockerHub registry. E.g., `"my.registry.io"`.                                                                                          | Yes  | Yes | Yes  | Yes  |
| `dockerUsername`            | The username for the Docker container registry; only used by the `docker` Task Type. E,g., `"my_password"`.                                                                                                                                | Yes  | Yes | Yes  | Yes  |
| `environment`               | The environment variables to set for a Task when it's executed. E.g., JSON: `{"VAR_1": "abc", "VAR_2": "def"}`, TOML: `{VAR_1 = "abc", VAR_2 = "def"}`.                                                                                    | Yes  | Yes | Yes  | Yes  |
| `exclusiveWorkers`          | If true, then do not allow claimed Workers to be shared with other Task Groups; otherwise, Workers can be shared. Default:`false`.                                                                                                         | Yes  | Yes | Yes  |      |
| `executable`                | The 'executable' to run when using one of the task types `bash`, `cmd`, `powershell`, or `docker`. This is the filename of the script to run, or the container image for Docker. Optional: omit to suppress automatic processing.          | Yes  | Yes | Yes  | Yes  |
| `finishIfAllTasksFinished`  | If true, the Task Group will finish automatically if all contained tasks finish. Default:`true`.                                                                                                                                           | Yes  | Yes | Yes  |      |
| `finishIfAnyTaskFailed`     | If true, the Task Group will be failed automatically if any contained tasks fail. Default:`false`.                                                                                                                                         | Yes  | Yes | Yes  |      |
| `flattenInputPaths`         | Determines whether input object paths should be flattened (i.e., directory structure removed) when downloaded to a node. Default: `false`.                                                                                                 | Yes  | Yes | Yes  | Yes  |
| `flattenUploadPaths`        | Ignore local directory paths when uploading files to the Object Store; place in `<namespace>:<work-req-name>/`. Default: `false`.                                                                                                          | Yes  | Yes |      |      |
| `inputs`                    | The list of input files to be uploaded to the YellowDog Object Store, and required by the Task (implies `verifyAtStart`). E.g. `["a.sh", "b.sh"]` or `["*.sh"]`.                                                                           | Yes  | Yes | Yes  | Yes  |
| `inputsOptional`            | A list of input files required by a Task, but which are not subject to verification. Can contain wildcards. E.g.: `["task_group_1/**/results.txt"]`.                                                                                       | Yes  | Yes | Yes  | Yes  |
| `instanceTypes`             | The machine instance types that can be used to execute Tasks. E.g., `["t3.micro", "t3a.micro"]`.                                                                                                                                           | Yes  | Yes | Yes  |      |
| `maximumTaskRetries`        | The maximum number of times a Task can be retried after it has failed. E.g.: `5`.                                                                                                                                                          | Yes  | Yes | Yes  |      |
| `maxWorkers`                | The maximum number of Workers that can be claimed for the associated Task Group. E.g., `10`.                                                                                                                                               | Yes  | Yes | Yes  |      |
| `minWorkers`                | The minimum number of Workers that the associated Task Group will retain even if this exceeds the current number of Tasks. E.g., `1`.                                                                                                      | Yes  | Yes | Yes  |      |
| `name`                      | The name of the Work Requirement, Task Group or Task. E.g., `"wr_name"`. Note that the `name` property is not inherited.                                                                                                                   | Yes  | Yes | Yes  | Yes  |
| `namespaces`                | Only Workers whose Worker Pools match one of the namespaces in this list can be claimed by the Task Group. E.g., `["namespace_1", "namespace_2"]. Defaults to `None`.                                                                      | Yes  | Yes | Yes  |      |
| `outputs`                   | The files to be uploaded to the YellowDog Object Store by a Worker node on completion of the Task. E.g., `["results_1.txt", "results_2.txt"]`.                                                                                             | Yes  | Yes | Yes  | Yes  |
| `outputsOther`              | Files to be uploaded to the YellowDog Object Store from outside the Tasks's Working Directory by a Worker node on completion of a Task. E.g., `outputsOther = [{"directoryName" = "tmp", "filePattern" = "out.txt", "required" = false}]`. | Yes  | Yes | Yes  | Yes  |
| `outputsRequired`           | The files that *must* be uploaded to the YellowDog Object Store by a Worker node on completion of the Task. The Task will fail if any outputs are unavailable.                                                                             | Yes  | Yes | Yes  | Yes  |
| `parallelBatches`           | The number of parallel threads to use when uploading batches of Tasks.                                                                                                                                                                     | Yes  |     |      |      |
| `priority`                  | The priority of Work Requirements and Task Groups. Higher priority acquires Workers ahead of lower priority. E.g., `0.0`.                                                                                                                  | Yes  | Yes | Yes  |      |
| `providers`                 | Constrains the YellowDog Scheduler only to execute tasks from the associated Task Group on the specified providers. E.g., `["AWS", "GOOGLE"]`.                                                                                             | Yes  | Yes | Yes  |      |
| `ram`                       | Range constraint on GB of RAM that are required to execute Tasks. E.g., `[2.5, 4.0]`.                                                                                                                                                      | Yes  | Yes | Yes  |      |
| `regions`                   | Constrains the YellowDog Scheduler only to execute Tasks from the associated Task Group in the specified regions. E.g., `["eu-west-2]`.                                                                                                    | Yes  | Yes | Yes  |      |
| `setTaskNames`              | Set this to `false` to suppress automatic generation of Task names. Defaults to `true`. Task names that are set by the user will still be observed. Note that Task names must be set if any outputs are specified.                         | Yes  | Yes | Yes  | Yes  |
| `tag`                       | A tag that can be associated with a Work Requirement, Task Group or Task. Note there is **no property inheritance** for these tags.                                                                                                        | Yes  | Yes | Yes  | Yes  |
| `taskBatchSize`             | Determines the batch size used to add Tasks to Task Groups. Default is 2,000.                                                                                                                                                              | Yes  |     |      |      |
| `taskCount`                 | The number of times to execute the Task.                                                                                                                                                                                                   | Yes  | Yes | Yes  |      |
| `taskData`                  | The data to be passed to the Worker when the Task is started. E.g., `"mydata"`. Becomes file `taskdata.txt` in the Task's working directory when The Task executes.                                                                        | Yes  | Yes | Yes  | Yes  |
| `taskDataFile`              | Populate the `taskData` property above with the contents of the specified file. E.g., `"my_task_data_file.txt"`.                                                                                                                           | Yes  | Yes | Yes  | Yes  |
| `taskDataInputs`            | A list of data inputs to downloaded by the task E.g., JSON: `{"source": "src", "destination": "dest"}`, TOML: `{source = "src", destination = "dest"}`.                                                                                    | Yes  | Yes | Yes  | Yes  |
| `taskDataOutputs`           | A list of data outputs to be uploaded at the conclusion of a task E.g., JSON: `{"source": "src", "destination": "dest", "alwaysUpload": true}`, TOML: `{source = "src", destination = "dest", alwaysUpload = true}`.                       | Yes  | Yes | Yes  | Yes  |
| `taskName`                  | The name to use for the Task. Only usable in the TOML file. Mostly useful in conjunction with CSV Task data. E.g., `"my_task_number_{{task_number}}"`.                                                                                     | Yes  |     |      |      |
| `taskGroupCount`            | Create `taskGroupCount` duplicates of a single Task Group.                                                                                                                                                                                 | Yes  | Yes |      |      |
| `taskGroupName`             | The name to use for the Task Group. Only usable in the TOML file. E.g., `"my_tg_number_{{task_group_number}}"`.                                                                                                                            | Yes  |     |      |      |
| `taskTimeout`               | The timeout in minutes after which an executing Task will be terminated and reported as `FAILED`. E.g. `120.0`. The default is no timeout.                                                                                                 | Yes  | Yes | Yes  |      |
| `timeout`                   | As above, but set at the individual Task level, which overrides the group level `taskTimeout` property (if present).                                                                                                                       | Yes  |     |      | Yes  |
| `taskType`                  | The Task Type of a Task. E.g., `"docker"`.                                                                                                                                                                                                 | Yes  |     |      | Yes  |
| `taskTypes`                 | The list of Task Types required by the range of Tasks in a Task Group. E.g., `["docker", bash"]`.                                                                                                                                          |      | Yes | Yes  |      |
| `tasksPerWorker`            | Determines the number of Worker claims based on splitting the number of unfinished Tasks across Workers. E.g., `1`.                                                                                                                        | Yes  | Yes | Yes  |      |
| `uploadFiles`               | The list of files to be uploaded to the YellowDog Object Store. E.g., (JSON): `[{"localPath": file_1.txt", "uploadPath": "file_1.txt"}]`.                                                                                                  | Yes  | Yes | Yes  | Yes  |
| `uploadTaskProcessOutput`   | Whether the console output of a Task's process (in file 'taskoutput.txt') should be uploaded to the YellowDog Object Store on Task completion. Default: `false`.                                                                           | Yes  | Yes | Yes  | Yes  |
| `vcpus`                     | Range constraint on number of vCPUs that are required to execute Tasks E.g., `[2.0, 4.0]`.                                                                                                                                                 | Yes  | Yes | Yes  |      |
| `verifyAtStart`             | A list of files required by a Task. Must be present when the Task is ready to start or the Task will fail. E.g.: `["task_group_1/task_1/results.txt"]`.                                                                                    | Yes  | Yes | Yes  | Yes  |
| `verifyWait`                | A list of files required by a Task. The Task will wait until the files are available before starting. E.g.: `["task_group_1/task_1/results.txt"]`.                                                                                         | Yes  | Yes | Yes  | Yes  |
| `workerTags`                | The list of Worker Tags that will be used to match against the Worker Tag of a candidate Worker. E.g., `["tag_x", "tag_y"]`.                                                                                                               | Yes  | Yes | Yes  |      |
| `workRequirementData`       | The name of the file containing the JSON document in which the Work Requirement is defined. E.g., `"test_workreq.json"`.                                                                                                                   | Yes  |     |      |      |

## Automatic Properties

In addition to the property inheritance mechanism, some properties are set automatically by the `yd-submit` command, as a usage convenience if they're not explicitly specified.

### Work Requirement, Task Group and Task Naming

- The **Work Requirement** name is automatically set using a concatenation of the `tag` property, and a UTC timestamp: e.g.: `mytag_221024-15552480`.
- **Task Group** names are automatically created for any Task Group that is not explicitly named, using names of the form `task_group_1` (or `task_group_01`, etc., for larger numbers of Task Groups). Task Group numbers can also be included in user-defined Task Group names using the `{{task_group_number}}` variable substitution discussed below.
- **Task** names are automatically created for any Task that is not explicitly named, using names of the form `task_1` (or `task_01`, etc., for larger numbers of Tasks). The Task counter resets for each different Task Group. Task numbers can also be included in user-defined Task names using the `{{task_number}}` variable substitution discussed below. Automatic Task name generation can be suppressed by setting the `setTaskNames` property to `false`, in which case the `task_name` variable will be set to `none`. Note that Task names must be set for any tasks that specify outputs.

#### Obtaining Names/Context from Environment Variables at Task Run Time

When a Task executes, its Task name and number, Task Group name and number, Work Requirement name, Namespace, and Tag can be made automatically available to the Task in the following environment variables, if the `addYDEnvironmentVariables` property is set to `true`:

- `YD_TASK_NAME`
- `YD_TASK_NUMBER`
- `YD_NUM_TASKS` (Number of Tasks in this Task Group)
- `YD_TASK_GROUP_NAME`
- `YD_TASK_GROUP_NUMBER`
- `YD_NUM_TASK_GROUPS` (Number of Task Groups in the Work Requirement)
- `YD_WORK_REQUIREMENT_NAME`
- `YD_NAMESPACE`
- `YD_TAG` (if set at the Task level)

This applies whether the names were set automatically by `yd-submit` or explicitly by the user.

For Tasks of type `docker` **and** where the `executable` property has been set, the variables above are instead available **within** the container environment.

In addition to the environment variables above, when a Task is executed by a Worker, the YellowDog Agent will set the following variables for use by the Task, based on the instance details and Task identification:

- `YD_PROVIDER`
- `YD_REGION`
- `YD_INSTANCE_TYPE`
- `YD_INSTANCE_ID`
- `YD_TASK_GROUP_ID`
- `YD_TASK_ID`
- `YD_AGENT_DATA`
- `YD_AGENT_HOME`

### Task Types

- If `taskType` is set only at the TOML file level, then `taskTypes` is automatically populated for Task Groups, unless overridden.
- If `taskTypes` is set at the Task Group Level, and has only one Task Type entry, then `taskType` is automatically set at the Task Level using the single Task Type, unless overridden.
- If `taskType` is set at the Task level, then `taskTypes` is automatically populated for the Task Groups level using the accumulated Task Types from the Tasks included in each Task Group, unless already specified.

For the **`bash`**, **`powershell`**, **`cmd`**/**`bat`** and **`docker`** task types, some automatic processing will be performed if the **`executable`** property is set.

#### Bash, Python, PowerShell and cmd/bat Tasks

As a convenience, for the **`bash`**, **`python`**, **`powershell`**, and **`cmd`** (or **`bat`**) Task Types, the script nominated in the **`executable`** property is automatically added to the `inputs` file list if not already present in that list. This means the nominated 'executable' script file will be uploaded to the Object Store, and made a requirement of the Task when it runs.

Using a Bash Task as an example (in TOML form):

```toml
taskType = "bash"
executable = "my_bash_script.sh"
arguments = ["1", "2", "3"]
```
is equivalent to:

```toml
taskType = "bash"
inputs = ["my_bash_script.sh"]
arguments = ["{{wr_name}}/my_bash_script.sh", "1", "2", "3"]
```

In the case of Windows batch (`.bat`) files, a `/c` flag is prepended to the `cmd.exe` argument list to ensure correct execution behaviour. For example:

```toml
taskType = "cmd"  # or "bat"
executable = "my_script.bat"
arguments = ["1", "2", "3"]
```

is equivalent to:

```toml
taskType = "cmd"  # or "bat"
inputs = ["my_script.bat"]
arguments = ["/c", "{{wr_name}}\\my_script.bat", "1", "2", "3"]
```

Note the `\\` requirement for directory separators when defining Tasks on Windows hosts. Note also that the `/c` is required when running commands or batch scripts using `cmd.exe`, otherwise the `cmd.exe` process created to execute the Task will not terminate.

#### Docker Tasks

For the **`docker`** Task Type, the variables supplied in the `dockerEnvironment` property are unpacked into the argument list as `--env` entries, the Docker container name supplied in the `executable` property is then added to the arguments list, followed by the arguments supplied in the `arguments` property.

The `dockerUsername`, `dockerPassword`, and `dockerRegistry` properties, if supplied, are added to the `environment` property for processing by the script invoked by the Agent, which launches the Docker container. The `dockerRegistry` property is supplied when using a container repository other than DockerHub.

For example:
```toml
taskType = "docker"
executable = "my_dockerhub_repo/my_container_image"
dockerEnvironment = {E1 = "EeeOne"}
dockerUsername = "my_user"
dockerPassword = "my_password"
dockerRegistry = "my_registry.io"
arguments = ["1", "2", "3"]
```

is equivalent to the following being sent for processing by the `docker` Task Type, the YellowDog version of which will log in to the Docker repo (if required) then issue a `docker run` command with the arguments supplied:

```toml
taskType = "docker"
arguments = ["--env", "E1=EeeOne", "my_dockerhubrepo/my_container_image", "1", "2", "3"]
environment = {DOCKER_USERNAME = "my_user", DOCKER_PASSWORD = "my_password", DOCKER_REGISTRY = "my_registry.io"}
```

In addition, the `dockerOptions` property can be used to supply a list of arguments to the `docker run` command. For example:

```toml
taskType = "docker"
executable = "my_dockerhub_repo/my_container_image"
dockerOptions = ["--runtime=nvidia", "--gpus=all"]
arguments = ["1", "2", "3"]
```

is equivalent to the following being sent for processing by the `docker` Task Type:

```toml
taskType = "docker"
arguments = ["--runtime=nvidia", "--gpus=all", "my_dockerhubrepo/my_container_image", "1", "2", "3"]
```

#### Bash, Python, PowerShell, cmd.exe/batch, and Docker without Automatic Processing

If the `executable` property is not supplied, none of the automatic processing described above for `bash`, `python`, `powershell`, `cmd` (or `bat`) and `docker` task types is applied.

### Task and Task Group Counts

The `taskCount` property can be used to expand the number of Tasks within a Task Group, by creating duplicates of a single Task; this can be handy for testing and demos. In JSON specifications, there must be zero or one Task(s) listed within each Task Group or `taskCount` is ignored. This property can also be set on the command line using the `--task-count`/`-C` option of `yd-submit` followed by the required number of Tasks.

Also useful for testing, the `taskGroupCount` property or the command line option `--task-group-count`/`-G` can be set to expand the number of Task Groups in the Work Requirement, by creating duplicates of a single Task Group. If used, the `taskCount` property will apply to every Task Group, i.e., the total number of tasks is the multiple of `taskGroupCount` and `taskGroup`.

## Examples

### TOML Properties in the `workRequirement` Section

Here's an example of the `workRequirement` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workRequirement]
    addYDEnvironmentVariables = true
    alwaysUpload = true
    arguments = ["1", "TWO"]
    completedTaskTtl = 10
    csvFile = "file1.csv"
    csvFiles = ["file1.csv", "file3.csv:3"]
    dockerEnvironment = {MY_DOCKER_VAR = 100}
    dockerPassword = "myPassword"
    dockerRegistry = "my.registry.io"
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
    inputsOptional = ["optional.txt"]
    instanceTypes = ["t3a.micro", "t3.micro"]
    namespaces = ["namespace_1", "namespace_2"]
    maxWorkers = 1
    maximumTaskRetries = 0
    minWorkers = 1
    name = "my-work-requirement"
    outputs = ["results.txt"]
    outputsOther = [{"directoryName" = "my_output_dir", "filePattern" = "out.txt", "required" = true}]
    outputsRequired = ["results_required.txt"]
    parallelBatches = 5
    priority = 0.0
    providers = ["AWS"]
    ram = [0.5, 2.0]
    regions = ["eu-west-2"]
    setTaskNames = false
    tag = "my_tag"
    taskBatchSize = 1000
    taskCount = 100
    taskData = "my_data_string"
    taskDataFile = "my_data_file.txt"
    taskDataInputs = [
      {source = "in_src_path_1", destination = "dest_path_1"},
      {source = "in_src_path_2", destination = "dest_path_2"},
    ]
    taskDataOutputs = [
        {source = "out_src_path_1", destination = "dest_path_1", alwaysUpload = true},
        {source = "out_src_path_2", destination = "dest_path_2", alwaysUpload = false},
    ]
    taskName = "my_task_number_{{task_number}}"
    taskGroupCount = 5
    taskGroupName = "my_task_group_number_{{task_group_number}}"
    taskTimeout = 120.0
    taskType = "docker"
    tasksPerWorker = 1
    uploadFiles = [{localPath = "file_1.txt", uploadPath = "file_1.txt"}]
    uploadTaskProcessOutput = true
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
  "addYDEnvironmentVariables": true,
  "alwaysUpload": true,
  "arguments": [1, "TWO"],
  "completedTaskTtl": 10,
  "dockerEnvironment": {"MY_DOCKER_VAR": 100},
  "dockerPassword": "myPassword",
  "dockerRegistry": "my.registry.io",
  "dockerUsername": "myUsername",
  "environment": {"MY_VAR": 100},
  "exclusiveWorkers": false,
  "executable": "my-container",
  "finishIfAllTasksFinished": true,
  "finishIfAnyTaskFailed": false,
  "flattenInputPaths": false,
  "flattenUploadPaths": false,
  "inputs": ["app/main.py", "app/requirements.txt"],
  "inputsOptional": ["optional.txt"],
  "instanceTypes": ["t3a.micro", "t3.micro"],
  "maxWorkers": 1,
  "maximumTaskRetries": 0,
  "minWorkers": 1,
  "name": "my-work-requirement",
  "namespaces": ["namespace_1", "namespace_2"],
  "outputs": ["results.txt"],
  "outputsOther": [{"directoryName": "my_output_dir", "filePattern": "out.txt", "required": true}],
  "outputsRequired": ["results_required.txt"],
  "priority": 0.0,
  "providers": ["AWS"],
  "ram": [0.5, 2],
  "regions": ["eu-west-2"],
  "setTaskNames": false,
  "tag": "my_tag"
  "taskCount": 100,
  "taskData": "my_task_data_string",
  "taskDataFile": "my_data_file.txt",
  "taskDataInputs": [
    {"destination": "dest_path_1", "source": "in_src_path_1"},
    {"destination": "dest_path_2", "source": "in_src_path_2"}
  ],
  "taskDataOutputs": [
    {"alwaysUpload": true, "destination": "dest_path_1", "source": "out_src_path_1"},
    {"alwaysUpload": false, "destination": "dest_path_2", "source": "out_src_path_2"}
  ],
  "taskGroupCount": 5,
  "taskTimeout": 120.0,
  "taskTypes": ["docker"],
  "tasksPerWorker": 1,
  "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
  "uploadTaskProcessOutput": true,
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
      "addYDEnvironmentVariables": true,
      "alwaysUpload": true,
      "arguments": [1, "TWO"],
      "completedTaskTtl": 10,
      "dockerEnvironment": {"MY_DOCKER_VAR": 100},
      "dockerPassword": "myPassword",
      "dockerRegistry": "my.registry.io",
      "dockerUsername": "myUsername",
      "environment": {"MY_VAR": 100},
      "exclusiveWorkers": false,
      "executable": "my-container",
      "finishIfAllTasksFinished": true,
      "finishIfAnyTaskFailed": false,
      "flattenInputPaths": false,
      "inputs": ["app/main.py", "app/requirements.txt"],
      "inputsOptional": ["optional.txt"],
      "instanceTypes": ["t3a.micro", "t3.micro"],
      "maximumTaskRetries": 0,
      "maxWorkers": 1,
      "minWorkers": 1,
      "name": "first-task-group",
      "namespaces": ["namespace_1", "namespace_2"],
      "outputs": ["results.txt"],
      "outputsOther": [{"directoryName": "my_output_dir", "filePattern": "out.txt", "required": true}],
      "outputsRequired": ["results_required.txt"],
      "priority": 0.0,
      "providers": ["AWS"],
      "ram": [0.5, 2],
      "regions": ["eu-west-2"],
      "setTaskNames": false,
      "tag": "my_tag",
      "taskCount": 5,
      "taskData": "my_task_data_string",
      "taskDataFile": "my_data_file.txt",
      "taskDataInputs": [
        {"destination": "dest_path_1", "source": "in_src_path_1"},
        {"destination": "dest_path_2", "source": "in_src_path_2"}
      ],
      "taskDataOutputs": [
        {"alwaysUpload": true, "destination": "dest_path_1", "source": "out_src_path_1"},
        {"alwaysUpload": false, "destination": "dest_path_2", "source": "out_src_path_2"}
      ],
      "taskTimeout": 120.0,
      "taskTypes": ["docker"],
      "tasksPerWorker": 1,
      "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
      "uploadTaskProcessOutput": true,
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
          "addYDEnvironmentVariables": true,
          "alwaysUpload": true,
          "arguments": [1, 2],
          "dockerEnvironment": {"MY_DOCKER_VAR": 100},
          "dockerPassword": "myPassword",
          "dockerRegistry": "my.registry.io",
          "dockerUsername": "myUsername",
          "environment": {"MY_VAR": 100},
          "executable": "my-container",
          "flattenInputPaths": false,
          "inputs": ["app/main.py", "app/requirements.txt"],
          "inputsOptional": ["optional.txt"],
          "name": "my-task",
          "outputs": ["results.txt"],
          "outputsOther": [{"directoryName": "my_output_dir", "filePattern": "out.txt", "required": true}],
          "outputsRequired": ["results_required.txt"],
          "setTaskNames": false,
          "tag": "my_tag",
          "taskData": "my_task_data_string",
          "taskDataFile": "my_data_file.txt",
          "taskDataInputs": [
            {"destination": "dest_path_1", "source": "in_src_path_1"},
            {"destination": "dest_path_2", "source": "in_src_path_2"}
          ],
          "taskDataOutputs": [
            {"alwaysUpload": true, "destination": "dest_path_1", "source": "out_src_path_1"},
            {"alwaysUpload": false, "destination": "dest_path_2", "source": "out_src_path_2"}
          ],
          "timeout": 120.0,
          "taskType": "docker",
          "uploadFiles": [{"localPath": "file_1.txt", "uploadPath": "file_1.txt"}],
          "uploadTaskProcessOutput": true,
          "verifyAtStart": ["ready_results.txt"],
          "verifyWait": ["wait_for_results.txt"]
        }
      ]
    }
  ]
}
```

## Variable Substitutions in Work Requirement Properties

Variable substitutions can be used within any property value in TOML configuration files or Work Requirement JSON files. See the description [above](#variable-substitutions) for more details on variable substitutions. This is a powerful feature that allows Work Requirements to be parameterised by supplying values on the command line, via environment variables or via the TOML file.

### Work Requirement Name Substitution

The name of the Work Requirement itself can be used via the variable substitution `{{wr_name}}`. This can be used anywhere in the `workRequirement` section of the TOML configuration file, or in JSON Work Requirement definitions

### Task and Task Group Name Substitutions

The following naming and numbering substitutions are available for use in TOML and JSON Work Requirement specifications, along with the context(s) in which each variable can be used. The variables can be used within the value of any property.

| Directive               | Description                                       | Task | Task Group |
|:------------------------|:--------------------------------------------------|:-----|:-----------|
| `{{task_number}}`       | The current Task number                           | Yes  |            |
| `{{task_name}}`         | The current Task name                             | Yes  |            |
| `{{task_group_name}}`   | The current Task Group name                       | Yes  | Yes        |
| `{{task_count}}`        | The number of Tasks in the current Task Group     | Yes  | Yes        |
| `{{task_group_number}}` | The current Task Group number                     | Yes  | Yes        |
| `{{task_group_count}}`  | The number of Task Groups in the Work Requirement | Yes  | Yes        |

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

To examine the JSON that will actually be sent to the YellowDog API after all processing, use the `--dry-run` (`-D`) command line option when running `yd-submit`. This will print the fully processed JSON for the Work Requirement. Nothing will be submitted to the Platform.

A dry-run is useful for inspecting the results of all the processing that's been performed. To suppress all output except for the JSON itself, add the `--quiet` (`-q`) command line option.

Note that the generated JSON is a consolidated form of what would be submitted to the YellowDog API, and Tasks are presented directly within their Task Groups for ease of comprehension. In actual API submissions, the Work Requirement with zero or more Task Groups is submitted first, and Tasks are then added to their Task Groups separately, in subsequent API calls. Task Groups and Tasks can also later be added to the Work Requirement.

A simple example of the JSON output is shown below, showing a Work Requirement with a single Task Group, containing a single Task.

`% yd-submit --dry-run --quiet`
```json
{
  "name": "pyex-bash-pwt2_240424-12051160",
  "namespace": "pyexamples-pwt2",
  "priority": 0,
  "tag": "pyex-bash-pwt2",
  "taskGroups": [
    {
      "finishIfAllTasksFinished": true,
      "finishIfAnyTaskFailed": false,
      "name": "task_group_1",
      "priority": 0,
      "runSpecification": {
        "maximumTaskRetries": 5,
        "taskTypes": ["bash"],
        "workerTags": ["pyex-bash-pwt2-worker", "onpremise-pwt2"]
      },
      "starved": false,
      "waitingOnDependency": false,
      "tasks": [
        {
          "arguments": ["pyex-bash-pwt2_240424-12051160/sleep_script.sh", 1, 2, 3],
          "environment": {
            "TEST_ENV_1": "100",
            "TEST_ENV_2": "200",
            "YD_TASK_NAME": "task_1",
            "YD_TASK_NUMBER": "1",
            "YD_TASK_GROUP_NAME": "task_group_1",
            "YD_TASK_GROUP_NUMBER": "1",
            "YD_WORK_REQUIREMENT_NAME": "pyex-bash-pwt2_240424-12051160",
            "YD_NAMESPACE": "pyexamples-pwt2"
          },
          "inputs": [
            {
              "objectNamePattern": "pyex-bash-pwt2_240424-12051160/sleep_script.sh",
              "source": "TASK_NAMESPACE",
              "verification": "VERIFY_AT_START"
            }
          ],
          "name": "task_1",
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

Note that variable substitutions **can** be used in the raw JSON file, just as in the other Work Requirement JSON examples, but there is no property inheritance, including from the `[workRequirement]` section of the TOML configuration or from Work Requirement properties supplied on the command line.

There is also no automatic file upload when using this option, so any files required at the start of the task (specified using `VERIFY_AT_START` in the `inputs` property) must be present before the Tasks are uploaded, or the Tasks will fail immediately. The `yd-upload` command can be used to upload these files, and `yd-submit` will pause for user confirmation to allow this upload to happen.

## File Storage Locations and File Usage

This section discusses how to upload files from local storage to the YellowDog Object Store, how those files are transferred to Worker Nodes for Task processing, how the results of Task processing are returned by Worker Nodes, and how files are transferred back from the YellowDog Object Store to local storage.

### Files Uploaded to the Object Store from Local Storage

#### Files in the `inputs` List

When a Work Requirement is submitted using `yd-submit`, files are uploaded to the YellowDog Object Store if they're included in the list of files in the `inputs` property. (For the **`bash`**, **`python`**, **`powershell`**, and **`cmd`** (or **`bat`**) Task Types, the file specified in the `executable` property is also automatically uploaded, as a convenience, even if not included in the `inputs` list.)

The `inputs` property accepts wildcard filenames, e.g.: `["*.sh", "*.txt"]`. This can be used to add the contents of directories, e.g.: `["my_dir/*", "data*/*"]`.

Files are uploaded to the Namespace specified in the configuration. Within the Namespace, each Work Requirement has a separate folder that shares the name of the Work Requirement, and in which all files related to the Work Requirement are stored.

1. Files to be uploaded that are in the **same directory as the Work Requirement specification** (the TOML or JSON file) are uploaded to the root of the Work Requirement folder.


2. Files to be uploaded that are in **subdirectories below the Work Requirement specification, or where absolute pathnames are supplied** are placed in the Object Store in directories that mirror their local storage locations.


3. Files to be uploaded that are in **directories relative to the Work Requirement specification, using `..` relative paths** are placed in Object Store directories in which the `..` parts of the pathname are replaced with an integer count of the number of `..` entries (because we can't use the `..` relative form in the Object Store).

Assuming a Namespace called `development` and a Work Requirement named `testrun_221108-120404-7d2`, the following locations are used when uploading files following the patterns above:

```shell
"inputs" : ["file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
"inputs" : ["dev/file_1.txt"] -> development::testrun_221108-120404-7d2/dev/file_1.txt
"inputs" : ["/home/dev/file_1.txt"] -> development::testrun_221108-120404-7d2/home/dev/file_1.txt
"inputs" : ["../dev/file_1.txt"] -> development::testrun_221108-120404-7d2/1/dev/file_1.txt
"inputs" : ["../../dev/file_1.txt"] -> development::testrun_221108-120404-7d2/2/dev/file_1.txt
```

**Using `flattenUploadPaths`**

The `flattenUploadPaths` property can be used to suppress the mirroring of any local directory structure when uploading files to the Object Store. If set to `true`, all files will be uploaded to the root of the Work Requirement folder. For example:

```shell
"inputs" : ["file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
"inputs" : ["dev/file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
"inputs" : ["/home/dev/file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
"inputs" : ["../dev/file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
"inputs" : ["../../dev/file_1.txt"] -> development::testrun_221108-120404-7d2/file_1.txt
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

When running the Python Examples commands on **Windows** hosts, note that either Windows or Unix directory separators can be used for the `localPath` pathnames (or the pathnames in `inputs`), but the Unix convention must be used for the `uploadPath` names, e.g.:

```toml
uploadFiles = [
    {localPath = "dir_2\\file_2.txt", uploadPath = "::my_directory/file_2.txt"},
]
```

The `uploadFiles` property can also be set at the Work Requirement and Task Group levels, and property inheritance operates as normal.

For `uploadPath`, the same `::` naming convention is available as is used in the `verifyAtStart`, `verifyWait` and `inputsOptional` properties discussed below:

- If `::` is not used, then the file is uploaded relative to the current namespace in a directory named after the name of the Work Requirement
- If `::` is used at the start of the `uploadPath`, the file is uploaded relative to the root of the current namespace
- If `<namespace>::` is used at the start of `uploadPath`, the file is uploaded relative to the root of `<namespace>`

Each file specified in the `uploadFiles` lists will only be uploaded once to each unique upload location for any given invocation of `yd-submit`.

If a file in the `uploadFiles` list is required by a Task, it must separately be added to the `verifyAtStart` or `verifyWait` lists discussed below. This is not done automatically. Note also that the `flattenUploadPaths` property is ignored for files in the `uploadFiles` list.

#### Using Wildcards in the `uploadFiles` List

File and directory name wildcards can be used in `localPath` properties. If wildcards are used, then the `uploadPath` property must end with a `*`, which will be replaced with the name of each file that matches the wildcard, e.g.:

```toml
uploadFiles = [
    {localPath = "*.sh", uploadPath = "scripts/*"},
    {localPath = "text/*.txt", uploadPath = "::top-level/*"},
    {localPath = "src/*.py", uploadPath = "other-namespace::*"},
]
```

The `--dry-run` (`-D`) option can be used with `yd-submit` to print out the files that would be uploaded, along with their upload locations. 

### File Dependencies Using `verifyAtStart` and `verifyWait`

It's possible to make Tasks dependent on the presence of files in the Object Store by using the `verifyAtStart` and `verifyWait` lists. These files are not automatically uploaded when using `yd-submit` so are uploaded manually (e.g., by using `yd-upload`), uploaded using the `uploadFiles` property, or are created as outputs from the execution of other Tasks.

Note that a given file can only appear in *one* of the `inputs`, `verifyAtStart` or `verifyWait` lists.

Tasks with `verifyAtStart` dependencies will fail immediately if the required files are not present when the Task is submitted. Tasks with `verifyWait` dependencies will not become `READY` to be allocated to Workers until their dependencies are satisfied.

When specifying files in the `verifyAtStart` and `verifyWait` lists, as with the `uploadPath` property discussed above, the file locations can be (1) relative to the Work Requirement name in the current namespace (the default), (2) relative to the root of the current namespace, or (3) relative to the root of a different namespace in the user's Account.

1. For files relative to the Work Requirement name in the current namespace, just use the file path, e.g.
```shell
"verifyWait": ["file_1.txt"] -> development:testrun_221108-120404-7d2/file_1.txt
```

2. For files relative to the root of the current namespace, prefix the file path with `::`, e.g.
```shell
"verifyWait": ["::file_1.txt"] -> development::file_1.txt
```

3. For files relative to the root of a different namespace, prefix the file path with the namespace name and `::`, e.g.
```shell
"verifyWait": ["other_namespace::file_1.txt"] -> other_namespace::file_1.txt
```

The use of the three different forms can be mixed within a single list, e.g.:
```shell
"verifyAtStart": ["file_1.txt", "::dir_2/file_2.txt", "other_namespace::dir_3/file_3.txt"]
```

### Files Uploaded to the Object Store Using `inputsOptional`

The `inputsOptional` property works in a similar fashion to the `verify*` properties above, but the files specified in this list are optional. This property also allows for the use of wildcards `*` and `**` to collect files using wildcard paths. The **ant** conventions are used for these wildcards.

### Files Downloaded to a Node for use in Task Execution

When a Task is executed by a Worker on a Node, its required files are downloaded from the Object Store prior to Task execution. Any file listed in the `inputs` for a Task is assumed to be required, along with any additional files specified in the `verifyAtStart` and `verifyWait` lists. Files specified using the `inputsOptional` property are optionally downloaded from the Object Store. (Note that a file should only appear in one of these four lists, otherwise `yd-submit` will return an error.)

When a Task is started by the Agent, its working directory has a pattern like:

`/var/opt/yellowdog/agent/data/workers/ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1`

Where `ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1` is an ephemeral directory that is removed after the Task finishes (or fails) and any nominated Task outputs have been uploaded to the Object Store.

Files that are downloaded by the Agent prior to Task execution are located as follows:

1. If the `flattenInputPaths` property is set to the default of `false` for the Task, the downloaded objects are placed in subdirectories that mirror those in the Object Store, including the Work Requirement name, situated beneath the working directory.


2. If the `flattenInputPaths` property is set to `true` for the Task, the downloaded objects are all placed directly in root of the Task's working directory.

For example:

```shell
If the required object is: development::testrun_221108-120404-7d2/dev/file_1.txt

then, if flattenInputPaths is false, the file will be found at:
 -> <working_directory>/testrun_221108-120404-7d2/dev/file_1.txt
 
else, if flattenInputPaths is true, the file will be found at:
 -> <working_directory>/file_1.txt 
 
where <working_directory> is:
  /var/opt/yellowdog/agent/data/workers/ydid_task_D0D0D0_68f5e5be-dc93-49eb-a824-1fcdb52f9195_1_1/
```

Note that the Work Requirement name is automatically made available to the Task via the environment variable `YD_WORK_REQUIREMENT_NAME`, by `yd-submit`, if the `addYDEnvironmentVariables` property is set to `true`. It's also available for client-side variable substitution in Work Requirements using the variable `{{wr_name}}`.

### Files Uploaded from a Node to the Object Store after Task Execution

After Task completion, the Agent will upload the specified output files to the Object Store. The files to be uploaded are those listed in the `outputs`, `outputsRequired`, and `outputsOther` properties for the Task.

In addition, the console output of the Task is captured in a file called `taskoutput.txt` in the root of the Task's working directory. Whether the `taskoutput.txt` file is uploaded to the Object Store is determined by the `uploadTaskProcessOutput` property for the Task, and this is set to 'false' by default.

If Task outputs are created in subdirectories below the Task's working directory, include the directories for files in the `outputs` property. E.g., if a Task creates files `results/openfoam.tar.gz` and `results/openfoam.log`, then specify these for upload in the `outputs` property as follows:

`"outputs": ["results/openfoam.tar.gz", "results/openfoam.log"]`

When output files are uploaded to the Object Store, they are placed in a Task Group and Task specific directory. So, if the Namespace is `development`, the Work Requirement is `testrun_221108-120404-7d2`, the Task Group is `task_group_1` and the Task is `task_1`, then the files above would be uploaded to the Object Store as follows:

```shell
development::testrun_221108-120404-7d2/task_group_1/task_1/results/openfoam.tar.gz
development::testrun_221108-120404-7d2/task_group_1/task_1/results/openfoam.log
development::testrun_221108-120404-7d2/task_group_1/task_1/taskoutput.txt
```

The **`outputsRequired`** property can be used instead of (or in addition to) the `outputs` property, if the output file(s) **must** be available for upload to the Object Store at the conclusion of the Task or the Task will be marked as `Failed`, e.g.:

`"outputsRequired": ["results/process_output.txt"]`

The **`outputsOther`** property is used to collect outputs from directories that are not contained under the Task's working directory. In this case, the YellowDog Agent must be explicitly configured to allow upload from these directories by establishing this in the `application.yaml` file. For example:

```yaml
yda.outputSources:
  - name: "my_output_dir"
    path: "/tmp/outputs"
```

Then, in the list of entries in the `outputsOther` property, the `directoryName` property is set to be the **`name`** specified in the `application.yaml`. For example:

```json
"outputsOther": [{"directoryName": "my_output_dir", "filePattern": "out.txt", "required": true}]
```

### Files Downloaded from the Object Store to Local Storage

The `yd-download` command can download all objects from the Object Store to a local directory, on a per Work Requirement basis (including any files that have been uploaded). A local directory is created with the same name as the Namespace and containing the Work Requirement directories.

Use the `--interactive` option with `yd-download` to select which Work Requirement(s) to download.

For the example above, `yd-download` would create a directory called `testrun_221108-120404-7d2` in the current working directory, containing something like:

```shell
current_directory
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

Note that everything within the `namespace::work-requirement` directory in the Object Store is downloaded, including any files that were specified in `inputs` and uploaded as part of the Work Requirement submission. Multiple Task Groups, and multiple Tasks will all appear in the directory structure.

Finer-grained downloads are also possible: please consult the output of `yd-download --help` to see the available options. For example to download only the `openfoam.tar.gz` file, to a local directory `results`:

```shell
yd-download testrun_221108-120404-7d2/task_group_1/task_1/results/openfoam.tar.gz --directory ./results
```

## Task Execution Context

This section discusses the context within which a Task operates when it's executed by a Worker on a node. It applies specifically to the YellowDog Agent running on a Linux node, and configured using the default username, directories, etc. Configurations can vary.

### Task Execution Steps

When a Task is allocated to a Worker on a node by the YellowDog Scheduler, the following steps are followed:

1. The Agent running on the node downloads the Task's properties: its `taskType`,  `arguments`, `environment`, `taskdata`, and (from the Object Store) any files in the `inputs` list and any available files in the `inputsOptional` list. A number of `YD_` environment variables are also automatically set by a combination (optionally) of `yd_submit`, and the Agent itself -- see above for details.
2. The downloaded files are placed in an ephemeral directory created for this Task's execution, and into which any output files are also written by default.
2. The Agent runs the command specified for the `taskType` in the Agent's `application.yaml` configuration file. This done as a simple `exec` of a subprocess to run the Task.
3. When the Task concludes, the Agent uses the exit code of the subprocess to report success (zero) or failure (non-zero).
4. The Agent then gathers any files in the `outputs` and `outputsRequired` lists and uploads them to the Object Store. If a file in the `outputsRequired` list is not found, the Task will be reported as failed. The Agent will also optionally upload the console output (including both `stdout` and `stderr`) of the Task, contained in the `taskoutput.txt` file.
5. The ephemeral Task directory is then deleted.

Note that if a Task is aborted during execution, the Task's subprocess is sent a `SIGTERM`, allowing the Task an opportunity to terminate any child processes or other resources (e.g., containers) that may have been started as part of Task execution. In addition, there is the option to set an `abort` clause as part of the Task Type specification in the Agent's `application.yaml` file, in which case the script specified in the `abort` clause takes over responsibility for any abort handling.

Once the steps above have been completed, the Worker is ready to accept its next Task from the YellowDog scheduler.

Note that if the Agent on a node advertises multiple Workers, then Tasks are executed in parallel on the node and can start and stop independently.

### The User and Group used for Tasks

By default, in the standard YellowDog Agent VM images and in images/instances created using the [YellowDog Agent Installer Script](https://github.com/yellowdog/resources/blob/main/agent-install/linux/README.md), the Agent runs as user and group `yd-agent`, and hence Tasks also execute under this user.

`yd-agent` does not have `sudo` privileges as standard, but this can be added if required at instance boot time via the `userData` property of a provisioning request. E.g. (for Ubuntu):

```shell
usermod -aG wheel yd-agent
echo -e "yd-agent\tALL=(ALL)\tNOPASSWD: ALL" > /etc/sudoers.d/020-yd-agent
```

### Home Directory for `yd-agent`

By default, the home directory of the `yd-agent` user is `/opt/yellowdog/agent`. This directory typically contains the `application.yaml` file used to configure the Agent, as well as any scripts that are used to execute the Task Types that the node supports.

If one wants to SSH to an instance as user `yd-agent`, perhaps for debugging purposes, SSH keys can be inserted via instance `userData`, e.g.:

```shell
YDA_HOME=/opt/yellowdog/agent
mkdir -p $YDA_HOME/.ssh
chmod og-rwx $YDA_HOME/.ssh
cat >> $YDA_HOME/.ssh/authorized_keys << EOF
<<Insert_Public_key_Here>>
EOF
chmod og-rw $YDA_HOME/.ssh/authorized_keys
chown -R yd-agent:yd-agent $YDA_HOME/.ssh
```

### Task Execution Directory

Ephemeral Task working directories are by default created under `/var/opt/yellowdog/agent/data/workers`, named using their YellowDog Task IDs with colons substituted by underscores.

(On Windows hosts, the Task directories are found under `%AppData%\yellowdog\agent\data\workers`.)

When a Task is allocated to a node, an ephemeral directory is created, e.g.:

`/var/opt/yellowdog/agent/data/workers/ydid_task_559EBE_74949336-ac2b-4811-a7d5-f3ecd9739908_1_1`

This is the directory into which downloaded objects are placed, and in which output files are created by default. The console output file, `taskoutput.txt`, containing stderr and stdout output will also be created in this directory.

See the [Files Downloaded to a Node](#files-downloaded-to-a-node-for-use-in-task-execution) section above for more details on how files in this directory are handled.

At the conclusion of the Task, after any files requested for upload have been uploaded to the Object Store (see the [Files Uploaded from a Node](#files-uploaded-from-a-node-to-the-object-store-after-task-execution) section for more information), the `ydid_task_559EBE_74949336-ac2b-4811-a7d5-f3ecd9739908_1_1` will be removed.

## Specifying Work Requirements using CSV Data

CSV data files can be used to drive the generation of lists of Tasks, as follows:

- A **prototype** Task specification is created within a JSON Work Requirement specification or in the `workRequirement` section of the TOML configuration file
- The prototype task includes one or more variable substitutions
- A CSV file is created, with the **headers** (first row) matching the names of the variable substitutions in the Task prototype
- Each subsequent row of the CSV file represents a new Task to be built using the prototype, with the variables substituted by the values in the row
- A Task will be created for each row of data

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

If these files are processed using `yd-submit wr.json -V wr_data.csv`, the following expanded list of three Tasks will be created prior to further processing by the `yd-submit` script:

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

### CSV Variable Substitutions

When the CSV file data is processed, the only substitutions made are those which match the variable substitutions in the prototype Task. The CSV file is the **only** source of substitutions used for this processing phase; all other variable substitutions (supplied on the command line, in the TOML configuration file, or from environment variables) are ignored -- i.e., they do not override the contents of the CSV file.

All variable substitutions unrelated to the CSV file data are left unchanged, for subsequent processing by `yd-submit`.

If the value to be inserted is a number (an integer or floating point value) or Boolean, the `{{num:my_number_var}}` and `{{bool:my_boolean_var}}` forms can be used in the JSON file, as with their use in other parts of the JSON Work Requirement specification. The substituted value will assume the nominated type rather than being a string. (The `array:` and `table:` prefixes are not currently supported for CSV substitutions.)

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
yd-submit wr.json -V wr_data_task_group_1.csv -V wr_data_task_group_2.csv
```

If there are **fewer** CSV files than Task Groups a warning will be printed and, if there are 'n' CSV files, CSV data processing will be applied to the first 'n' Task Groups in the Work Requirement by default, in the order in which the CSV files were supplied. If there are **more** CSV files than Task Groups, an error will be raised and processing will stop.

It is possible to apply CSV files explicitly to specific Task Groups, by using an optional **index postfix** (e.g., `:2`) at the end of each CSV filename. For example, if there are two CSV files to be applied to the second and fourth Task Groups in a JSON Work Requirement, use the following syntax:

```shell
yd-submit wr.json -V wr_data_task_group_2.csv:2 -V wr_data_task_group_4.csv:4
```

Alternatively, the **Task Group name** (if supplied in the JSON file) can be used as the postfix. For example, if the Task Groups above are named `tg_two` and `tg_four`, the `yd-submit` command would become:

```shell
yd-submit wr.json -V wr_data_task_group_2.csv:tg_two -V wr_data_task_group_4.csv:tg_four
```

Note that only one CSV file can be applied to any given Task Group. A single CSV file can, however, be reused for multiple Task Groups.

### Using CSV Data with Simple, TOML-Only Work Requirement Specifications

It's possible to use TOML exclusively to derive a list of Tasks from CSV data -- i.e., a JSON Work Requirement specification is not required.

To make use of this:

1. Ensure that no JSON Work Requirement document is specified (no `workRequirementData` in the TOML file, or no positional argument on the command line)
2. Insert the required CSV-supplied variable substitutions directly into the TOML properties, e.g. `arguments = ["{{arg_1}}", "{{arg_2}}"]`
3. Specify a single CSV file in the `csvFiles` TOML property, e.g. `csvFiles = ["wr_data.csv"]`, or provide the CSV file on the command line `-V wr_data.csv`

When `yd-submit` is run, it will expand the Task list to match the number of data rows in the CSV file.

### Inspecting the Results of CSV Variable Substitution

The `--process-csv-only` (or `-p`) option can be used with `yd-submit` to output the JSON Work Requirement after CSV variable substitutions only, prior to all other substitutions and property inheritance applied by `yd-submit`.

# Worker Pool Properties

The `workerPool` section of the TOML file defines the properties of the Worker Pool to be created, and is used by the `yd-provision` command. A subset of the properties is also used by the `yd-instantiate` command, for creating standalone Compute Requirements that are not associated with Worker Pools. Note that `computeRequirement` may be used as a synonym for `workerPool`, and the two may be used simultaneously in the same TOML file provided that their contained properties are not duplicated.

The only mandatory property is `templateId`. All other properties have defaults (or are not required). 
The `templateId` property can use either the YellowDog ID ('YDID') for the Compute Requirement Template, or its name.

The following properties are available:

| Property                  | Description                                                                                                          | Default                 |
|:--------------------------|:---------------------------------------------------------------------------------------------------------------------|:------------------------|
| `idleNodeTimeout`         | The timeout in minutes after which an idle node will be shut down. Set this to `0` to disable the timeout.           | `5.0`                   |
| `idlePoolTimeout`         | The timeout in minutes after which an idle Worker Pool will be shut down. Set this to `0` to disable the timeout.    | `30.0`                  |
| `imagesId`                | The image ID, Image Family ID, or Image Family name to use when booting instances.                                   |                         |
| `instanceTags`            | The dictionary of instance tags to apply to the instances. Tag names must be lower case.                             |                         |
| `maintainInstanceCount`   | Only used when instantiating Compute Requirements; attempt to maintain the requested number of instances.            | `False`                 |
| `maxNodes`                | The maximum number of nodes to which the Worker Pool can be scaled up.                                               | `1`                     |
| `metricsEnabled`          | Whether to enable performance metrics for nodes in the Worker Pool                                                   | `false`                 |
| `minNodes`                | The minimum number of nodes to which the Worker Pool can be scaled down.                                             | `0`                     |
| `name`                    | The name of the Worker Pool.                                                                                         | Automatically Generated |
| `nodeBootTimeout`         | The time in minutes allowed for a node to boot and register with the platform, otherwise it will be terminated.      | `10.0`                  |
| `requirementTag`          | The tag to apply to the Compute Requirement.                                                                         | `tag` set in `common`   |
| `targetInstanceCount`     | The initial number of nodes to create in the Worker Pool.                                                            | `1`                     |
| `templateId`              | The YellowDog Compute Requirement Template ID or name to use for provisioning. (**Required**)                        | No default provided     |
| `userData`                | User Data to be supplied to instances on boot.                                                                       |                         |
| `userDataFile`            | As above, but read the User Data from the filename supplied in this property.                                        |                         |
| `userDataFiles`           | As above, but create the User Data by concatenating the contents of the list of filenames supplied in this property. |                         |
| `workerPoolData`          | The name of a file containing a JSON specification of a Worker Pool.                                                 |                         |
| `workerTag`               | The Worker Tag to publish for the each of the Workers on the node(s).                                                |                         |
| `workersPerNode`          | The number of Workers to establish on each node in the Worker Pool.                                                  | `1`                     |
| `workersPerVCPU`          | The number of Workers to establish per vCPU on each node in the Worker Pool. (Overrides `workersPerNode`.)           |                         |

## Using Textual Names instead of IDs for Compute Requirement Templates and Image Families

The `templateId` property can be directly populated with the YellowDog ID (YDID), or it can be populated with the textual name of the template, in the form `namespace/template_name`.

Similarly, the `imagesId` property can be populated with the YDID of an Image Family, Image Group, Image, or a string representing the native name of a cloud provider image (e.g., an AWS AMI). It can also be populated with the textual name of an Image Family, in the form `namespace/image_family_name`.

## Automatic Properties

The name of the Worker Pool, if not supplied, is automatically generated using a concatenation of `wp_`, the `tag` property, and a UTC timestamp, e,g,: `wp_mytag_221024-155524`.

## TOML Properties in the `workerPool` Section

Here's an example of the `workerPool` section of a TOML configuration file, showing all the possible properties that can be set:

```toml
[workerPool]
    idleNodeTimeout = 10.0
    idlePoolTimeout = 60.0
    imagesId = "ydid:imgfam:000000:41962592-577c-4fde-ab03-d852465e7f8b"
    instanceTags = {}
    maxNodes = 1
    minNodes = 1
    metricsEnabled = true
    name = "my-worker-pool"
    nodeBootTimeout = 5
    requirementTag = "my_tag"
    targetInstanceCount = 1
    templateId = "ydid:crt:D9C548:465a107c-7cea-46e3-9fdd-15116cb92c40"
    # Note: only one of 'userData'/'userDataFile'/'userDataFiles' should be set
    userData = ""
    # userDataFile = "myuserdata.txt"
    # userDataFiles = ["myuserdata1.txt", "myuserdata2.txt"]
    workerTag = "tag-{{username}}"
    # Specify either workersPerNode or workersPerVCPU
    workersPerNode = 1
    # workersPerVCPU = 1
    # workerPoolData = "worker_pool.json"  # Optionally specify worker pool JSON specification
```

## Worker Pool Specification Using JSON Documents

It's also possible to capture a Worker Pool definition as a JSON document. The JSON filename can be supplied either by supplying the command line positional argument for `yd-provision`, or by populating the `workerPoolData` property in the TOML configuration file with the JSON filename. Command line specification takes priority over TOML specification.

The JSON specification allows the creation of **Advanced Worker Pools**, with the ability to specify Node Actions and to differentiate Node Types.

When using a JSON document to specify the Worker Pool, the schema of the document is identical to that expected by the YellowDog REST API for Worker Pool Provisioning.

### Worker Pool JSON Examples

The example below is of a simple JSON specification of a Worker Pool with one initial node, Worker Pool shutdown, etc.

```json
{
  "requirementTemplateUsage": {
    "maintainInstanceCount": false,
    "requirementName": "wp_pyex-primes_230113-161528",
    "requirementNamespace": "pyexamples",
    "requirementTag": "pyex-primes",
    "targetInstanceCount": 1,
    "templateId": "ydid:crt:D9C548:465a107c-7cea-46e3-9fdd-15116cb92c40"
  },
  "provisionedProperties": {
    "idleNodeShutdown": {"enabled": true, "timeout": "PT10M"},
    "idlePoolShutdown": {"enabled": true, "timeout": "PT1H"},
    "createNodeWorkers": {"targetCount": 1, "targetType": "PER_VCPU"},
    "maxNodes": 5,
    "metricsEnabled": true,
    "minNodes": 0,
    "nodeBootTimeout": "PT5M",
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
    "maintainInstanceCount": false
  },
  "provisionedProperties": {
    "createNodeWorkers": {"targetCount": 0, "targetType": "PER_NODE"},
    "nodeConfiguration": {
      "nodeTypes": [
        {"name": "slurmctld", "count": 1},
        {"name": "slurmd", "min": 2, "slotNumbering": "REUSABLE"}
      ],
      "nodeEvents": {
        "STARTUP_NODES_ADDED": [
          {
            "actions": [
              {
                "action": "WRITE_FILE",
                "path": "nodes.json",
                "content": "{\"nodes\":[{{#otherNodes}}{\"name\":\"slurmd{{details.nodeSlot}}\",\"ip\":\"{{details.privateIpAddress}}\"}{{^-last}},{{/-last}}{{/otherNodes}}]}",
                "nodeTypes": ["slurmctld"]
              },
              {
                "action": "RUN_COMMAND",
                "path": "start_simple_slurmctld",
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
                "content": "{\"nodes\":[{{#filteredNodes}}{\"name\":\"slurmd{{details.nodeSlot}}\",\"ip\":\"{{details.privateIpAddress}}\"}{{^-last}},{{/-last}}{{/filteredNodes}}]}",
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
    }
  }
}
```

### TOML Properties Inherited by Worker Pool JSON Specifications

When a JSON Worker Pool specification is used, the following properties from the `config.toml` file will be inherited if the value is absent in the JSON file:

**Properties Inherited within the `requirementTemplateUsage` property**

- `imagesId`
- `instanceTags`
- `requirementName`: derived from the `name` property in the `TOML` configuration. (The name will be generated automatically if not supplied in either the TOML file or the JSON specification.)
- `requirementNamespace`: derived from the `namespace` property in the `TOML` configuration
- `requirementTag`: : derived from the `requirementTag` property at the `workerPool` level, or the `tag` in the `common` configuration
- `targetInstanceCount`
- `templateId`
- `userData`
- `userDataFile`
- `userDataFiles`

Note that the `templateId` property can use either the YellowDog ID ('YDID') for the Compute Requirement Template, or its name. Similarly, the `imagesId` property can use either a YDID or the Image Family Name (e.g, `"yd-agent-docker"`).

**Properties Inherited within the `provisionedProperties` Property**

- `idleNodeTimeout` (set to `0` to disable)
- `idlePoolTimeout` (set to `0` to disable)
- `maxNodes`
- `metricsEnabled`
- `minNodes`
- `nodeBootTimeout`
- `workerTag`
- `workersPerNode` or `workersPerVCPU` (Note that the default value for `workersPerNode` is `1`; override this with `workersPerNode = 0` if required)

## Variable Substitutions in Worker Pool Properties

Variable substitutions can be used within any property value in TOML configuration files or Worker Pool JSON files. See the description [above](#variable-substitutions) for more details on variable substitutions. This is a powerful feature that allows Worker Pools to be parameterised by supplying values on the command line, via environment variables, or via the TOML file.

An important distinction when using variable substitutions within Worker Pool (or Compute Requirement) JSON (or Jsonnet) documents is that each variable directive **must be prefixed and postfixed by a `__` (double underscore)** to disambiguate it from variable substitutions that are to be passed directly to the API. For example, use: `__{{username}}__` to apply a substitution for the `username` default variable substitution.

In general, double underscores are **not** required in variable substitutions within the `workerPool` and/or `computeRequirement` sections of a TOML file. The exception to this is if the `userData` property is supplied, in which case double underscores **are** required. They are also required within any files referenced by the `userDataFile` or `userDataFiles` properties.

## Dry-Running Worker Pool Provisioning

To examine the JSON that will actually be sent to the YellowDog API after all processing, use the `--dry-run` command line option when running `yd-provision`. This will print the JSON specification for the Worker Pool. Nothing will be submitted to the platform.

The generated JSON is produced after all processing (incorporating `config.toml` properties, variable substitutions, etc.) has been concluded, so the dry-run is useful for inspecting the results of all the processing that's been performed.

To suppress all output except for the JSON itself, add the `--quiet` (`-q`) command line option.

The JSON dry-run output could itself be used by `yd-provision`, if captured in a file, e.g.:

```shell
yd-provision --dry-run -q > my_worker_pool.json
yd-provision my_worker_pool.json
```

# Creating, Updating and Removing Resources

The commands **yd-create** and **yd-remove** allow the creation, update and removal of the following YellowDog resources:

- Keyrings
- Credentials
- Compute Source Templates
- Compute Requirement Templates
- Image Families, Image Groups, and Images
- Namespace Storage Configurations
- Configured Worker Pools
- Allowances
- String Attribute Definitions
- Numeric Attribute Definitions
- Namespace Policies

## Overview of Operation

The **yd-create** and **yd-remove** commands operate on a list of one or more resource specification files in JSON (or Jsonnet) format.

Each resource specification file can contain a single resource specification or a list of resource specifications. Different resource types can be mixed together in the same list.

The complete list of resource specifications is re-sequenced on processing to ensure that possibly dependent resources are dealt with in a suitable order. For example, all Compute Source Templates are always processed before any Compute Requirement Templates on resource creation, and the reverse sequencing is used on resource removal.

Resource specification files can use all forms of **variable substitution** just as in the case of Work Requirements, etc.

### Resource Creation

To create resources, use the `yd-create` command as follows:

```shell
yd-create resources_1.json <resources_2.json, ...>
```

### Resource Update

Resources are updated by re-running the `yd-create` command with the same (edited) resource specifications. Update operations will prompt the user for approval: as in other commands, this can be overridden using the `--yes` command line option.

The update action will create any resources that are not already present in the Platform, and it will update any resources that are already present. The command does not check for specific differences, so an unchanged resource specification will still cause an update.

### Resource Removal

Resources are removed by running the `yd-remove` command, with the same form of resource specifications. For example:

```shell
yd-remove resources_1.json <resources_2.json, ...>
```
Destructive operations will prompt the user for approval: as in other commands, this can be overridden using the `--yes` command line option.

The `yd-remove` command can also be used to remove resources by their `ydid` resource IDs, by using the `--ids` option. For example:

```shell
yd-remove --ids ydid:crt:D9C548:2a09093d-c74c-4bde-95d1-c576c6f03b13 ydid:imgfam:D9C548:4bc3cc57-1387-49a6-85d4-132bcf3a65fd
```

### Resource Matching

Resources match on **resource names** and (where applicable) **resource namespaces** rather than on YellowDog IDs. This is done for flexibility and to allow the `yd-create` and `yd-remove` commands to be essentially stateless (i.e., we don't need to keep a local record of the YellowDog IDs of the resources created). 

However, this means that **caution is required** when updating or removing resources, since resource matching is done using **only** the **namespace/name** of the resource -- i.e., the system-generated `ydid` IDs are not used. This means that a resource with a given name could have been removed and replaced in Platform by some other means, and the resource specification(s) would still match it.

## Resource Specification Definitions

The JSON specification used to define each type of resource can be found by inspecting the YellowDog Platform REST API documentation at https://docs.yellowdog.co/api.

For example, to obtain the JSON schema for creating a Compute Source Template, take a look at the REST API call for adding a new Compute Source template: https://docs.yellowdog.co/api/?spec=Compute%20API#tag/compute/post/compute/templates/sources.

When using the `yd-create` and `yd-remove` commands, note that an additional property `resource` must be supplied, to identify the type of resource being specified. The `"resource"` property can take the following values:

- `"Keyring"`
- `"Credential"`
- `"ComputeSourceTemplate"`
- `"ComputeRequirementTemplate"`
- `"MachineImageFamily"`
- `"NamespaceStorageConfiguration"`
- `"ConfiguredWorkerPool"`
- `"Allowance"`
- `"StringAttributeDefinition"`
- `"NumericAttributeDefinition"`
- `"NamespacePolicy"`

## Generating Resource Specifications

To generate example JSON specifications from resources already included in the platform, the `yd-list` command can be used with the `--details` option, and select the resources for which details are required. E.g.:

```shell
yd-list --keyrings --details
yd-list --source-templates --details
yd-list --compute-templates --details
yd-list --image-families --details
```

This will produce a list of resource specifications that can be copied and used directly with `yd-create` and `yd-remove`. Certain fields, such as the ID, will be ignored, with warnings. The detailed resource list can also be copied directly to an output file in addition to being displayed on the console:

```shell
yd-list yd-list --source-templates --details --output-file my-resources.json
```

Alternatively, the `yd-show` command can be used with one or more `ydid` arguments to generate the details of each identified resource. E.g.,

```shell
yd-show -q ydid:cst:000000:cde265f8-0b17-4e0e-be1c-505174a620e4 > my-compute-source-template.json
```

would generate a JSON file that can be used with `yd-create` without alteration, or which could be edited.

Both `yd-list` and `yd-show` support the `--substitute-ids`/`-U` option. For Compute Requirement Template detailed output, this will substitute Compute Source Template IDs and Image Family IDs with their names, to make it easier to use the output acrosss YellowDog accounts.

## Preprocessing Resource Specifications

The `--dry-run`/`-D` and `--jsonnet-dry-run`/`-J` options can be used with `yd-create` to display the processed JSON data structures without any resources being created or updated.

Below, we'll discuss each item type with example specifications.

## Keyrings

The Keyring example and schema can be found at: https://docs.yellowdog.co/api/?spec=Account%20API#tag/keyring/post/keyrings.

An example Keyring specification is shown below:

```json
{"resource": "Keyring", "name": "my-keyring-1", "description": "My First Keyring"}
```

or to specify two Keyrings at once:

```json
[
  {"resource": "Keyring", "name": "my-keyring-1", "description": "My First Keyring"},
  {"resource": "Keyring", "name": "my-keyring-2", "description": "My Second Keyring"}
]
```

When a new Keyring is created it's usable only by the YellowDog application which created it. A **system-generated password** is also returned as a one time response, which would allow the Keyring also to be claimed by YellowDog Portal users. For security reasons the password is not displayed, but this behaviour can be overridden using the `--show-keyring-passwords` command line option, e.g.:

```shell
% yd-create --quiet --show-keyring-passwords keyring.json
Keyring 'my-keyring-1': Password = 4OQAdcZagUX7ZiHaYvqC4yuKb4KCyN9lk4Z7mCcTYXA
```

Note that Keyrings **cannot be updated**; they must instead be removed and recreated, and in doing so, any contained credentials will be lost.

## Credentials

The Credential example and schema can be found at: https://docs.yellowdog.co/api/?spec=Account%20API#tag/keyring/put/keyrings/%7BkeyringName%7D/credentials.

For example, to add a single AWS credential to a Keyring, the following resource specification might be used:

```json
{
  "resource": "Credential",
  "keyringName": "my-keyring-1",
  "credential": {
    "type": "co.yellowdog.platform.account.credentials.AwsCredential",
    "name": "my-aws-creds",
    "description": "Fake AWS credentials",
    "accessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "secretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}
```
To **update** a Credential, make the modifications to the resource specification and run `yd-create` again, and to remove a credential, run `yd-remove`.

## Compute Source Templates

The Compute Source Template example and schema can be found at: https://docs.yellowdog.co/api/?spec=Compute%20API#tag/compute/post/compute/templates/sources.

An example Compute Source resource specification is found below:

```json
{
  "resource": "ComputeSourceTemplate",
  "namespace": "my-namespace",
  "description": "one",
  "attributes": [],
  "source": {
    "type": "co.yellowdog.platform.model.AwsInstancesComputeSource",
    "name": "my-compute-source-template",
    "credential": "my-keyring/my-aws-credential",
    "region": "eu-west-1",
    "availabilityZone": null,
    "securityGroupId": "sg-07bcbfb052873888",
    "instanceType": "*",
    "imageId": "*",
    "limit": 0,
    "specifyMinimum": false,
    "assignPublicIp": true,
    "createClusterPlacementGroup": null,
    "createElasticFabricAdapter": null,
    "enableDetailedMonitoring": null,
    "keyName": null,
    "iamRoleArn": null,
    "subnetId": "subnet-0d241e541249e9fdc",
    "userData": null,
    "instanceTags": {"environment": "demo-prod"}
  }
}
```

In the Compute Source Template `imageId` property, an Image Family **namespace/name** may be used instead of an ID. For example: `"imageId": "yellowdog/yd-agent-docker"`. The `yd-create` command will look up the Image Family name and substitute its ID. 

## Compute Requirement Templates

The Compute Requirement Template example and schema can be found at: https://docs.yellowdog.co/api/?spec=Compute%20API#tag/compute/post/compute/templates/requirements.

An example Compute Requirement resource specification is found below, for a **static** tempate:

```json
{
  "resource": "ComputeRequirementTemplate",
  "imagesId": "ami-097767a3a3e071555",
  "instanceTags": {},
  "name": "my-static-compute-template",
  "namespace": "my-namespace",
  "strategyType": "co.yellowdog.platform.model.WaterfallProvisionStrategy",
  "type": "co.yellowdog.platform.model.ComputeRequirementStaticTemplate",
  "sources": [
    {"instanceType": "t3a.small", "sourceTemplateId": "ydid:cst:D9C548:d41c36a7-0630-4fa2-87e7-4e20bf472bcd"},
    {"instanceType": "t3a.medium", "sourceTemplateId": "ydid:cst:D9C548:d41c36a7-0630-4fa2-87e7-4e20bf472bcd"}
  ]
}
```

Note that Compute Source Template **namespace/names** in the form `namespace/compute_source_template_name` can be used instead of their IDs: the **yd-create** command will look up the IDs and make the substitutions. The Compute Source Templates must already exist.

Also, In the `imagesId` property, an Image Family **namespace/name** may be used instead of an ID. For example: `"imagesId": "yellowdog/yd-agent-docker"`. The `yd-create` command will look up the Image Family name and substitute its ID.

A **dynamic** template example is:

```json
{
  "resource": "ComputeRequirementTemplate",
  "sourceTraits": {},
  "strategyType": "co.yellowdog.platform.model.SplitProvisionStrategy",
  "type": "co.yellowdog.platform.model.ComputeRequirementDynamicTemplate",
  "imagesId": "ydid:imgfam:000000:41962592-577c-4fde-ab03-d852465e7f8b",
  "instanceTags": {},
  "maximumSourceCount": 10,
  "minimumSourceCount": 1,
  "name": "my-dynamic-compute-template",
  "namespace": "my-namespace",
  "constraints": [
    {
      "anyOf": ["AWS"],
      "attribute": "source.provider",
      "type": "co.yellowdog.platform.model.StringAttributeConstraint"
    },
    {"attribute": "yd.cost", "max": 0.05, "min": 0, "type": "co.yellowdog.platform.model.NumericAttributeConstraint"},
    {
      "anyOf": ["UK", "Ireland"],
      "attribute": "yd.country",
      "type": "co.yellowdog.platform.model.StringAttributeConstraint"
    },
    {"attribute": "yd.ram", "max": 4096, "min": 2, "type": "co.yellowdog.platform.model.NumericAttributeConstraint"}
  ],
  "preferences": [
    {
      "attribute": "yd.cpu",
      "rankOrder": "PREFER_HIGHER",
      "type": "co.yellowdog.platform.model.NumericAttributePreference",
      "weight": 3
    },
    {
      "attribute": "yd.ram",
      "rankOrder": "PREFER_HIGHER",
      "type": "co.yellowdog.platform.model.NumericAttributePreference",
      "weight": 2
    },
    {
      "attribute": "yd.cpu-type",
      "preferredValues": ["AMD"],
      "type": "co.yellowdog.platform.model.StringAttributePreference",
      "weight": 1
    }
  ]
}
```

## Image Families

The Image Family example and schema can be found at: https://docs.yellowdog.co/api/?spec=Images%20API#tag/images/post/images/families.

An example specification, illustrating a containment hierarchy of Image Family -> Image Group -> Image, is shown below:

```json
{
  "resource": "MachineImageFamily",
  "access": "PRIVATE",
  "metadataSpecification": {},
  "name": "my-windows-image-family",
  "namespace": "my-namespace",
  "osType": "WINDOWS",
  "imageGroups": [
    {
      "metadataSpecification": {},
      "name": "v5_0_16",
      "osType": "WINDOWS",
      "images": [
        {
          "metadata": {},
          "name": "win-2022-yd-agent-5_0_16",
          "osType": "WINDOWS",
          "provider": "AWS",
          "providerImageId": "ami-0cb09e7f49c1eb021",
          "regions": ["eu-west-1"],
          "supportedInstanceTypes": []
        },
        {
          "metadata": {},
          "name": "win-2022-yd-agent-5_0_16",
          "osType": "WINDOWS",
          "provider": "AWS",
          "providerImageId": "ami-0cb09e7f49c1eb022",
          "regions": ["eu-west-2"],
          "supportedInstanceTypes": []
        }
      ]
    }
  ]
}
```

Note that if the name of an Image Group or an Image is changed in the resource specification, the existing resource with the previous name will be removed from the Platform because it's no longer present in the resource specification. To prevent this, retain the previous resource in your specification, and add resources as required.

## Namespace Storage Configurations

The Namespace Storage Configuration example and schema can be found at: https://docs.yellowdog.co/api/?spec=Object%20Store%20API#tag/object-store/put/objectstore/configurations.

Example:

```json
{
  "resource": "NamespaceStorageConfiguration",
  "type": "co.yellowdog.platform.model.S3NamespaceStorageConfiguration",
  "namespace": "my-s3-namespace",
  "bucketName": "com.my-company.test.my-yd-objects",
  "region": "eu-west-2",
  "credential": "my-keyring/my-aws-credential"
}
```

## Configured Worker Pools

The Configured Worker Pool example and schema can be found at: https://docs.yellowdog.co/api/?spec=Scheduler%20API#tag/worker-pools/post/workerPools/configured.

Example:

```json
{
  "resource": "ConfiguredWorkerPool",
  "name": "my-configured-pool-pwt",
  "namespace": "my-namespace", 
  "properties": {
    "nodeConfiguration": {
      "nodeTypes": [
        {
          "name": "example",
          "count": 0,
          "min": 0,
          "sourceNames": ["example"],
          "slotNumbering": "REUSABLE"
        }
      ],
      "nodeEvents": {
        "STARTUP_NODES_ADDED": []
      },
      "targetNodeCount": 0
    }
  }
}
```

## Allowances

The Allowances example and schema can be found at: https://docs.yellowdog.co/api/?spec=Usage%20API#tag/allowances/post/allowances.

Example:
```json
{
  "resource": "Allowance",
  "description": "my-allowance",
  "allowedHours": 1000,
  "effectiveFrom": "Now",
  "effectiveUntil": "After two months",
  "instanceTypes": [],
  "limitEnforcement": "SOFT",
  "monitoredStatuses": ["RUNNING", "PENDING", "STOPPED", "TERMINATING", "STOPPING"],
  "regions": ["eu-west-2"],
  "resetType": "NONE",
  "sourceCreatedFromId": "awsondemand-eu-west-2",
  "type": "co.yellowdog.platform.model.SourcesAllowance"
}
```

The `effectiveFrom` and `effectiveUntil` date-time string fields can use any format supported by the **[dateparser](https://dateparser.readthedocs.io/en/latest/)** library, including some natural language formulations.

Compute Source Template and Compute Requirement Template IDs can use names instead of IDs, and the IDs will be substituted by `yd-create`. However, if a Source allowance is created (type `co.yellowdog.platform.model.SourceAllowance`), then the Compute Source ID (note: **not** the Compute Source Template ID) itself must be used in the `sourceId` property.

Allowances **cannot be updated** (edited) once they have been created; they can only be removed and recreated. However, if using `yd-create` to update existing Allowances, the `--match-allowances-by-description`/`-M` option can be used, in which case Allowances will be matched using their `description` property. If matches are found, these can optionally be removed before new Allowances are created. If multiple existing, matching Allowances are found, the user will be asked to select which ones (if any) to remove.

When using `yd-remove`, Allowances are again matched using their `description` property only if `--match-allowances-by-description`/`-M` is used. As with other resources, Allowances can also be removed by their IDs (`yd-remove --ids <allowance_id> [<allowance_id>]`).

Allowances can be **boosted** (have extra hours added to the Allowance) using the `yd-boost` command.

## Attribute Definitions

The Attribute Definition example and schema can be found at: https://docs.yellowdog.co/api/?spec=Compute%20API#tag/compute/post/compute/attributes/user.

### String Attribute Definitions

Example:

```json
{
  "resource": "StringAttributeDefinition",
  "name": "user.my-attribute",
  "title": "My attribute title",
  "description": "This is a description of my attribute",
  "options": ["yes", "no", "maybe"]
}
```

The `name` and `title` properties are required, while the rest are optional. The `user.` prefix is required when specifying the `name` property.

### Numeric Attribute Definitions

Example:

```json
{
  "resource": "NumericAttributeDefinition",
  "name": "user.my-numeric-attribute",
  "title": "Attribute Title",
  "defaultRankOrder": "PREFER_LOWER",
  "description": "A description of the attribute",
  "units": "$",
  "range": {"min": 1, "max": 10}
}
```

The `name`, `title` and `defaultRankOrder` properties are required, while the rest are optional. Either the `range` property or the `options` property (with numeric option values) can be specified, but not both. The `user.` prefix is required when specifying the `name` property.

## Namespace Policies

The Namespace Policies example and schema can be found at: (TBD).

```json
{
  "resource": "NamespacePolicy",
  "namespace": "test_namespace",
  "autoscalingMaxNodes": 3
}
```

Namespace Policies are matched by their `namespace` property when using `yd-create` and `yd-remove`. The `autoscalingMaxNodes` property can be omitted or set to `null` to remove an existing limit for a namespace.

# Jsonnet Support

In all circumstances where JSON files are used by the Python Examples commands,  **[Jsonnet](https://jsonnet.org)** files can be used instead. This allows the use of Jsonnet's powerful JSON extensions, including comments, variables, functions, etc.

A simple usage example might be:

```shell
yd-submit my_work_req.jsonnet
```

The use of the filename extension `.jsonnet` will invoke Jsonnet evaluation. (Note that a temporary JSON file is created as part of Jsonnet processing, which you may see referred to in error messages: this file will have been deleted before the command exits.)

## Jsonnet Installation

Jsonnet is **not** installed by default when `yellowdog-python-examples` is installed, because the package has binary components that are not available on PyPI for all platforms. If you try to use a Jsonnet file in the absence of Jsonnet, the scripts will print an error message, and suggest an installation mechanism.

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

## Variable Substitutions in Jsonnet Files

The scripts provide full support for variable substitutions in Jsonnet files, using the same rules as for the JSON specifications. Remember that for **Worker Pool** and **Compute Requirement** specifications, variable substitutions must be prefixed and postfixed by double underscores (`__`), e.g. `"__{{username}}__"`.

Variable substitution is performed before Jsonnet expansion into JSON, **and** again after the expansion.

## Checking Jsonnet Processing

There are three possibilities for verifying that a Jsonnet specification is doing what is intended:

1. To inspect the basic conversion of Jsonnet into JSON, without any additional processing by the Python Examples commands, the `yd-jsonnet2json` command can be used. This takes a single command line argument which is the name of the jsonnet file to be processed:

```shell
yd-jsonnet2json my_file.jsonnet
```


2. The `jsonnet-dry-run` (`-J`) option of the `yd-submit`, `yd-provision`, `yd-instantiate`, `yd-create` and `yd-remove` commands will generate JSON output representing the Jsonnet to JSON processing only, including applicable variable substitutions, but before full property expansion into the JSON that will be submitted to the Platform.


3. The `dry-run` (`-D`) option will generate JSON output representing the full processing of the Jsonnet file into what will be submitted to the API. This allows inspection to check that the output matches expectations, prior to submitting to the Platform.

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

When this is inspected using the `jsonnet-dry-run` option (`yd-submit -Jq my_work_req.jsonnet`), this is the processed output:

```json
{
  "name": "workreq_230114-140645",
  "taskGroups": [
    {
      "tasks": [
        {
          "arguments": ["1"],
          "environment": {"A": "A_1"},
          "name": "my_task_{{task_number}}"
        },
        {
          "arguments": ["2", "3"],
          "environment": {},
          "name": "my_task_{{task_number}}"
        },
        {
          "arguments": ["4"],
          "environment": {},
          "name": "my_task_{{task_number}}"
        },
        {
          "arguments": [],
          "environment": {},
          "name": "my_task_{{task_number}}"
        }
      ]
    }
  ]
}
```

When this is inspected using the `dry-run` option (`yd-submit -D my_work_req.jsonnet`), this is the processed output:

```json
{
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

To suppress output formatting, including coloured output and line wrapping, the `--no-format` option can be used. Note that any outputs exceeding 1,000 lines in size (e.g., a very large JSON object, or table), will not produce coloured output.

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

The `yd-download` command downloads objects from the YellowDog Object Store.

The `namespace` and `tag` values are used to determine which objects to download. To download a specific object or directory, specify it using the `--tag` option, e.g.:

```shell
yd-download --tag "path/to/my/object"
```

Use the `--all` (`-a`) option to list the full directory/object structure and all objects.

Objects will be downloaded to a directory with the same name as `namespace`. Alternatively, a local download directory can be specified with the `--directory` option. Directories will be created if they don't already exist. Files that are downloaded will overwrite existing local files **without warning**.

## yd-delete

The `yd-delete` command deletes any objects created in the YellowDog Object Store.

The `namespace` and `tag` values in the `config.toml` file are used to identify which objects to delete. Note that it's easy to use `yd-delete` to clear the contents of a namespace by using an empty `tag`, as follows:

```shell
yd-delete -t ""
```

This can be extended to any other namespace by using the `--namespace`/`-n` option.

To delete a specific directory or object, supply the directory or object name using the `--tag` option, e.g.:

```shell
yd-delete --tag "path/to/my/directory"
yd-delete -t "path/to/my/directory/object"
```

Use the `--all` (`-a`) option to see the list directory/object structure and all objects.

## yd-upload

The `yd-upload` command uploads files from the local filesystem to the YellowDog Object store. Files are placed in the configured `namespace` within a directory matching the `tag` property or using the value of the `--prefix` (`--tag`, `-t`) option, e.g.:

```shell
yd-upload --prefix my_work_requirement file_1 file_2 morefiles/file3
```
To suppress the mirroring of the local directory structure within the object store, use the `--flatten-upload-paths` or `-f` option. Note that if this creates multiple uploaded files with the same path in the Object Store folder, files will be overwritten.

Files in directories may be recursively uploaded using the `--recursive` or `-r` option, e.g.:

```shell
yd-upload --prefix my_work_requirement -r mydir myotherdir myfile
```

To upload to other namespaces, use the `--namespace`/`-n` option.

To use the **batch** uploader, use the `--batch`/`-b` option. Note that the `--prefix`, `--recursive`, and `--flatten-upload-paths` options are ignored when using batch uploads. Batch uploading only accepts file patterns with wildcards, and these should be quoted to prevent shell expansion. E.g.:

```shell
yd-upload --batch '*.sh' '*.json'
```

## yd-shutdown

The `yd-shutdown` command shuts down Worker Pools that match the `namespace` and `tag` found in the configuration file. All remaining work will be cancelled, but currently executing Tasks will be allowed to complete, after which the Compute Requirement will be terminated.

## yd-instantiate

The `yd-instantiate` command instantiates a Compute Requirement (i.e., a set of instances that are managed by their creator and do not automatically become part of a YellowDog Worker Pool).

This command uses the data from the `workerPool` configuration section (or, synonymously, the `computeRequirement` section), but only uses the `name`, `templateId`, `targetInstanceCount`, `instanceTags`, `userData`, `requirementTag`, and `imagesId` properties. In addition, the Boolean property `maintainInstanceCount` (default = `false`) is available for use with `yd-instantiate`.

Compute Requirements can be instantiated directly from JSON (or Jsonnet) specifications, using the `--compute-requirement` (or `-C`) command line option, followed by the filename, or by using the `computeRequirementData` property in the `workerPool`/`computeRequirement` section. The properties listed above will be inherited from the config.toml `workerPool` specification if they are not present in the JSON file.

Variable substitutions must be prefixed and postfixed by a double underscore (`__`), e.g.: `"__{{my_variable}}__"`.

An example JSON specification is shown below:

```json
{
  "imagesId": "ydid:imgfam:000000:41962592-577c-4fde-ab03-d852465e7f8b",
  "instanceTags": {"a1": "one", "a2": "two"},
  "requirementName": "cr_test___{{datetime}}__",
  "requirementNamespace": "pyexamples",
  "requirementTag": "pyexamples-test",
  "templateId": "ydid:crt:000000:230e9a42-97db-4d69-aa91-29ff309951b4",
  "userData": "#/bin/bash\n#Other stuff...",
  "targetInstanceCount": 1,
  "maintainInstanceCount": true
}
```

Note that the `templateId` property can use either the YellowDog ID ('YDID') for the Compute Requirement Template, or its name. The same is true for the `imagesId` property.

If a Worker Pool is defined in JSON, using `workerPoolData` in the configuration file or by supplying the command line positional argument, `yd-instantiate` will extract the Compute Requirement from the Worker Pool specification (ignoring Worker-Pool-specific data), and use that for instantiating the Compute Requirement.

Use the `--dry-run` option to inspect the details of the Compute Requirement specification that will be submitted, in JSON format. The JSON output of this command can itself be used with the `yd-instantiate` command.

### Test-Running a Dynamic Template

When a the `templateId` of a Dynamic Requirement is used, the `yd-instantiate` command can be used to report on a test run of the Template, using the `--report` (or `-r`) command line option. This can be used with TOML-defined Compute Requirement specifications, but not those that are JSON-defined.

No instances will be provisioned during the test run.

For example:

```shell
% yd-instantiate --report --quiet
┌────┬────────┬────────────┬───────────────────────────┬───────────┬────────────────┬───────────────────┐
│    │   Rank │ Provider   │ Type                      │ Region    │ InstanceType   │ Source Name       │
├────┼────────┼────────────┼───────────────────────────┼───────────┼────────────────┼───────────────────┤
│  1 │      1 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ t3a.micro      │ awsspot-eu-west-2 │
│  2 │      2 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ t3a.small      │ awsspot-eu-west-2 │
│  3 │      3 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ c5a.large      │ awsspot-eu-west-2 │
│  4 │      3 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ c6a.large      │ awsspot-eu-west-2 │
│  5 │      3 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ t3a.medium     │ awsspot-eu-west-2 │
│  6 │      4 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ m5a.large      │ awsspot-eu-west-2 │
│  7 │      4 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ m5ad.large     │ awsspot-eu-west-2 │
│  8 │      4 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ m6a.large      │ awsspot-eu-west-2 │
│  9 │      4 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ t3a.large      │ awsspot-eu-west-2 │
│ 10 │      5 │ AWS        │ AwsInstancesComputeSource │ eu-west-2 │ r5a.large      │ awsspot-eu-west-2 │
└────┴────────┴────────────┴───────────────────────────┴───────────┴────────────────┴───────────────────┘
```

## yd-terminate

The `yd-terminate` command immediately terminates Compute Requirements that match the `namespace` and `tag` found in the configuration file. Any executing Tasks will be terminated immediately, and the Worker Pool will be shut down.

## yd-list

The `yd-list` command is used to list various YellowDog items, using the `namespace` and `tag` properties (if applicable) to target the scope of what to list:

- Allowances
- Applications
- Attribute Definitions
- Compute Requirement Templates
- Compute Requirements
- Compute Source Templates
- Groups
- Image Families, Image Groups, and Images
- Instances
- Keyrings
- Namespace Policies
- Namespace Storage Configurations
- Nodes
- Objects in the Object Store
- Roles
- Task Groups
- Tasks
- Users
- Work Requirements
- Worker Pools
- Workers

Please use `yd-list --help` to inspect the various options.

In some cases a `--details/-d` option can be supplied to drill down into additional detail on selected resources. For example `yd-list --keyrings --details` allows inspection of the Credentials within the selected Keyrings.

The `--active` flag can be used to list only entities that are in a non-terminated state, if applicable, for example Work Requirements and Worker Pools.

To relax filtering on `namespace` and `tag`, these can be set to empty strings using `-n -t` without values.

## yd-resize

The `yd-resize` command is used to resize Worker Pools, and also Compute Requirements when used with the `--compute-requirement`/`-C` option. See `yd-resize --help` for more information.

The name or ID of the Worker Pool or Compute Requirement is supplied along with the new target number of Nodes or Instances. Usage examples:

```shell
yd-resize wp_pyex-slurm-pwt_230711-124356-0d6 10
yd-resize ydid:wrkrpool:D9C548:1f020696-ae9a-4786-bed2-c31b484b1d4f 10
yd-resize --compute-requirement cr_pyex-slurm-pwt_230712-110226-04c 5
yd-resize -C ydid:compreq:D9C548:600bef1f-7ccd-431c-afcc-b56208565aac 5
```

## yd-create

The `yd-create` command is used to create or update YellowDog resources, specified in one or more JSON (or Jsonnet) files supplied on the command line. Each file can contain one or more resources.

## yd-remove

The `yd-remove` command is used to remove YellowDog resources, specified in one or more JSON (or Jsonnet) files supplied on the command line. Each file can contain one or more resources.

## yd-follow

The `yd-follow` command is used to follow the event streams for one or more Work Requirements, Worker Pools and Compute Requirements, specified by their YellowDog IDs (`ydids`), e.g.:

```shell
yd-follow ydid:workreq:D9C548:37d3c0cd-2651-4779-be17-89a8601b03b8 \
          ydid:wrkrpool:D9C548:c22f0d9a-4a99-460d-ae42-15653ba264c3 \
          ydid:compreq:D9C548:98879b5a-9192-4a56-ad25-fc1330e49185
```

The `yd-follow` command will continue to run until manually stopped using `CTRL-C`, unless all the IDs to be followed are in a terminal state.

## yd-start

The `yd-start` command is used to start `HELD` Work Requirements.

It can optionally be supplied with a list of the names and/or YDIDs of the specific Work Requirements to start, otherwise the `namespace` and `tag` will be used to generate a list of candidate requirements.

## yd-hold

The `yd-hold` command is used to hold (pause) `RUNNING` Work Requirements.

It can optionally be supplied with a list of the names and/or YDIDs of the specific Work Requirements to hold, otherwise the `namespace` and `tag` will be used to generate a list of candidate requirements.

## yd-boost

The `yd-boost` command is used to boost Allowances by the specified number of hours.

## yd-show

The `yd-show` command will show the details (in JSON) of any YellowDog entity that has a YellowDog ID. It supports IDs referring to:

- Compute Source Templates
- Compute Requirement Templates
- Compute Requirements
- Sources
- Worker Pools
- Nodes
- Workers
- Work Requirements
- Task Groups
- Tasks
- Image Families, Image Groups, and Images
- Keyrings
- Allowances
- Users
- Applications
- Groups
- Roles

## yd-compare

The `yd-compare` command takes a Work Requirement or Task Group ID and one or more Worker Pool IDs, and compares the selected Task Group(s) against the available Nodes/Workers in the Worker Pool(s). If a Work Requirement ID is supplied, all Task Groups in the Work Requirement will be compared.

```commandline
yd-compare ydid:taskgrp:000000:83587010-5e26-4174-92a7-c7cc2612638d:1 ydid:wrkrpool:000000:3666e4c5-382e-4512-a2c7-33dbb839f75
```

The command checks if the **Run Specification** of a Task Group matches the properties of the Worker Pools and their registered Nodes and Workers, meaning there are Workers in the Worker Pool that could be claimed by the Task Group and that the Worker Pool would be a candidate for scaling up to meet the demands of the Task Group.

A detailed matching report showing the comparison against each specific property is created, which can be used to determine which properties are preventing a Worker Pool match.

The match status of a Worker Pool falls into one of four categories:

| **Match Status** | **Meaning**                                                                                                     |
|------------------|-----------------------------------------------------------------------------------------------------------------|
| **YES**          | The Worker Pool and every Node/Worker that has registered so far match the Task Group.                          |
| **NO**           | The Worker Pool and/or none of the Nodes/Workers that have registered so far match the Task Group.              |
| **MAYBE**        | The Worker Pool matches the Task Group but no Nodes have yet registered, so Node/Worker properties are unknown. |
| **PARTIAL**      | The Worker Pool and some of the Nodes/Workers that have registered are a match for the Task Group.              |
