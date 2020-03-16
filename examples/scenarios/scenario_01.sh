#!/bin/bash

SCENARIO="01"

echo
echo "Scenario $SCENARIO:"
echo "This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is"
echo "created with hashes of all files on the card."

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
