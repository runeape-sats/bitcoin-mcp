# bitcoin_mcp_server.py
# Main entry point for the Bitcoin MCP server that interfaces with bitcoin-cli

import logging
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Optional
import traceback
import os

from mcp.server.fastmcp import FastMCP, Context

# Import our modules
from bitcoin_connection import get_bitcoin_connection

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BitcoinMCPServer")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    
    try:
        logger.info("Bitcoin MCP server starting up")
        
        # Test bitcoin-cli connection on startup
        try:
            bitcoin = get_bitcoin_connection()
            if bitcoin.test_connection():
                connection_info = bitcoin.get_connection_info()
                logger.info(f"Successfully connected to Bitcoin Core")
                logger.info(f"  Network: {connection_info.get('chain', 'unknown')}")
                logger.info(f"  Blocks: {connection_info.get('blocks', 0)}")
                logger.info(f"  Version: {connection_info.get('version', 'unknown')} ({connection_info.get('subversion', '')})")
            else:
                logger.warning(f"Could not connect to Bitcoin Core on startup")
                logger.warning(f"Make sure Bitcoin Core is running and bitcoin-cli is available")
        except Exception as e:
            logger.warning(f"Could not connect to Bitcoin Core on startup: {str(e)}")
            logger.warning(f"Make sure Bitcoin Core is running and bitcoin-cli is available")
        
        # Return an empty context
        yield {}
    finally:
        # Shutdown logging
        logger.info("Bitcoin MCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "BitcoinMCP",
    description="Bitcoin Core integration through the Model Context Protocol",
    lifespan=server_lifespan
)

# Register Bitcoin Blockchain RPC tools
@mcp.tool()
async def get_bitfeed_3d_representation(ctx: Context, blockHeight: int, scale: float) -> str:
    """
    Get accurate 3D coordinates (x, y, z) and sizes (width, height, depth) of parcels from a BTC block based on Bitfeed representation. Units are in meters.

    Do not modify the individuall numbers because it breaks the accuracy of the visual representation as a whole. For any sizing or scaling adjustments, use the "scale" parameter (default: 0.5 meter).
    
    Returns a JSON object with details about the specific Block including:
    parcels: array of 3D representations of transactions in 3D sizes and coordinates, totalWidth: the final width of the visual representation (in meters), 
    parcelColor: hex color code, 
    blockNumber: the block height number,
    totalParcels: total transactions
    """
    try:
        # Import our Bitfeed implementation
        from bitfeed import get_bitfeed_3d
        
        # Call the get_bitfeed_3d function with the block height parameter
        result = await get_bitfeed_3d(blockHeight, scale)
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_bitfeed_3d_representation: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error getting Bitfeed 3D representation: {str(e)}"

@mcp.tool()
def get_blockchain_info(ctx: Context) -> str:
    """
    Get information about the current state of the blockchain and network.
    
    Returns a JSON object with details about the current blockchain state including:
    chain, blocks, headers, bestblockhash, difficulty, mediantime, verificationprogress,
    pruned (if applicable), and other blockchain metrics.
    """
    try:
        from bitcoin_utils import get_blockchain_info
        result = get_blockchain_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_blockchain_info: {str(e)}")
        return f"Error getting blockchain info: {str(e)}"

@mcp.tool()
def get_block_hash(ctx: Context, height: int) -> str:
    """
    Get the block hash for a specific block height.
    
    Parameters:
    - height: Block height to get the hash for. Block height only increases as more blocks are mined.
    
    Returns the block hash as a hex string.
    """
    try:
        from bitcoin_utils import get_block_hash
        result = get_block_hash(height)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_block_hash: {str(e)}")
        return f"Error getting block hash: {str(e)}"

@mcp.tool()
def get_block(ctx: Context, blockhash: str, verbosity: int = 1) -> str:
    """
    Get block data for a specific block hash.
    
    Parameters:
    - blockhash: The hash of the block to get
    - verbosity: The verbosity level (0-2, default=1)
      0: Returns a hex-encoded string of the block
      1: Returns an object with block header and transaction IDs
      2: Returns an object with block header and complete transaction objects
    
    Returns block data based on the specified verbosity level.
    """
    try:
        from bitcoin_utils import get_block
        result = get_block(blockhash, verbosity)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_block: {str(e)}")
        return f"Error getting block: {str(e)}"

@mcp.tool()
def get_block_stats(ctx: Context, hash_or_height: str) -> str:
    """
    Get computed statistics for a specific block.
    
    Parameters:
    - hash_or_height: Block hash or height to get statistics for
    
    Returns computed statistics about the specified block including averages 
    for feerate, txsize, and other metrics.
    """
    try:
        from bitcoin_utils import get_block_stats
        result = get_block_stats(hash_or_height)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_block_stats: {str(e)}")
        return f"Error getting block stats: {str(e)}"

@mcp.tool()
def get_chain_tips(ctx: Context) -> str:
    """
    Get information about all known chain tips in the node, including the main chain and any orphaned branches.
    
    Returns information about all known tips in the block tree, including the main chain and orphaned branches.
    """
    try:
        from bitcoin_utils import get_chain_tips
        result = get_chain_tips()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_chain_tips: {str(e)}")
        return f"Error getting chain tips: {str(e)}"

@mcp.tool()
def get_chain_tx_stats(ctx: Context, nblocks: int = 30, blockhash: str = None) -> str:
    """
    Get statistics about chain transaction volume.
    
    Parameters:
    - nblocks: Number of blocks to include in the stats (default: 30)
    - blockhash: The hash of the block that ends the window (default: chain tip)
    
    Returns statistics about chain transaction volume and rates.
    """
    try:
        from bitcoin_utils import get_chain_tx_stats
        result = get_chain_tx_stats(nblocks, blockhash)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_chain_tx_stats: {str(e)}")
        return f"Error getting chain transaction stats: {str(e)}"

@mcp.tool()
def get_difficulty(ctx: Context) -> str:
    """
    Get the current difficulty of the Bitcoin network.
    
    Returns the current proof-of-work difficulty as a multiple of the minimum difficulty.
    """
    try:
        from bitcoin_utils import get_difficulty
        result = get_difficulty()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_difficulty: {str(e)}")
        return f"Error getting difficulty: {str(e)}"

@mcp.tool()
def get_mempool_info(ctx: Context) -> str:
    """
    Get information about the node's current transaction memory pool.
    
    Returns details about the memory pool including size, memory usage, and fee statistics.
    """
    try:
        from bitcoin_utils import get_mempool_info
        result = get_mempool_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_mempool_info: {str(e)}")
        return f"Error getting mempool info: {str(e)}"

@mcp.tool()
def get_tx_out(ctx: Context, txid: str, n: int, include_mempool: bool = True) -> str:
    """
    Get details about an unspent transaction output (UTXO).
    
    Parameters:
    - txid: The transaction id
    - n: The output number (vout)
    - include_mempool: Whether to include the mempool (default: true)
    
    Returns details about the specified unspent transaction output, if it exists in the UTXO set.
    """
    try:
        from bitcoin_utils import get_tx_out
        result = get_tx_out(txid, n, include_mempool)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_tx_out: {str(e)}")
        return f"Error getting transaction output: {str(e)}"

@mcp.tool()
def get_tx_out_set_info(ctx: Context) -> str:
    """
    Get statistics about the unspent transaction output (UTXO) set.
    
    Returns statistics about the UTXO set including total amount, number of transactions, 
    and disk size usage.
    """
    try:
        from bitcoin_utils import get_tx_out_set_info
        result = get_tx_out_set_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_tx_out_set_info: {str(e)}")
        return f"Error getting transaction output set info: {str(e)}"

@mcp.tool()
def get_raw_transaction(ctx: Context, txid: str, verbose: bool = True, blockhash: str = None) -> str:
    """
    Get raw transaction data.
    
    Parameters:
    - txid: The transaction ID to get data for
    - verbose: If true, returns a JSON object, otherwise hex-encoded string (default: true)
    - blockhash: Optional hash of the block containing the transaction
    
    Returns the raw transaction data, either as a hex string or JSON object depending on 'verbose' parameter.
    """
    try:
        from bitcoin_transactions import get_transaction
        result = get_transaction(txid, verbose, blockhash)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_raw_transaction: {str(e)}")
        return f"Error getting raw transaction: {str(e)}"

@mcp.tool()
def decode_raw_transaction(ctx: Context, hexstring: str) -> str:
    """
    Decode a raw transaction hex string to a JSON object.
    
    Parameters:
    - hexstring: The hex string of the raw transaction
    
    Returns the decoded transaction as a JSON object.
    """
    try:
        from bitcoin_transactions import decode_transaction
        result = decode_transaction(hexstring)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in decode_raw_transaction: {str(e)}")
        return f"Error decoding raw transaction: {str(e)}"

@mcp.tool()
def estimate_smart_fee(ctx: Context, conf_target: int, estimate_mode: str = "CONSERVATIVE") -> str:
    """
    Estimate the fee rate needed for a transaction to be confirmed within a certain number of blocks.
    
    Parameters:
    - conf_target: Number of blocks to aim for confirmation
    - estimate_mode: Fee estimate mode (UNSET, ECONOMICAL, CONSERVATIVE) - default: CONSERVATIVE
    
    Returns an estimate of the fee rate (in BTC/kB) needed for a transaction 
    to be confirmed within conf_target blocks.
    """
    try:
        from bitcoin_utils import estimate_smart_fee
        result = estimate_smart_fee(conf_target, estimate_mode)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in estimate_smart_fee: {str(e)}")
        return f"Error estimating smart fee: {str(e)}"

@mcp.tool()
def get_network_info(ctx: Context) -> str:
    """
    Get information about the node's network connections and settings.
    
    Returns information about the node's connection to the network, including
    version, protocol version, timeoffset, connections count, and other network-related settings.
    """
    try:
        from bitcoin_utils import get_network_info
        result = get_network_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in get_network_info: {str(e)}")
        return f"Error getting network info: {str(e)}"

# Advanced Analytics Tools

@mcp.tool()
def get_blockchain_status(ctx: Context) -> str:
    """
    Get a comprehensive status report about the current state of the blockchain.
    
    Returns a detailed JSON report including blockchain state, network status, mempool info,
    fee estimates, and other metrics.
    """
    try:
        from bitcoin_utils import get_blockchain_status
        return get_blockchain_status()
    except Exception as e:
        logger.error(f"Error in get_blockchain_status: {str(e)}")
        return f"Error getting blockchain status: {str(e)}"

@mcp.tool()
def get_detailed_block_info(ctx: Context, block_identifier: str) -> str:
    """
    Get detailed information about a specific block.
    
    Parameters:
    - block_identifier: Block hash or height
    
    Returns a comprehensive JSON object with detailed block information including
    block header, transaction summary, and additional statistics.
    """
    try:
        from bitcoin_utils import get_detailed_block_info
        return get_detailed_block_info(block_identifier)
    except Exception as e:
        logger.error(f"Error in get_detailed_block_info: {str(e)}")
        return f"Error getting detailed block info: {str(e)}"

@mcp.tool()
def analyze_transaction(ctx: Context, txid: str) -> str:
    """
    Analyze a transaction with detailed information.
    
    Parameters:
    - txid: Transaction ID to analyze
    
    Returns a comprehensive JSON analysis of the transaction including inputs, outputs,
    fees, and other relevant metrics.
    """
    try:
        from bitcoin_transactions import analyze_transaction
        return analyze_transaction(txid)
    except Exception as e:
        logger.error(f"Error in analyze_transaction: {str(e)}")
        return f"Error analyzing transaction: {str(e)}"

@mcp.tool()
def get_difficulty_history(ctx: Context, blocks: int = 10) -> str:
    """
    Get the difficulty adjustment history.
    
    Parameters:
    - blocks: Number of difficulty adjustment periods to analyze (default: 10)
    
    Returns a JSON history of difficulty adjustments including percentage changes
    and timeframes.
    """
    try:
        from bitcoin_analytics import get_difficulty_history
        return get_difficulty_history(blocks)
    except Exception as e:
        logger.error(f"Error in get_difficulty_history: {str(e)}")
        return f"Error getting difficulty history: {str(e)}"

@mcp.tool()
def get_fee_history(ctx: Context, blocks: int = 10) -> str:
    """
    Get the transaction fee history over a number of recent blocks.
    
    Parameters:
    - blocks: Number of recent blocks to analyze (default: 10)
    
    Returns a JSON history of transaction fees including averages, minimums,
    maximums, and other statistics.
    """
    try:
        from bitcoin_analytics import get_fee_history
        return get_fee_history(blocks)
    except Exception as e:
        logger.error(f"Error in get_fee_history: {str(e)}")
        return f"Error getting fee history: {str(e)}"

@mcp.tool()
def get_hashrate_estimate(ctx: Context, blocks: int = 144) -> str:
    """
    Estimate the current network hashrate.
    
    Parameters:
    - blocks: Number of recent blocks to use for the estimate (default: 144)
    
    Returns a JSON estimate of the network hashrate in various units (TH/s, PH/s, EH/s).
    """
    try:
        from bitcoin_analytics import get_hashrate_estimate
        return get_hashrate_estimate(blocks)
    except Exception as e:
        logger.error(f"Error in get_hashrate_estimate: {str(e)}")
        return f"Error estimating hashrate: {str(e)}"

@mcp.tool()
def get_block_time_distribution(ctx: Context, blocks: int = 144) -> str:
    """
    Analyze the distribution of time between blocks.
    
    Parameters:
    - blocks: Number of recent blocks to analyze (default: 144)
    
    Returns a JSON analysis of block time distribution including averages,
    medians, and standard deviations.
    """
    try:
        from bitcoin_analytics import get_block_time_distribution
        return get_block_time_distribution(blocks)
    except Exception as e:
        logger.error(f"Error in get_block_time_distribution: {str(e)}")
        return f"Error analyzing block time distribution: {str(e)}"

@mcp.tool()
def search_blocks(ctx: Context, kwargs_str: str) -> str:
    """
    Search for blocks within a specific range or meeting criteria.
    
    Parameters:
    - kwargs_str: String containing parameters as key=value pairs or JSON
      Example: "start_height=680000 end_height=680100 min_size=1000000"
      
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
    
    Returns a JSON list of blocks matching the specified criteria.
    """
    try:
        from bitcoin_utils import search_blocks
        return search_blocks(kwargs_str)
    except Exception as e:
        logger.error(f"Error in search_blocks: {str(e)}")
        return f"Error searching blocks: {str(e)}"

@mcp.tool()
def analyze_blockchain(ctx: Context, kwargs_str: str) -> str:
    """
    Perform a comprehensive analysis of the blockchain.
    
    Parameters:
    - kwargs_str: String containing parameters as key=value pairs or JSON
      Example: "timespan=24 difficulty_periods=5 fee_blocks=144"
      
    Supported parameters:
    - timespan: Time period to analyze in hours (default: 24)
    - difficulty_periods: Number of difficulty periods to analyze (default: 5)
    - fee_blocks: Number of blocks to analyze for fees (default: 144)
    - hashrate_blocks: Number of blocks to analyze for hashrate (default: 144)
    - mempool_analysis: Whether to include mempool analysis (default: true)
    
    Returns a comprehensive JSON analysis of the blockchain including difficulty,
    hashrate, fees, block time distribution, and other metrics.
    """
    try:
        from bitcoin_analytics import analyze_blockchain
        return analyze_blockchain(kwargs_str)
    except Exception as e:
        logger.error(f"Error in analyze_blockchain: {str(e)}")
        return f"Error analyzing blockchain: {str(e)}"

# If this module is run directly, start the server
if __name__ == "__main__":
    try:
        logger.info("Starting Bitcoin MCP server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running Bitcoin MCP server: {str(e)}")
        traceback.print_exc()
