# bitcoin_utils.py
# Utility functions for working with Bitcoin blockchain data

import json
import logging
from typing import Dict, Any, List, Optional, Union
import time
from datetime import datetime

from bitcoin_connection import get_bitcoin_connection
from bitcoin_transactions import parse_kwargs

logger = logging.getLogger(__name__)

def get_blockchain_info() -> Dict[str, Any]:
    """
    Get information about the blockchain
    
    Returns:
        Dict with blockchain information
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getblockchaininfo"])

def get_network_info() -> Dict[str, Any]:
    """
    Get information about the network
    
    Returns:
        Dict with network information
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getnetworkinfo"])

def get_block(block_hash: str, verbose: int = 1) -> Dict[str, Any]:
    """
    Get block data
    
    Args:
        block_hash: Block hash
        verbose: Verbosity level (0-2)
            0: Returns a hex-encoded string
            1: Returns an object with block header and transaction IDs
            2: Returns an object with block header and transaction objects
            
    Returns:
        Block data
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getblock", block_hash, str(verbose)])

def get_block_hash(height: int) -> str:
    """
    Get block hash for a specific height
    
    Args:
        height: Block height
        
    Returns:
        Block hash
    """
    bitcoin = get_bitcoin_connection()
    result = bitcoin.run_command(["getblockhash", str(height)])
    
    # Handle different response formats
    if isinstance(result, dict):
        if "result" in result:
            return result["result"]
        if "error" in result:
            logger.error(f"Error getting block hash: {result['error']}")
            return json.dumps(result)
    
    return result

def get_block_stats(hash_or_height: Union[str, int]) -> Dict[str, Any]:
    """
    Get block statistics
    
    Args:
        hash_or_height: Block hash or height
        
    Returns:
        Block statistics
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getblockstats", str(hash_or_height)])

def get_chain_tips() -> List[Dict[str, Any]]:
    """
    Get information about chain tips
    
    Returns:
        List of chain tips
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getchaintips"])

def get_difficulty() -> float:
    """
    Get current difficulty
    
    Returns:
        Current difficulty
    """
    bitcoin = get_bitcoin_connection()
    result = bitcoin.run_command(["getdifficulty"])
    
    # Handle different response formats
    if isinstance(result, dict):
        if "result" in result:
            return result["result"]
        if "error" in result:
            logger.error(f"Error getting difficulty: {result['error']}")
            return 0.0
    
    return result

def get_mempool_info() -> Dict[str, Any]:
    """
    Get mempool information
    
    Returns:
        Mempool information
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getmempoolinfo"])

def get_raw_mempool(verbose: bool = False) -> Dict[str, Any]:
    """
    Get all transaction IDs in the mempool
    
    Args:
        verbose: Whether to include detailed information
        
    Returns:
        Mempool transactions
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["getrawmempool", "true" if verbose else "false"])

def get_tx_out(txid: str, n: int, include_mempool: bool = True) -> Dict[str, Any]:
    """
    Get information about an unspent transaction output
    
    Args:
        txid: Transaction ID
        n: Output index
        include_mempool: Whether to include mempool
        
    Returns:
        Unspent transaction output information
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command([
        "gettxout", 
        txid, 
        str(n), 
        "true" if include_mempool else "false"
    ])

def get_tx_out_set_info() -> Dict[str, Any]:
    """
    Get statistics about the unspent transaction output set
    
    Returns:
        UTXO set statistics
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["gettxoutsetinfo"])

def get_chain_tx_stats(nblocks: int = 30, blockhash: str = None) -> Dict[str, Any]:
    """
    Get statistics about the total number and rate of transactions in the chain
    
    Args:
        nblocks: Number of blocks to look at
        blockhash: The hash of the block that ends the window
        
    Returns:
        Chain transaction statistics
    """
    bitcoin = get_bitcoin_connection()
    
    command = ["getchaintxstats"]
    if nblocks is not None:
        command.append(str(nblocks))
        if blockhash is not None:
            command.append(blockhash)
    
    return bitcoin.run_command(command)

def estimate_smart_fee(conf_target: int, estimate_mode: str = "CONSERVATIVE") -> Dict[str, Any]:
    """
    Estimate fee rate needed for a transaction to confirm within a certain number of blocks
    
    Args:
        conf_target: Confirmation target in blocks
        estimate_mode: Fee estimate mode (UNSET, ECONOMICAL, CONSERVATIVE)
        
    Returns:
        Estimated fee rate
    """
    bitcoin = get_bitcoin_connection()
    return bitcoin.run_command(["estimatesmartfee", str(conf_target), estimate_mode])

def get_blockchain_status() -> str:
    """
    Get a comprehensive status report about the blockchain
    
    Returns:
        JSON string with blockchain status
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # Get blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        
        # Get network info
        network_info = bitcoin.run_command(["getnetworkinfo"])
        
        # Get mempool info
        mempool_info = bitcoin.run_command(["getmempoolinfo"])
        
        # Get current fee estimates
        fee_estimate_2 = bitcoin.run_command(["estimatesmartfee", "2", "CONSERVATIVE"])
        fee_estimate_6 = bitcoin.run_command(["estimatesmartfee", "6", "CONSERVATIVE"])
        fee_estimate_24 = bitcoin.run_command(["estimatesmartfee", "24", "CONSERVATIVE"])
        
        # Format time values
        if "mediantime" in blockchain_info:
            try:
                median_time = datetime.fromtimestamp(blockchain_info["mediantime"]).isoformat()
                blockchain_info["median_time_iso"] = median_time
            except Exception:
                pass
        
        # Build the status report
        status = {
            "blockchain": blockchain_info,
            "network": {
                "version": network_info.get("version", ""),
                "subversion": network_info.get("subversion", ""),
                "protocol_version": network_info.get("protocolversion", ""),
                "connections": network_info.get("connections", 0),
                "connections_in": network_info.get("connections_in", 0),
                "connections_out": network_info.get("connections_out", 0),
                "relay_fee": network_info.get("relayfee", 0),
                "network_active": network_info.get("networkactive", True),
                "networks": network_info.get("networks", [])
            },
            "mempool": {
                "size": mempool_info.get("size", 0),
                "bytes": mempool_info.get("bytes", 0),
                "usage": mempool_info.get("usage", 0),
                "max_memory": mempool_info.get("maxmempool", 0),
                "min_fee": mempool_info.get("mempoolminfee", 0),
                "min_relay_fee": mempool_info.get("minrelaytxfee", 0)
            },
            "fee_estimates": {
                "blocks_2": fee_estimate_2.get("feerate", 0) if isinstance(fee_estimate_2, dict) else 0,
                "blocks_6": fee_estimate_6.get("feerate", 0) if isinstance(fee_estimate_6, dict) else 0,
                "blocks_24": fee_estimate_24.get("feerate", 0) if isinstance(fee_estimate_24, dict) else 0
            },
            "time": int(time.time()),
            "time_iso": datetime.now().isoformat()
        }
        
        return json.dumps(status, indent=2)
    except Exception as e:
        logger.error(f"Error getting blockchain status: {str(e)}")
        return json.dumps({"error": str(e)})

def get_detailed_block_info(block_identifier: Union[str, int]) -> str:
    """
    Get detailed information about a specific block
    
    Args:
        block_identifier: Block hash or height
        
    Returns:
        JSON string with detailed block information
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # If a height was provided, get the hash
        block_hash = block_identifier
        if isinstance(block_identifier, int) or block_identifier.isdigit():
            block_hash = bitcoin.run_command(["getblockhash", str(block_identifier)])
            
            # Handle potential errors
            if isinstance(block_hash, dict) and "error" in block_hash:
                return json.dumps(block_hash)
            if isinstance(block_hash, dict) and "result" in block_hash:
                block_hash = block_hash["result"]
        
        # Get block data
        block_data = bitcoin.run_command(["getblock", block_hash, "1"])
        
        if "error" in block_data:
            return json.dumps(block_data)
            
        # Get block stats
        try:
            block_stats = bitcoin.run_command(["getblockstats", block_hash])
            if "error" not in block_stats:
                # Merge block stats into the result
                for key, value in block_stats.items():
                    if key not in block_data:
                        block_data[f"stats_{key}"] = value
        except Exception as stats_error:
            logger.error(f"Error getting block stats: {str(stats_error)}")
            block_data["stats_error"] = str(stats_error)
            
        # Format time values
        if "time" in block_data:
            try:
                block_time = datetime.fromtimestamp(block_data["time"]).isoformat()
                block_data["time_iso"] = block_time
            except Exception:
                pass
                
        # Add transaction count
        if "tx" in block_data:
            block_data["tx_count"] = len(block_data["tx"])
            
        # Get next and previous block hashes for navigation
        if "height" in block_data:
            height = block_data["height"]
            
            # Only get previous block if not genesis block
            if height > 0:
                try:
                    prev_hash = bitcoin.run_command(["getblockhash", str(height - 1)])
                    block_data["prev_hash_lookup"] = prev_hash
                except Exception:
                    pass
                    
            # Try to get next block
            try:
                next_hash = bitcoin.run_command(["getblockhash", str(height + 1)])
                block_data["next_hash_lookup"] = next_hash
            except Exception:
                # No next block exists yet
                pass
        
        return json.dumps(block_data, indent=2)
    except Exception as e:
        logger.error(f"Error getting detailed block info: {str(e)}")
        return json.dumps({"error": str(e)})

def search_blocks(kwargs_str: str) -> str:
    """
    Search for blocks within a specific range or meeting criteria
    
    Args:
        kwargs_str: String containing parameters as key=value pairs or JSON
            Supported parameters:
            - start_height: Starting height (default: chain tip - 10)
            - end_height: Ending height (default: chain tip)
            - start_time: Start time in Unix timestamp
            - end_time: End time in Unix timestamp
            - min_size: Minimum block size in bytes
            - max_size: Maximum block size in bytes
            - min_tx_count: Minimum transaction count
            - max_tx_count: Maximum transaction count
            - include_details: Whether to include full block details (default: false)
            
    Returns:
        JSON string with matching blocks
    """
    try:
        kwargs = parse_kwargs(kwargs_str)
        bitcoin = get_bitcoin_connection()
        
        # Get blockchain info to determine chain height
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        current_height = blockchain_info.get("blocks", 0)
        
        # Parse parameters with defaults
        start_height = kwargs.get("start_height", max(0, current_height - 10))
        end_height = kwargs.get("end_height", current_height)
        start_time = kwargs.get("start_time", None)
        end_time = kwargs.get("end_time", None)
        min_size = kwargs.get("min_size", None)
        max_size = kwargs.get("max_size", None)
        min_tx_count = kwargs.get("min_tx_count", None)
        max_tx_count = kwargs.get("max_tx_count", None)
        include_details = kwargs.get("include_details", False)
        
        # Limit range to protect against very large queries
        if end_height - start_height > 100:
            end_height = start_height + 100
            
        # Collect matching blocks
        matching_blocks = []
        
        for height in range(start_height, end_height + 1):
            try:
                # Get block hash for this height
                block_hash = bitcoin.run_command(["getblockhash", str(height)])
                
                # Handle different response formats
                if isinstance(block_hash, dict):
                    if "error" in block_hash:
                        continue
                    if "result" in block_hash:
                        block_hash = block_hash["result"]
                
                # Get block data
                block_data = bitcoin.run_command(["getblock", block_hash, "1"])
                
                if "error" in block_data:
                    continue
                    
                # Apply filters
                # Time filter
                if start_time is not None and block_data.get("time", 0) < start_time:
                    continue
                if end_time is not None and block_data.get("time", 0) > end_time:
                    continue
                    
                # Size filter
                if min_size is not None and block_data.get("size", 0) < min_size:
                    continue
                if max_size is not None and block_data.get("size", 0) > max_size:
                    continue
                    
                # Transaction count filter
                tx_count = len(block_data.get("tx", []))
                if min_tx_count is not None and tx_count < min_tx_count:
                    continue
                if max_tx_count is not None and tx_count > max_tx_count:
                    continue
                
                # Add to results
                if include_details:
                    matching_blocks.append(block_data)
                else:
                    # Include only essential information
                    matching_blocks.append({
                        "hash": block_data.get("hash", ""),
                        "height": block_data.get("height", 0),
                        "time": block_data.get("time", 0),
                        "time_iso": datetime.fromtimestamp(block_data.get("time", 0)).isoformat(),
                        "size": block_data.get("size", 0),
                        "tx_count": tx_count,
                        "difficulty": block_data.get("difficulty", 0),
                        "weight": block_data.get("weight", 0)
                    })
            except Exception as block_error:
                logger.error(f"Error processing block at height {height}: {str(block_error)}")
                continue
        
        result = {
            "count": len(matching_blocks),
            "start_height": start_height,
            "end_height": end_height,
            "filters": {
                "start_time": start_time,
                "end_time": end_time,
                "min_size": min_size,
                "max_size": max_size,
                "min_tx_count": min_tx_count,
                "max_tx_count": max_tx_count
            },
            "blocks": matching_blocks
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching blocks: {str(e)}")
        return json.dumps({"error": str(e)})
