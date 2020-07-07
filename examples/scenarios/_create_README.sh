#!/bin/bash

# re run the scenario tests creating new output
rm -rf Output
mkdir Output
pushd ../..
pytest tests/test_scenarios.py
popd

# collect all log outputs into one README.md file
rm -rf README.md
echo "### Sample output of all test scenarios " >> README.md
echo >> README.md

for FOLDER in `ls Output`; do
  if [ -d "Output/$FOLDER" ]; then
    echo >> README.md
    echo "## $FOLDER" >> README.md
    echo "\`\`\`" >> README.md
    cat "Output/$FOLDER/log.txt" >> README.md
    echo "\`\`\`" >> README.md
  fi
done

echo >> README.md
echo "The ASC MHL files can be found in the \`\`ascmhl\`\` folders amongst the scenario output files in the [Output/](Output/) folder." >> README.md
echo >> README.md
