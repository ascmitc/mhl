#!/bin/bash

SCENARIO="01A"

echo
echo "Scenario $SCENARIO:"
echo "This is the most basic example, this time adding additional descriptive metadata."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A: The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive, and additional metadata is added to the"
echo "         ASC-MHL file."

echo

COMMAND="asc-mhl.py verify -n \"John Doe\" -u jodo -c \"This is a verification in scenario 01A\" $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
eval ../$COMMAND

echo
