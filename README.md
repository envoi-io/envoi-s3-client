# Envoi S3 Client

## Overview

A utility that wraps several S3 clients to provide a consistent experience for S3 operations.

## Installation

You can install the utility by creating a symbolic link in the current user's bin directory using 
the following command:

```bash
ln -s src/envoi-s3.py /usr/local/bin/envoi-s3
```

## Prerequisites

- A supported S3 client, either [s4cmd](https://github.com/bloomreach/s4cmd) or [s5cmd](https://github.com/peak/s5cmd)

## Usage

### Commands

#### `envoi-s3 ls [path]`

List buckets and/or objects. If no path is provided then a bucket list will be returned.

#### `envoi-s3 put [source] [target]`

Upload local files using a S3 client.


### Options

#### `--client CLIENT`

Client can be either`s4cmd` or `s5cmd`. 
