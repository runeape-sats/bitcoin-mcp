# bitcoin_connection.py
# Utility module for establishing and testing connections to the Bitcoin Core node

import subprocess
import json
import logging
import os
from typing import Dict, Any, Optional, List
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Bitcoin connection settings loaded from environment variables
BITCOIN_CLI_PATH = os.environ.get("BITCOIN_CLI_PATH", "bitcoin-cli")
BITCOIN_DATADIR = os.environ.get("BITCOIN_DATADIR", None)
BITCOIN_CONF = os.environ.get("BITCOIN_CONF", None)
BITCOIN_NETWORK = os.environ.get("BITCOIN_NETWORK", "mainnet")

class BitcoinConnection:
    """Class to handle connection to Bitcoin Core via bitcoin-cli"""
    
    def __init__(self, cli_path: str = None, datadir: str = None, conf: str = None, network: str = None):
        """
        Initialize the Bitcoin connection
        
        Args:
            cli_path: Path to bitcoin-cli executable
            datadir: Bitcoin data directory
            conf: Path to bitcoin.conf
            network: Network to use (mainnet, testnet, regtest)
        """
        self.cli_path = cli_path or BITCOIN_CLI_PATH
        
        # If cli_path doesn't include a full path, try to find it in PATH
        if not os.path.isabs(self.cli_path) and '/' not in self.cli_path and '\\' not in self.cli_path:
            resolved_path = shutil.which(self.cli_path)
            if resolved_path:
                self.cli_path = resolved_path
        
        self.datadir = datadir or BITCOIN_DATADIR
        self.conf = conf or BITCOIN_CONF
        self.network = network or BITCOIN_NETWORK
        
    def test_connection(self) -> bool:
        """
        Test the connection to Bitcoin Core
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            result = self.run_command(["getblockchaininfo"])
            return "error" not in result
        except Exception as e:
            logger.error(f"Bitcoin connection test failed: {str(e)}")
            return False
            
    def run_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Run a bitcoin-cli command
        
        Args:
            command: List of command arguments to pass to bitcoin-cli
            
        Returns:
            Dict containing the parsed JSON response
            
        Raises:
            Exception if the command fails
        """
        # Build the complete command with bitcoin-cli path and any necessary options
        full_command = [self.cli_path]
        
        # Add optional arguments if specified
        if self.datadir:
            full_command.extend(["-datadir=" + self.datadir])
        if self.conf:
            full_command.extend(["-conf=" + self.conf])
        if self.network == "testnet":
            full_command.extend(["-testnet"])
        elif self.network == "regtest":
            full_command.extend(["-regtest"])
        
        # Add the actual command and its arguments
        full_command.extend(command)
        
        logger.debug(f"Running: {' '.join(full_command)}")
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON response
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Some commands return plain text, not JSON
                    return {"result": result.stdout.strip()}
            return {"result": "success"}
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.strip() if e.stderr else "Unknown error"
            logger.error(f"Bitcoin CLI error: {error_message}")
            return {"error": error_message}
        except Exception as e:
            logger.error(f"Error running bitcoin-cli: {str(e)}")
            return {"error": str(e)}
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection
        
        Returns:
            Dict with connection information
        """
        info = {
            "cli_path": self.cli_path,
            "datadir": self.datadir,
            "conf": self.conf,
            "network": self.network,
            "connected": False,
            "version": None,
            "chain": None,
            "blocks": None
        }
        
        try:
            blockchain_info = self.run_command(["getblockchaininfo"])
            network_info = self.run_command(["getnetworkinfo"])
            
            if "error" not in blockchain_info and "error" not in network_info:
                info["connected"] = True
                info["version"] = network_info.get("version", None)
                info["subversion"] = network_info.get("subversion", None)
                info["chain"] = blockchain_info.get("chain", None)
                info["blocks"] = blockchain_info.get("blocks", None)
                info["headers"] = blockchain_info.get("headers", None)
                info["verification_progress"] = blockchain_info.get("verificationprogress", None)
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            
        return info

def get_bitcoin_connection(cli_path: str = None, datadir: str = None, conf: str = None, network: str = None) -> BitcoinConnection:
    """
    Get a Bitcoin connection instance
    
    Args:
        cli_path: Path to bitcoin-cli executable
        datadir: Bitcoin data directory
        conf: Path to bitcoin.conf
        network: Network to use (mainnet, testnet, regtest)
        
    Returns:
        BitcoinConnection instance
    """
    return BitcoinConnection(cli_path, datadir, conf, network)