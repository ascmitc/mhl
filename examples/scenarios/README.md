### Sample output of all test scenarios 


## scenario_01
```
Scenario 01:
This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is
created with hashes of all files on the card.

Assume the source card /A002R2EC is copied to a travel drive /travel_01.

Seal the copy on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/A002R2EC -h xxh64
Creating new generation for folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl


```

## scenario_02
```
Scenario 02:
In this scenario a copy is made, and then a copy of the copy. Two ASC-MHL are created during
this process, documenting the history of both copy processes.

Assume the source card /A002R2EC is copied to a travel drive /travel_01.

Seal the copy on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/A002R2EC -h xxh64
Creating new generation for folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

Creating new generation for the folder A002R2EC again on the file server
this will verify all hashes, check for completeness and create a second generation

$ ascmhl.py create -v /file_server/A002R2EC -h xxh64
Creating new generation for folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  xxh64: OK
  verified                      Clips/A002C007_141024_R2EC.mov  xxh64: OK
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  verified                      Sidecar.txt  xxh64: OK
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0002_A002R2EC_2020-01-17_143000.mhl


```

## scenario_03
```
Scenario 03:
In this scenario the first hashes are created using the xxhash format. Different hash formats
might be required by systems used further down the workflow, so the second copy is verified
against the existing xxhash hashes, and additional MD5 hashes can be created and stored during
that process on demand.

Assume the source card /A002R2EC is copied to a travel drive /travel_01.

Seal the copy on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/A002R2EC -h xxh64
Creating new generation for folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

Creating new generation for the folder A002R2EC again on the file server using MD5 hash format
this will verify all existing xxHashes, check for completeness,
and create a second generation with additional (new) MD5 hashes.

$ ascmhl.py create -v -h md5 /file_server/A002R2EC
Creating new generation for folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  xxh64: OK
  created new (verif.) hash for Clips/A002C006_141024_R2EC.mov  md5: f5ac8127b3b6b85cdc13f237c6005d80
  verified                      Clips/A002C007_141024_R2EC.mov  xxh64: OK
  created new (verif.) hash for Clips/A002C007_141024_R2EC.mov  md5: 614dd0e977becb4c6f7fa99e64549b12
  calculated directory hash for Clips  md5: 202a2d71b56b080d9b089c1f4f29a4ba (content), 4a739024fd19d928e9dea6bb5c480200 (structure)
  verified                      Sidecar.txt  xxh64: OK
  created new (verif.) hash for Sidecar.txt  md5: 6425c5a180ca0f420dd2b25be4536a91
  calculated root hash  md5: 6fae2da9bc6dca45486cb91bfea6db70 (content), be1f2eaed208efbed061845a64cacdfa (structure)
Created new generation ascmhl/0002_A002R2EC_2020-01-17_143000.mhl


```

## scenario_04
```
Scenario 04:
Copying a folder to a travel drive and from there to a file server with a hash mismatch in
one file.

Assume the source card /A002R2EC is copied to a travel drive /travel_01.

Seal the copy on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/A002R2EC -h xxh64
Creating new generation for folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

afterwards we simulate that during the copy the Sidecar.txt got corrupt (altered
by modifying the file content

Creating new generation for the folder A002R2EC again on the file server.
This will verify all existing hashes and fail because Sidecar.txt was altered.
An error is shown and create a new generation that documents the failed verification

$ ascmhl.py create -v /file_server/A002R2EC -h xxh64
Creating new generation for folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  xxh64: OK
  verified                      Clips/A002C007_141024_R2EC.mov  xxh64: OK
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
ERROR: hash mismatch for        Sidecar.txt  xxh64 (old): 3ab5a4166b9bde44, xxh64 (new): 70d2cf31aaa3eac4
  calculated root hash  xxh64: 8e52e9c3d15e055c (content), 32706d5f4b48f047 (structure)
Created new generation ascmhl/0002_A002R2EC_2020-01-17_143000.mhl
Error: Verification of files referenced in the ASC MHL history failed


```

## scenario_05
```
Scenario 05:
Copying two camera mags to a `Reels` folder on a travel drive, and the entire `Reels` folder
folder to a server.

Assume the source card /A002R2EC is copied to a Reels folder on travel drive /travel_01.

Seal the copy of A002R2EC on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/Reels/A002R2EC -h xxh64
Creating new generation for folder at path: /travel_01/Reels/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume a second card /A003R2EC is copied to the same Reels folder on travel drive /travel_01.

Seal the copy of A003R2EC on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/Reels/A003R2EC -h xxh64
Creating new generation for folder at path: /travel_01/Reels/A003R2EC ...
  created original hash for     Clips/A003C011_141024_R2EC.mov  xxh64: 52392f79a36d6571
  created original hash for     Clips/A003C012_141024_R2EC.mov  xxh64: 5dbca064ddddd6fc
  calculated directory hash for Clips  xxh64: f2afc6434255a53d (content), a25d5ca89c95f9e2 (structure)
  created original hash for     Sidecar.txt  xxh64: e5dda75a353d8b34
  calculated root hash  xxh64: 7a82373c131cf40a (content), 1131a950fcc55e4b (structure)
Created new generation ascmhl/0001_A003R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the common Reels folder is copied from the travel drive to a file server at /file_server.

Afterwards an arbitrary file Summary.txt is added to the Reels folder.

Creating new generation for the Reels folder on the file server.
This will verify all hashes, check for completeness and create two second generations
in the card sub folders A002R2EC and A003R2EC and an initial one for the Reels folder
with the original hash of the Summary.txt and references to the child histories
of the card sub folders.

$ ascmhl.py create -v /file_server/Reels -h xxh64
Creating new generation for folder at path: /file_server/Reels ...
  verified                      A002R2EC/Clips/A002C006_141024_R2EC.mov  xxh64: OK
  verified                      A002R2EC/Clips/A002C007_141024_R2EC.mov  xxh64: OK
  calculated directory hash for A002R2EC/Clips  xxh64: 4c226b42e27d7af3 (content), 906faa843d591a9f (structure)
  verified                      A002R2EC/Sidecar.txt  xxh64: OK
  calculated directory hash for A002R2EC  xxh64: 8d02114c32e28cbe (content), f557f8ca8e5a88ef (structure)
  verified                      A003R2EC/Clips/A003C011_141024_R2EC.mov  xxh64: OK
  verified                      A003R2EC/Clips/A003C012_141024_R2EC.mov  xxh64: OK
  calculated directory hash for A003R2EC/Clips  xxh64: f2afc6434255a53d (content), a25d5ca89c95f9e2 (structure)
  verified                      A003R2EC/Sidecar.txt  xxh64: OK
  calculated directory hash for A003R2EC  xxh64: 7a82373c131cf40a (content), 1131a950fcc55e4b (structure)
  created original hash for     Summary.txt  xxh64: 0ac48e431d4538ba
  calculated root hash  xxh64: 92950bc8fda076ec (content), 2c2ce52605558158 (structure)
Created new generation A002R2EC/ascmhl/0002_A002R2EC_2020-01-17_143000.mhl
Created new generation A003R2EC/ascmhl/0002_A003R2EC_2020-01-17_143000.mhl
Created new generation ascmhl/0001_Reels_2020-01-17_143000.mhl


```

The ASC MHL files can be found in the ``ascmhl`` folders amongst the scenario output files in the [Output/](Output/) folder.

