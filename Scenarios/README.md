### Sample output of all scenario scipts

## scenario_01.sh
```

Scenario 01:
This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is
created with hashes of all files on the card.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_01/A002R2EC
traversing […]Output/scenario_01/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_01/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl

```
## scenario_01A.sh
```

Scenario 01A:
This is the most basic example, this time with adding additional descriptive metadata.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive, and additional metadata is added to the
         ASC-MHL file.

$ asc-mhl.py verify -n "John Doe" -u jodo -c "This is a verification in scenario 01A" […]Output/scenario_01A/A002R2EC
traversing […]Output/scenario_01A/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_01A/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl

```
## scenario_02.sh
```

Scenario 02:
In this scenario a copy is made, and then a copy of the copy. Two ASC-MHL are created during
this process, documenting the history of both copy processes.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_02/A002R2EC
traversing […]Output/scenario_02/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_02/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl

Step 2A (imaginary): The card is copied from the travel drive to a file server.
Step 2B: The files are verified on the file server.

$ asc-mhl.py verify […]Output/scenario_02/A002R2EC
traversing […]Output/scenario_02/A002R2EC
ascmhl_path […]Output/scenario_02/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095838_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
  xxhash: 9742fa8b8e6c78c6                 new       : asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl
  xxhash: 3ab5a4166b9bde44                 verified  : Sidecar.txt
writing […]Output/scenario_02/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0002.ascmhl

```
## scenario_03.sh
```

Scenario 03:
In this scenario the first hashes are created using the xxhash format. Different hash formats
might be required by systems used further down the workflow, so the second copy is verified
against the existin xxhash hashes, and additional MD5 hashes can be created and stored during
that process on demand.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive by creating xxhash hashes.

$ asc-mhl.py verify […]Output/scenario_03/A002R2EC
traversing […]Output/scenario_03/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_03/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl

Step 2A (imaginary): The card is copied from the travel drive to a file server.
Step 2B: The files are verified on the file server, and additional ("secondary") MD5 hashes
         are created.

$ asc-mhl.py verify -h "MD5" […]Output/scenario_03/A002R2EC
traversing […]Output/scenario_03/A002R2EC
ascmhl_path […]Output/scenario_03/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095838_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
     MD5: f5ac8127b3b6b85cdc13f237c6005d80 new       : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
     MD5: 614dd0e977becb4c6f7fa99e64549b12 new       : Clips/A002C007_141024_R2EC.mov
     MD5: 7f672157e303a202f16f21a31e807561 new       : asc-mhl/A002R2EC_2019-10-08_095838_0001.ascmhl
  xxhash: 3ab5a4166b9bde44                 verified  : Sidecar.txt
     MD5: 6425c5a180ca0f420dd2b25be4536a91 new       : Sidecar.txt
writing […]Output/scenario_03/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095838_0002.ascmhl

```
## scenario_04.sh
```

Scenario 04:
Copying a folder to a travel drive and from there to a file server with hash mismatch in one
file.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_04/A002R2EC
traversing […]Output/scenario_04/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_04/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl

Step 3A (imaginary): The card is copied from the travel drive to a file server. During the copy
         the file "Sidecar.txt" becomes corrupt (altered).
Step 3B: The files are verified on the file server.

$ asc-mhl.py verify […]Output/scenario_04/A002R2EC
traversing […]Output/scenario_04/A002R2EC
ascmhl_path […]Output/scenario_04/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
  xxhash: 65a33f334db5306f                 new       : asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
! xxhash: d60ed728dc0b8d2c                 failed    : Sidecar.txt
writing […]Output/scenario_04/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0002.ascmhl

Step 4: The files are verified again, against the hashes from ASC-MHL file with generation 02.

$ asc-mhl.py verify -s -g 2 […]Output/scenario_04/A002R2EC
traversing […]Output/scenario_04/A002R2EC
ascmhl_path […]Output/scenario_04/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0002.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095839_0002.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
  xxhash: 65a33f334db5306f                 verified  : asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: bbcd9a0358a41cca                 new       : asc-mhl/A002R2EC_2019-10-08_095839_0002.ascmhl
  xxhash: d60ed728dc0b8d2c                 verified  : Sidecar.txt

```
## scenario_05.sh
```

Scenario 05:
Copying two single reels to a "Reels" folder on a travel drive, and the entire "Reels" 
folder to a server.

Step 1A (imaginary): The card A002 is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_05/Reels/A002R2EC
traversing […]Output/scenario_05/Reels/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_05/Reels/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl

Step 2A (imaginary): The card A003 is copied to a travel drive.
Step 2B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_05/Reels/A003R2EC
traversing […]Output/scenario_05/Reels/A003R2EC
ascmhl_path None
  xxhash: 52392f79a36d6571                 original  : Clips/A003C011_141024_R2EC.mov
  xxhash: 104a1844733bba51                 original  : Clips/A003C012_141024_R2EC.mov
  xxhash: e5dda75a353d8b34                 original  : Sidecar.txt
writing […]Output/scenario_05/Reels/A003R2EC/asc-mhl/A003R2EC_2019-10-08_095839_0001.ascmhl

Step 3A (imaginary): The entire folder "Reels" is copied from the travel drive to a file
         server.
Step 3B: A summary file "Summary.txt" is added to the "Reels" folder.
Step 3C: The "Reels" folder is verified on the file server.

$ asc-mhl.py verify […]Output/scenario_05/Reels
traversing […]Output/scenario_05/Reels
ascmhl_path None
verifying against hashes from A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
  xxhash: 2495bd319f8ac480                 new       : asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 3ab5a4166b9bde44                 verified  : Sidecar.txt
writing […]Output/scenario_05/Reels/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0002.ascmhl
verifying against hashes from A003R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 52392f79a36d6571                 verified  : Clips/A003C011_141024_R2EC.mov
  xxhash: 104a1844733bba51                 verified  : Clips/A003C012_141024_R2EC.mov
  xxhash: e144e379e657b4a0                 new       : asc-mhl/A003R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: e5dda75a353d8b34                 verified  : Sidecar.txt
writing […]Output/scenario_05/Reels/A003R2EC/asc-mhl/A003R2EC_2019-10-08_095839_0002.ascmhl
  xxhash: b7219c53e6093233                 original  : Summary.txt
writing […]Output/scenario_05/Reels/asc-mhl/Reels_2019-10-08_095839_0001.ascmhl

```
## scenario_06.sh
```

Scenario 06:
Calculating and displaying directory hashes during verification. Folder hashes might be required
by systems used further down the workflow, so these hashes can be created "on the fly" from
hashes in the ASC-MHL files on demand.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_06/A002R2EC
traversing […]Output/scenario_06/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_06/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl

Step 2: The files are verified again, and folder hashes are calculated and displayed (folder
        hashes are created by concatenating the hashes of the contents of a directory and
        hashing that collected hash data).

$ asc-mhl.py verify -s -d […]Output/scenario_06/A002R2EC
traversing […]Output/scenario_06/A002R2EC
ascmhl_path […]Output/scenario_06/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
d xxhash: 4c226b42e27d7af3                 directory : Clips
  xxhash: 4e9e2eaf94660819                 new       : asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
d xxhash: 73269ba5af597142                 directory : asc-mhl
  xxhash: 3ab5a4166b9bde44                 verified  : Sidecar.txt
d xxhash: 6a02da4a38c3c74a                 directory : .

```
## scenario_07.sh
```

Scenario 07:
Writing extended attributes (xxattr) to file system (for files and folders) during verification.
Hashes stored in extended attributes might be required by systems used further down the
workflow, so the hashes in the ASC-MHL file can be written to extended attributes on demand.

Step 1A (imaginary): The card is copied to a travel drive.
Step 1B: The files are verified on the travel drive.

$ asc-mhl.py verify […]Output/scenario_07/A002R2EC
traversing […]Output/scenario_07/A002R2EC
ascmhl_path None
  xxhash: 0ea03b369a463d9d                 original  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 original  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3ab5a4166b9bde44                 original  : Sidecar.txt
writing […]Output/scenario_07/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl

Step 2: Inspecting extended attributes - no hash attributes are set.

$ /usr/bin/xattr -r -l […]Output/scenario_07/A002R2EC | grep theasc.asc-mhl.


Step 3: The files are verified again, and hashes are written into the extended attributes of
        the files.

$ asc-mhl.py verify -s -wx […]Output/scenario_07/A002R2EC
traversing […]Output/scenario_07/A002R2EC
ascmhl_path […]Output/scenario_07/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
verifying against hashes from A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 0ea03b369a463d9d                 verified  : Clips/A002C006_141024_R2EC.mov
  xxhash: 7680e5f98f4a80fd                 verified  : Clips/A002C007_141024_R2EC.mov
  xxhash: 3f58f07bab2cc46a                 new       : asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl
  xxhash: 3ab5a4166b9bde44                 verified  : Sidecar.txt

Step 4: Inspecting extended attributes again - hash attributes are set now.

$ /usr/bin/xattr -r -l […]Output/scenario_07/A002R2EC | grep theasc.asc-mhl.
[…]Output/scenario_07/A002R2EC/Clips/A002C006_141024_R2EC.mov: com.theasc.asc-mhl.xxhash: 0ea03b369a463d9d
[…]Output/scenario_07/A002R2EC/Clips/A002C007_141024_R2EC.mov: com.theasc.asc-mhl.xxhash: 7680e5f98f4a80fd
[…]Output/scenario_07/A002R2EC/Sidecar.txt: com.theasc.asc-mhl.xxhash: 3ab5a4166b9bde44
[…]Output/scenario_07/A002R2EC/asc-mhl/A002R2EC_2019-10-08_095839_0001.ascmhl: com.theasc.asc-mhl.xxhash: 3f58f07bab2cc46a

```

The created ASC-MHL files can be found in the ``asc-mhl`` folders amongst the scenario output files in the [Output/](Output/) folder.

