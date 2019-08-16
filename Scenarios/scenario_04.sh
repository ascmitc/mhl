#!/bin/bash

SCENARIO="04"

echo
echo "Scenario $SCENARIO:"
echo "Copying a folder to a travel drive and from there to a file server with hash mismatch in one"
echo "file."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A (imaginary): The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
echo "Step 3A (imaginary): The card is copied from the travel drive to a file server. During the copy"
echo "         the file \"Sidecar.txt\" becomes corrupt (altered)."

# altering the file
echo "!!" >> ./Output/scenario_$SCENARIO/A002R2EC/Sidecar.txt


echo "Step 3B: The files are verified on the file server."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
echo "Step 4: The files are verified again, against the hashes from ASC-MHL file with generation 02."

echo
COMMAND="asc-mhl.py verify -s -g 2 $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND


echo
