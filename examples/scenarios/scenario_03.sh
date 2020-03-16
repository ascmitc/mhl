#!/bin/bash

SCENARIO="03"

echo
echo "Scenario $SCENARIO:"
echo "In this scenario the first hashes are created using the xxhash format. Different hash formats"
echo "might be required by systems used further down the workflow, so the second copy is verified"
echo "against the existing xxhash hashes, and additional MD5 hashes can be created and stored during" 
echo "that process on demand."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A: The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive by creating xxhash hashes."

echo

COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
echo "Step 2A: The card is copied from the travel drive to a file server."
echo "Step 2B: The files are verified on the file server, and additional (\"secondary\") MD5 hashes"
echo "         are created."

echo
COMMAND="asc-mhl.py verify -h \"MD5\" $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"

eval ../$COMMAND

echo
