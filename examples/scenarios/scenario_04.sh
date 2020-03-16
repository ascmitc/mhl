#!/bin/bash

SCENARIO="04"

echo
echo "Scenario $SCENARIO:"
echo "Copying a folder to a travel drive and from there to a file server with a hash mismatch in"
echo "one file."

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
echo "Step 2A: The card is copied from the travel drive to a file server. During the copy"
echo "         the file \"Sidecar.txt\" becomes corrupt (altered)."

# altering the file
echo "!!" >> ./Output/scenario_$SCENARIO/A002R2EC/Sidecar.txt


echo "Step 2B: The files are verified on the file server."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
