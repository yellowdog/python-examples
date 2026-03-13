#!/bin/bash

YD_AGENT_HOME="/opt/yellowdog/agent"

# Insert 'bash' Task Type into 'application.yaml', if not already present
grep -q '"bash"' $YD_AGENT_HOME/application.yaml
if [[ $? == 1 ]]
then
  sed -i '/^yda.taskTypes:/a\  - name: "bash"\n    run: "/bin/bash"' \
      $YD_AGENT_HOME/application.yaml
fi
