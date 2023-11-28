#!/usr/bin/env python3

import boto3
import logging
import optparse
import os
import shutil
import subprocess
import sys

logger = logging.Logger('envoi-s3')
logger.setLevel(logging.WARN)


def augment_common(cmd_args, env_vars):
    access_key = os.getenv('S3_ACCESS_KEY')
    if access_key:
        env_vars.setdefault('AWS_ACCESS_KEY_ID', access_key)

    secret_key = os.getenv('S3_SECRET_KEY')
    if secret_key:
        env_vars.setdefault('AWS_SECRET_ACCESS_KEY', secret_key)

    return cmd_args, env_vars


def augment_aws_arguments(cmd_args, env_vars):

    cmd_args, env_vars = augment_common(cmd_args, env_vars)

    endpoint_url = os.getenv('AWS_ENDPOINT_URL_S3') or os.getenv('S3_ENDPOINT_URL')
    if '--endpoint-url' not in cmd_args and endpoint_url is not None:
        cmd_args.extend(['--endpoint-url', endpoint_url])

    return cmd_args, env_vars


def augment_s4cmd_arguments(cmd_args, env_vars):
    """
    Augments the given cmd_args list with necessary arguments to configure s4cmd.

    :param cmd_args: The list of command line arguments for s4cmd.
    :param env_vars: Environment variables to be set in the subprocess environment.
    :return: The updated cmd_args list with additional arguments.
    """

    cmd_args, env_vars = augment_common(cmd_args, env_vars)

    endpoint_url = os.getenv('AWS_ENDPOINT_URL_S3') or os.getenv('S3_ENDPOINT_URL')
    if endpoint_url is not None:
        cmd_args.extend(['--endpoint', endpoint_url])

    if '--region' not in cmd_args:
        region = os.getenv('S3_REGION')
        if region is not None:
            cmd_args.extend(['--region', region])

    return cmd_args, env_vars


def augment_s5cmd_arguments(cmd_args, env_vars):
    cmd_args, env_vars = augment_common(cmd_args, env_vars)

    return cmd_args, env_vars


def aws_wrapper(cmd_args, env_vars):
    """
    Wrapper function for running the `aws s3` command with supplied arguments.

    :param cmd_args: List of command line arguments to be pass to aws s3.
    :param env_vars: Environment variables to be set in the subprocess environment.
    :return: Process object representing the completed command.
    """
    cmd_args, env_vars = augment_aws_arguments(cmd_args, env_vars)

    cmd = ['aws', 's3'] + cmd_args

    process = subprocess.run(cmd, check=True, env=env_vars)

    return process


def s4cmd_wrapper(cmd_args, env_vars):
    """
    Wrapper function for running the `s4cmd` command with supplied arguments.

    :param cmd_args: List of command line arguments to be pass to s4cmd.
    :param env_vars: Environment variables to be set in the subprocess environment.
    :return: Process object representing the completed command.
    """
    cmd_args, env_vars = augment_s4cmd_arguments(cmd_args, env_vars)

    # Create the s4cmd command
    cmd = ['s4cmd'] + cmd_args

    # Run the command and capture the output
    process = subprocess.run(cmd, check=True, env=env_vars)

    return process


def s5cmd_wrapper(cmd_args, env_vars):
    """
    Wrapper function for running the `s5cmd` command with supplied arguments.

    :param cmd_args: A list of additional arguments to pass to the s5cmd command.
    :param env_vars: Environment variables to be set in the subprocess environment.
    :return: Process object representing the completed command.
    """
    cmd_args, env_vars = augment_s5cmd_arguments(cmd_args, env_vars)

    # Create the s4cmd command
    cmd = ['s5cmd'] + cmd_args

    # Run the command and capture the output
    process = subprocess.run(cmd, check=True, env=env_vars)

    return process


def parse_command_line(cli_args, env_vars):
    parser = optparse.OptionParser(
        description='Envoi S3 Command Line Utility',
    )

    parser.add_option('--client', dest='client_name', default='s5cmd',
                      help='The client to use when communicating with S3.')
    parser.add_option('--role-arn', dest='role_arn', default=None,
                      help='The arn for the IAM Role to assume.')

    (opt, args) = parser.parse_args(cli_args)
    return opt, args, env_vars


def determine_client(opts):
    """Determine the client executable command.

    :return: The first executable command from ['s5cmd', 's4cmd', 'aws'] or None if none of the commands are found.
    """
    return opts.client_name or determine_first_executable_command(['s5cmd', 's4cmd', 'aws'])


def determine_first_executable_command(commands):
    """
    :param commands: a list of commands to check for executability
    :return: the first command from the list that is executable

    This method takes a list of commands as input and returns the first command from the list that is executable on the
    operating system. It checks if each command is executable using the shutil.which() function. If a command is found
    to be executable, it is returned immediately, otherwise the next command is checked. If none of the commands are
    found to be executable, None is returned.

    Example usage:

        commands = ['ls', 'dir', 'echo']
        first_executable_command = determine_first_executable_command(commands)

        if first_executable_command:
            print(f"The first executable command is: {first_executable_command}")
        else:
            print("No executable command found.")

    The determine_first_executable_command() method depends on the shutil module, which provides the which() function
    for checking if a command is executable. Additionally, this method also depends on the os module for retrieving the
    operating system environment.

    Note: This method does not handle cases where a command requires a different syntax or additional arguments to be
    executed successfully. Its purpose is to simply determine if a command is executable or not.
    """
    for cmd in commands:
        if shutil.which(cmd) is not None:
            return cmd


def assume_role_using_arn(role_arn, env_vars):
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='envoi-s3'
    )
    credentials = assumed_role_object['Credentials']
    env_vars['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
    env_vars['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
    env_vars['AWS_SESSION_TOKEN'] = credentials['SessionToken']
    return env_vars


def execute_client(client_name, cli_args, env_vars):
    """
    Execute a client based on the given client name and command-line arguments.

    :param client_name: The name of the client to execute ('aws', 's4cmd', or 's5cmd').
    :param cli_args: The command-line arguments to be passed to the client.
    :param env_vars:

    :return: None
    """
    process = None
    exit_code = 0
    try:
        if client_name == 's4cmd':
            process = s4cmd_wrapper(cli_args, env_vars)
        elif client_name == 's5cmd':
            process = s5cmd_wrapper(cli_args, env_vars)
        elif client_name == 'aws':
            process = aws_wrapper(cli_args, env_vars)
        else:
            logger.error(f"Unknown client name: {client_name}")
            exit_code = 1

        if process:
            exit_code = process.returncode

    except Exception as e:
        logger.error(f"Error running client {client_name}: {str(e)}")
        exit_code = 1

    return exit_code


def is_executable(cmd):
    """
    Check if a given command is executable.

    :param cmd: The command to check for executability.
    :return: True if the command is executable, False otherwise.
    """
    return shutil.which(cmd)


def main():
    cli_args = sys.argv[1:]
    env_vars = os.environ.copy()
    (opts, remaining_args, env_vars) = parse_command_line(cli_args, env_vars)
    client_name = determine_client(opts)

    role_arn = opts.role_arn
    if role_arn:
        env_vars = assume_role_using_arn(role_arn, env_vars)

    exit_code = execute_client(client_name, remaining_args, env_vars)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
