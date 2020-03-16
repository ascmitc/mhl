#!/bin/bash

SCENARIO="02"

echo
echo "Scenario $SCENARIO:"
echo "In this scenario a copy is made, and then a copy of the copy. Two ASC-MHL are created during"
echo "this process, documenting the history of both copy processes."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A: The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive."

echo

COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND


echo
echo "Step 2A: The card is copied from the travel drive to a file server."
echo "Step 2B: The files are verified on the file server."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"

eval ../$COMMAND

echo
