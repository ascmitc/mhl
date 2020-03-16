#!/bin/bash

SCENARIO="07"

echo
echo "Scenario $SCENARIO:"
echo "Writing extended attributes (xxattr) for files and folders during verification."
echo
echo "Hashes stored in extended attributes might be required by systems used further down the"
echo "workflow, so the hashes from the ASC-MHL file can also be written to extended attributes"
echo "on demand."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A: The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
eval ../$COMMAND

echo
echo "Step 2: Inspecting extended attributes - no hash attributes are set."

echo 
COMMAND="/usr/bin/xattr -r -l $(pwd)/Output/scenario_$SCENARIO/A002R2EC | grep theasc.asc-mhl."
echo "$ $COMMAND"
eval $COMMAND
echo

echo
echo "Step 3: The files are verified again, and hashes are written into the extended attributes of"
echo "        the files."

echo
COMMAND="asc-mhl.py verify -s -wx $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
eval ../$COMMAND

echo
echo "Step 4: Inspecting extended attributes again - hash attributes are now set."

echo

COMMAND="/usr/bin/xattr -r -l $(pwd)/Output/scenario_$SCENARIO/A002R2EC | grep theasc.asc-mhl."
echo "$ $COMMAND"
eval $COMMAND

echo
