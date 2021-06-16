### Sample output of all test scenarios 


## scenario_01
```
Scenario 01:
This is the most basic example. A camera card is copied to a travel drive and an ASC-MHL file is
created with hashes of all files on the card.

Assume the source card /A002R2EC is copied to a travel drive /travel_01.

Seal the copy on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/A002R2EC -h xxh64
Sealing folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
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
Sealing folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

Sealing the folder A002R2EC again on the file server
this will verify all hashes, check for completeness and create a second generation

$ ascmhl.py create -v /file_server/A002R2EC -h xxh64
Sealing folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  OK
  verified                      Clips/A002C007_141024_R2EC.mov  OK
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  verified                      Sidecar.txt  OK
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
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
Sealing folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

Sealing the folder A002R2EC again on the file server using MD5 hash format
this will verify all existing xxHashes, check for completeness,
and create a second generation with additional (new) MD5 hashes.

$ ascmhl.py create -v -h md5 /file_server/A002R2EC
Sealing folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  OK
  created new, verified hash for          Clips/A002C006_141024_R2EC.mov  md5: f5ac8127b3b6b85cdc13f237c6005d80
  verified                      Clips/A002C007_141024_R2EC.mov  OK
  created new, verified hash for          Clips/A002C007_141024_R2EC.mov  md5: 614dd0e977becb4c6f7fa99e64549b12
  calculated directory hash for Clips  md5: 5bfa20fc4fb2c4a8e6fafcd07b85061b (content), a36f6434c9cb1f5fc44a7dc80aa6400a (structure)
  verified                      Sidecar.txt  OK
  created new, verified hash for          Sidecar.txt  md5: 6425c5a180ca0f420dd2b25be4536a91
  calculated root hash  md5: ef2c1c34ebac7d493ffb0e79efaa0a1d (content), b2ae676728fea69eb9f826defee34d07 (structure)
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
Sealing folder at path: /travel_01/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the folder A002R2EC is copied there from the travel drive to a file server at /file_server.

afterwards we simulate that during the copy the Sidecar.txt got corrupt (altered
by modifying the file content

Sealing the folder A002R2EC again on the file server.
This will verify all existing hashes and fail because Sidecar.txt was altered.
An error is shown and create a new generation that documents the failed verification

$ ascmhl.py create -v /file_server/A002R2EC -h xxh64
Sealing folder at path: /file_server/A002R2EC ...
  verified                      Clips/A002C006_141024_R2EC.mov  OK
  verified                      Clips/A002C007_141024_R2EC.mov  OK
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
ERROR: hash mismatch for        Sidecar.txt  xxh64 (old): 3ab5a4166b9bde44, xxh64 (new): 70d2cf31aaa3eac4
  calculated root hash  xxh64: 2ca8e358d014d65e (content), 574ab2d2afc981cd (structure)
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
Sealing folder at path: /travel_01/Reels/A002R2EC ...
  created original hash for     Clips/A002C006_141024_R2EC.mov  xxh64: 0ea03b369a463d9d
  created original hash for     Clips/A002C007_141024_R2EC.mov  xxh64: 7680e5f98f4a80fd
  calculated directory hash for Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  created original hash for     Sidecar.txt  xxh64: 3ab5a4166b9bde44
  calculated root hash  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
Created new generation ascmhl/0001_A002R2EC_2020-01-16_091500.mhl



Assume a second card /A003R2EC is copied to the same Reels folder on travel drive /travel_01.

Seal the copy of A003R2EC on the travel drive /travel_01 to create the original mhl generation.

$ ascmhl.py create -v /travel_01/Reels/A003R2EC -h xxh64
Sealing folder at path: /travel_01/Reels/A003R2EC ...
  created original hash for     Clips/A003C011_141024_R2EC.mov  xxh64: 52392f79a36d6571
  created original hash for     Clips/A003C012_141024_R2EC.mov  xxh64: 5dbca064ddddd6fc
  calculated directory hash for Clips  xxh64: 8d220e119e7b3b04 (content), 2be728e9147a4b67 (structure)
  created original hash for     Sidecar.txt  xxh64: e5dda75a353d8b34
  calculated root hash  xxh64: f6c455e7941fe0f3 (content), 0729474d03751da0 (structure)
Created new generation ascmhl/0001_A003R2EC_2020-01-16_091500.mhl



Assume the travel drive arrives at a facility on the next day.
And the common Reels folder is copied from the travel drive to a file server at /file_server.

Afterwards an arbitrary file Summary.txt is added to the Reels folder.

Sealing the Reels folder on the file server.
This will verify all hashes, check for completeness and create two second generations
in the card sub folders A002R2EC and A003R2EC and an initial one for the Reels folder
with the original hash of the Summary.txt and references to the child histories
of the card sub folders.

$ ascmhl.py create -v /file_server/Reels -h xxh64
Sealing folder at path: /file_server/Reels ...
  verified                      A002R2EC/Clips/A002C006_141024_R2EC.mov  OK
  verified                      A002R2EC/Clips/A002C007_141024_R2EC.mov  OK
  calculated directory hash for A002R2EC/Clips  xxh64: 6d43a82e7a5d40f6 (content), a27e08b77ae22c78 (structure)
  verified                      A002R2EC/Sidecar.txt  OK
  calculated directory hash for A002R2EC  xxh64: 7e423206834bf81a (content), 574ab2d2afc981cd (structure)
  verified                      A003R2EC/Clips/A003C011_141024_R2EC.mov  OK
  verified                      A003R2EC/Clips/A003C012_141024_R2EC.mov  OK
  calculated directory hash for A003R2EC/Clips  xxh64: 8d220e119e7b3b04 (content), 2be728e9147a4b67 (structure)
  verified                      A003R2EC/Sidecar.txt  OK
  calculated directory hash for A003R2EC  xxh64: f6c455e7941fe0f3 (content), 0729474d03751da0 (structure)
  created original hash for     Summary.txt  xxh64: 0ac48e431d4538ba
  calculated root hash  xxh64: 3b7af44c2476dcd4 (content), e6546d6cea0092e2 (structure)
Created new generation A002R2EC/ascmhl/0002_A002R2EC_2020-01-17_143000.mhl
Created new generation A003R2EC/ascmhl/0002_A003R2EC_2020-01-17_143000.mhl
Created new generation ascmhl/0001_Reels_2020-01-17_143000.mhl


```

The ASC MHL files can be found in the ``ascmhl`` folders amongst the scenario output files in the [Output/](Output/) folder.

