import argparse
import functools

from prompt_toolkit import HTML, print_formatted_text
from web3 import Web3

from .api.base_api import BaseAPIException
from .safe_operator import (ExistingOwnerException,
                            FallbackHandlerNotSupportedException,
                            InvalidMasterCopyException,
                            NonExistingOwnerException, NotEnoughEtherToSend,
                            NotEnoughSignatures, NotEnoughTokenToSend,
                            SafeAlreadyUpdatedException, SafeOperator,
                            SameFallbackHandlerException,
                            SameMasterCopyException, SenderRequiredException,
                            ThresholdLimitException)


def check_ethereum_address(address: str) -> bool:
    """
    Ethereum address validator for ArgParse
    :param address:
    :return:
    """
    if not Web3.isChecksumAddress(address):
        raise argparse.ArgumentTypeError(f'{address} is not a valid checksummed ethereum address')
    return address


def safe_exception(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except BaseAPIException as e:
            if e.args:
                print_formatted_text(HTML(f'<b><ansired>{e.args[0]}</ansired></b>'))
        except NotEnoughSignatures as e:
            print_formatted_text(HTML(f'<ansired>Cannot find enough owners to sign. {e.args[0]} missing</ansired>'))
        except SenderRequiredException:
            print_formatted_text(HTML(f'<ansired>Please load a default sender</ansired>'))
        except ExistingOwnerException as e:
            print_formatted_text(HTML(f'<ansired>Owner {e.args[0]} is already an owner of the Safe'
                                      f'</ansired>'))
        except NonExistingOwnerException as e:
            print_formatted_text(HTML(f'<ansired>Owner {e.args[0]} is not an owner of the Safe'
                                      f'</ansired>'))
        except ThresholdLimitException:
            print_formatted_text(HTML(f'<ansired>Having less owners than threshold is not allowed'
                                      f'</ansired>'))
        except SameFallbackHandlerException as e:
            print_formatted_text(HTML(f'<ansired>Fallback handler {e.args[0]} is the current one</ansired>'))
        except FallbackHandlerNotSupportedException:
            print_formatted_text(HTML(f'<ansired>Fallback handler is not supported for your Safe, '
                                      f'you need to <b>update</b> first</ansired>'))
        except SameMasterCopyException as e:
            print_formatted_text(HTML(f'<ansired>Master Copy {e.args[0]} is the current one</ansired>'))
        except InvalidMasterCopyException as e:
            print_formatted_text(HTML(f'<ansired>Master Copy {e.args[0]} is not valid</ansired>'))
        except SafeAlreadyUpdatedException:
            print_formatted_text(HTML(f'<ansired>Safe is already updated</ansired>'))
        except (NotEnoughEtherToSend, NotEnoughTokenToSend) as e:
            print_formatted_text(HTML(f'<ansired>Cannot find enough to send. Current balance is {e.args[0]}'
                                      f'</ansired>'))
    return wrapper


def get_prompt_parser(safe_operator: SafeOperator) -> argparse.ArgumentParser:
    """
    Returns an ArgParse capable of decoding and executing the Safe commands
    :param safe_operator:
    :return:
    """
    prompt_parser = argparse.ArgumentParser(prog='')
    subparsers = prompt_parser.add_subparsers()

    @safe_exception
    def show_cli_owners(args):
        safe_operator.show_cli_owners()

    @safe_exception
    def load_cli_owners(args):
        safe_operator.load_cli_owners(args.keys)

    @safe_exception
    def unload_cli_owners(args):
        safe_operator.unload_cli_owners(args.addresses)

    @safe_exception
    def add_owner(args):
        safe_operator.add_owner(args.address)

    @safe_exception
    def remove_owner(args):
        safe_operator.remove_owner(args.address)

    @safe_exception
    def change_fallback_handler(args):
        safe_operator.change_fallback_handler(args.address)

    @safe_exception
    def change_master_copy(args):
        safe_operator.change_master_copy(args.address)

    @safe_exception
    def change_threshold(args):
        safe_operator.change_threshold(args.threshold)

    @safe_exception
    def send_ether(args):
        safe_operator.send_ether(args.address, args.value)

    @safe_exception
    def send_erc20(args):
        safe_operator.send_erc20(args.address, args.token_address, args.value)

    @safe_exception
    def send_erc721(args):
        safe_operator.send_erc721(args.address, args.token_address, args.token_id)

    @safe_exception
    def get_threshold(args):
        safe_operator.get_threshold()

    @safe_exception
    def get_nonce(args):
        safe_operator.get_nonce()

    @safe_exception
    def get_owners(args):
        safe_operator.get_owners()

    @safe_exception
    def enable_module(args):
        safe_operator.enable_module(args.address)

    @safe_exception
    def disable_module(args):
        safe_operator.disable_module(args.address)

    @safe_exception
    def update_version(args):
        safe_operator.update_version()

    @safe_exception
    def get_info(args):
        safe_operator.print_info()

    @safe_exception
    def get_refresh(args):
        safe_operator.refresh_safe_cli_info()

    @safe_exception
    def get_balances(args):
        safe_operator.get_balances()

    @safe_exception
    def get_history(args):
        safe_operator.get_transaction_history()

    # Cli owners
    parser_show_cli_owners = subparsers.add_parser('show_cli_owners')
    parser_show_cli_owners.set_defaults(func=show_cli_owners)

    parser_load_cli_owners = subparsers.add_parser('load_cli_owners')
    parser_load_cli_owners.add_argument('keys', type=str, nargs='+')
    parser_load_cli_owners.set_defaults(func=load_cli_owners)

    parser_unload_cli_owners = subparsers.add_parser('unload_cli_owners')
    parser_unload_cli_owners.add_argument('addresses', type=check_ethereum_address, nargs='+')
    parser_unload_cli_owners.set_defaults(func=unload_cli_owners)

    # Change threshold
    parser_change_threshold = subparsers.add_parser('change_threshold')
    parser_change_threshold.add_argument('threshold', type=int)
    parser_change_threshold.set_defaults(func=change_threshold)

    # Add owner
    parser_add_owner = subparsers.add_parser('add_owner')
    parser_add_owner.add_argument('address', type=check_ethereum_address)
    parser_add_owner.set_defaults(func=add_owner)

    # Remove owner
    parser_remove_owner = subparsers.add_parser('remove_owner')
    parser_remove_owner.add_argument('address', type=check_ethereum_address)
    parser_remove_owner.set_defaults(func=remove_owner)

    # Change FallbackHandler
    parser_change_master_copy = subparsers.add_parser('change_fallback_handler')
    parser_change_master_copy.add_argument('address', type=check_ethereum_address)
    parser_change_master_copy.set_defaults(func=change_fallback_handler)

    # Change MasterCopy
    parser_change_master_copy = subparsers.add_parser('change_master_copy')
    parser_change_master_copy.add_argument('address', type=check_ethereum_address)
    parser_change_master_copy.set_defaults(func=change_master_copy)

    # Update Safe to last version
    parser_change_master_copy = subparsers.add_parser('update')
    parser_change_master_copy.set_defaults(func=update_version)

    # Send ether
    parser_send_ether = subparsers.add_parser('send_ether')
    parser_send_ether.add_argument('address', type=check_ethereum_address)
    parser_send_ether.add_argument('value', type=int)
    parser_send_ether.set_defaults(func=send_ether)

    # Send erc20
    parser_send_erc20 = subparsers.add_parser('send_erc20')
    parser_send_erc20.add_argument('address', type=check_ethereum_address)
    parser_send_erc20.add_argument('token_address', type=check_ethereum_address)
    parser_send_erc20.add_argument('value', type=int)
    parser_send_erc20.set_defaults(func=send_erc20)

    # Send erc721
    parser_send_erc20 = subparsers.add_parser('send_erc721')
    parser_send_erc20.add_argument('address', type=check_ethereum_address)
    parser_send_erc20.add_argument('token_address', type=check_ethereum_address)
    parser_send_erc20.add_argument('token_id', type=int)
    parser_send_erc20.set_defaults(func=send_erc721)

    # Retrieve threshold, nonce or owners
    parser_get_threshold = subparsers.add_parser('get_threshold')
    parser_get_threshold.set_defaults(func=get_threshold)
    parser_get_nonce = subparsers.add_parser('get_nonce')
    parser_get_nonce.set_defaults(func=get_nonce)
    parser_get_owners = subparsers.add_parser('get_owners')
    parser_get_owners.set_defaults(func=get_owners)

    # Enable and disable modules
    parser_enable_module = subparsers.add_parser('enable_module')
    parser_enable_module.add_argument('address', type=check_ethereum_address)
    parser_enable_module.set_defaults(func=enable_module)
    parser_disable_module = subparsers.add_parser('disable_module')
    parser_disable_module.add_argument('address', type=check_ethereum_address)
    parser_disable_module.set_defaults(func=disable_module)

    # Info and refresh
    parser_info = subparsers.add_parser('info')
    parser_info.set_defaults(func=get_info)
    parser_refresh = subparsers.add_parser('refresh')
    parser_refresh.set_defaults(func=get_refresh)

    # Tx-History
    # TODO Use subcommands
    parser_info = subparsers.add_parser('balances')
    parser_info.set_defaults(func=get_balances)
    parser_info = subparsers.add_parser('history')
    parser_info.set_defaults(func=get_history)

    return prompt_parser
