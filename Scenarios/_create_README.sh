#!/bin/bash

rm -rf README.md

echo "### Sample output of all scenario scipts" >> README.md
echo >> README.md

echo "## scenario_01.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_01.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_01A.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_01A.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_02.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_02.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_03.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_03.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_04.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_04.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_05.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_05.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_06.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_06.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_07.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_07.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_08.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_08.sh >> README.md
echo "\`\`\`" >> README.md

echo "## scenario_09.sh" >> README.md
echo "\`\`\`" >> README.md
./scenario_09.sh >> README.md
echo "\`\`\`" >> README.md

PATHPREFIX="Writing \""$(PWD)
PATHPREFIX=$PATHPREFIX"/"
PATHPREFIX=$(echo $PATHPREFIX | sed 's/\//\\\//g')
sed -i -e 's/'"$PATHPREFIX"'/Writing \"[…]/g' README.md

PATHPREFIX="Traversing \""$(PWD)
PATHPREFIX=$PATHPREFIX"/"
PATHPREFIX=$(echo $PATHPREFIX | sed 's/\//\\\//g')
sed -i -e 's/'"$PATHPREFIX"'/Traversing \"[…]/g' README.md

PATHPREFIX=" "$(PWD)
PATHPREFIX=$PATHPREFIX"/"
PATHPREFIX=$(echo $PATHPREFIX | sed 's/\//\\\//g')
sed -i -e 's/'"$PATHPREFIX"'/[…]/g' README.md


echo >> README.md
echo "The ASC-MHL files can be found in the \`\`asc-mhl\`\` folders amongst the scenario output files in the [Output/](Output/) folder." >> README.md
echo >> README.md

rm -rf README.md-e

# update hive material:
#
# $ cd hive-master/cli
# $ python3 -m venv env
# $ env/bin/activate
# $ hive seal [....]/asc-mhl-tools/Scenarios/Output/scenario_06/A002R2EC
# 
# copy and paste output into Scenarios/Template/Material/Scenario 06/hive-output.rtf
# move "Scenarios/Output/scenario_06/A002R2EC/hive" to "Scenarios/Template/Material/Scenario 06"



