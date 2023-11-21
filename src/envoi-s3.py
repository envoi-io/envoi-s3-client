#!/usr/bin/env python
import logging
import optparse
import os
import shutil
import subprocess
import sys

logger = logging.Logger('envoi-s3')
logger.setLevel(logging.WARN)

def augment_s4cmd_arguments(cmd_args):
    """
    Augments the given cmd_args list with necessary arguments to configure s4cmd.

    :param cmd_args: The list of command line arguments for s4cmd.
    :return: The updated cmd_args list with additional arguments.
    """
    access_key = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('S3_ACCESS_KEY')
    if access_key:
        pass

    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('S3_SECRET_KEY')
    if secret_key:
        pass

    endpoint_url = os.getenv('AWS_ENDPOINT_URL_S3') or os.getenv('S3_ENDPOINT_URL')
    if endpoint_url is not None:
        cmd_args.extend(['--endpoint', endpoint_url])

    if '--region' not in cmd_args:
        region = os.getenv('S3_REGION')
        if region is not None:
            cmd_args.extend(['--region', region])

    return cmd_args


def augment_s5cmd_arguments(cmd_args):
    pass


def s4cmd_wrapper(cmd_args, *args):
    cmd_args = augment_s4cmd_arguments(cmd_args)

    # Create the s4cmd command
    cmd = ['s4cmd'] + cmd_args

    # Run the command and capture the output
    process = subprocess.run(cmd, check=True)

    return process


def s5cmd_wrapper(cmd_args, *args):
    """
    Wrapper function for running the s5cmd command with supplied arguments.

    :param cmd_args: A list of additional arguments to pass to the s5cmd command.
    :param args: Additional positional arguments to be passed to augment_s4cmd_arguments() function.
    :return: None

    This function takes a list of additional command line arguments (cmd_args) and optional positional arguments (args). It calls the augment_s4cmd_arguments() function to modify the cmd_args list if necessary. Then, it creates the s5cmd command by concatenating the 's5cmd' string with cmd_args. Finally, it runs the command using the subprocess.run() function, with the 'check=True' parameter to raise an exception if the command fails.
    """
    cmd_args = augment_s4cmd_arguments(cmd_args)

    # Create the s4cmd command
    cmd = ['s5cmd'] + cmd_args

    # Run the command and capture the output
    process = subprocess.run(cmd, check=True)

    return process

def parse_command_line(cli_args):
    parser = optparse.OptionParser(
        description='Envoi S3 Command Line Utility',
    )

    parser.add_option('--client', dest='client_name', default='s5cmd', help='The client to use when communicating with S3.')
    (opt, args) = parser.parse_args(cli_args)
    return opt, args


def determine_client(opts):
    """Determine the client executable command.

    :return: The first executable command from ['s5cmd', 's4cmd'] or None if none of the commands are found.
    """
    return opts.client_name or determine_first_executable_command(['s5cmd', 's4cmd'])


def determine_first_executable_command(commands):
    """
    :param commands: a list of commands to check for executability
    :return: the first command from the list that is executable

    This method takes a list of commands as input and returns the first command from the list that is executable on the operating system. It checks if each command is executable using the shutil.which() function. If a command is found to be executable, it is returned immediately, otherwise the next command is checked. If none of the commands are found to be executable, None is returned.

    Example usage:

        commands = ['ls', 'dir', 'echo']
        first_executable_command = determine_first_executable_command(commands)

        if first_executable_command:
            print(f"The first executable command is: {first_executable_command}")
        else:
            print("No executable command found.")

    The determine_first_executable_command() method depends on the shutil module, which provides the which() function for checking if a command is executable. Additionally, this method also depends on the os module for retrieving the operating system environment.

    Note: This method does not handle cases where a command requires a different syntax or additional arguments to be executed successfully. Its purpose is to simply determine if a command is executable or not.
    """
    for cmd in commands:
        if shutil.which(cmd) is not None:
            return cmd


def execute_client(client_name, cli_args):
    """
    Execute a client based on the given client name and command-line arguments.

    :param client_name: The name of the client to execute ('s4cmd' or 's5cmd').
    :param cli_args: The command-line arguments to be passed to the client.

    :return: None
    """
    process = None
    exit_code = 0
    try:
        if client_name == 's4cmd':
            process = s4cmd_wrapper(cli_args)
        elif client_name == 's5cmd':
            process = s5cmd_wrapper(cli_args)
        else:
            logger.error(f"Unknown client name: {client_name}")
            exit_code = 1

        if process:
            exit_code = process.returncode



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
    (opts, remaining_args) = parse_command_line(cli_args)
    client_name = determine_client(opts)

    exit_code = execute_client(client_name, remaining_args)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
