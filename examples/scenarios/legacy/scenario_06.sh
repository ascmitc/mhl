#!/bin/bash

SCENARIO="06"

echo
echo "Scenario $SCENARIO:"
echo "Calculating and displaying directory hashes during verification. Folder hashes might be required"
echo "by systems used further down the workflow, so these hashes can be created \"on the fly\" from"
echo "hashes in the ASC-MHL files on demand."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A (imaginary): The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
eval ../$COMMAND

echo
echo "Step 2: The files are verified again, and folder hashes are calculated and displayed (folder"
echo "        hashes are created by concatenating the hashes of the contents of a directory and"
echo "        hashing that collected hash data)."

echo
COMMAND="asc-mhl.py verify -s -d $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
eval ../$COMMAND

echo

