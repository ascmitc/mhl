#!/bin/bash

SCENARIO="05"

echo
echo "Scenario $SCENARIO:"
echo "Copying two single reels to a \"Reels\" folder on a travel drive, and the entire \"Reels\" "
echo "folder to a server."

rm -rf ./Output/scenario_$SCENARIO
mkdir -p ./Output/scenario_$SCENARIO/Reels/
cp -r ./Template/A002R2EC ./Output/scenario_$SCENARIO/Reels/
cp -r ./Template/A003R2EC ./Output/scenario_$SCENARIO/Reels/

echo
echo "Step 1A (imaginary): The card A002 is copied to a travel drive."
echo "Step 1B: The files are verified on the travel drive."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/Reels/A002R2EC"
echo "$ $COMMAND"
../$COMMAND


echo
echo "Step 2A (imaginary): The card A003 is copied to a travel drive."
echo "Step 2B: The files are verified on the travel drive."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/Reels/A003R2EC"
echo "$ $COMMAND"
../$COMMAND

echo
echo "Step 3A (imaginary): The entire folder \"Reels\" is copied from the travel drive to a file"
echo "         server."
echo "Step 3B: A summary file \"Summary.txt\" is added to the \"Reels\" folder."

cp ./Template/Summary.txt ./Output/scenario_$SCENARIO/Reels/

echo "Step 3C: The \"Reels\" folder is verified on the file server."

echo
COMMAND="asc-mhl.py verify $(pwd)/Output/scenario_$SCENARIO/Reels"
echo "$ $COMMAND"
../$COMMAND

echo
