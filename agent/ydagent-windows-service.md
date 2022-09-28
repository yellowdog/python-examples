# YellowDog Agent: Installation as a Windows Service for On-Premise Systems (Draft)

## Prerequisites
- Java 11+ installed
- Access to the YellowDog Agent jar file

## Installation Steps
1. Create `C:\Program Files\YellowDog\Agent`
2. Create `C:\ProgramData\YellowDog\Agent\actions` and `C:\ProgramData\YellowDog\Agent\workers`
3. Copy the YellowDog Agent jar file `agent.jar` file to `C:\Program Files\YellowDog\Agent`
4. Create or copy a suitably configured `application.yaml` to `C:\ProgramData\YellowDog\Agent`
5. Add `YD_AGENT_HOME=C:\Program Files\YellowDog\Agent` to the System Environment Variables 
6. Add `YD_AGENT_DATA=C:\Program Files\YellowDog\Agent` to the System Environment Variables
7. Add `%YD_AGENT_HOME%` to the System Path
8. Download the appropriate version for your platform of the **WinSW** wrapper executable from https://github.com/winsw/winsw/releases/tag/v3.0.0-alpha.10 (e.g., `WinSW-x64.exe`)
9. Copy the WinSW wrapper executable to `C:\Program Files\YellowDog\Agent` and rename it to `ydagent.exe`
10. Create `ydagent.xml` in `C:\Program Files\YellowDog\Agent` with the following contents:
```xml
<service>
    <id>ydagent</id>
    <name>YellowDog Agent</name>
    <description>The YellowDog Scheduler node agent.</description>
    <executable>java</executable>
    <arguments>-jar "%BASE%\agent.jar"</arguments>
    <startmode>Automatic</startmode>
    <delayedAutoStart>true</delayedAutoStart>
    <logmode>rotate</logmode>
</service>
```
11. In `C:\Program Files\YellowDog\Agent` run `ydagent.exe install`
