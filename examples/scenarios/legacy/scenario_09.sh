#!/bin/bash

SCENARIO="09"

echo
echo "Scenario $SCENARIO:"
echo "In this scenario two copies are made, while the first MHL file is digitally signed."
echo "The signature gets checked afterwards."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/

echo
echo "Step 1A: The card is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive, the ASCMHL file gets signed with"
echo "         a private key."

echo

COMMAND="asc-mhl.py verify -csi abc@example.com -csp $(pwd)/Template/Material/Scenario09/abc-private-key.pem $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
echo "Step 2A: The card is copied again."
echo "Step 2B: The files are verified on the travel drive."

echo

COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND


echo
echo "Step 3A: The chain is verified."

echo

COMMAND="asc-mhl.py verify -s $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"
../$COMMAND

echo 
echo "Step 3B: The signature is checked with a public key."
echo

COMMAND="asc-mhl.py checksignature -g 1 -csp $(pwd)/Template/Material/Scenario09/abc-public-key.pem $(pwd)/Output/scenario_$SCENARIO/A002R2EC"
echo "$ $COMMAND"

eval ../$COMMAND

echo
