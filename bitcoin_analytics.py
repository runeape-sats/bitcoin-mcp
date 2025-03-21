# bitcoin_analytics.py
# Advanced analytics and data processing for Bitcoin blockchain data

import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import math

from bitcoin_connection import get_bitcoin_connection
from bitcoin_transactions import parse_kwargs
from bitcoin_utils import get_block_hash, get_block

logger = logging.getLogger(__name__)

def get_difficulty_history(blocks: int = 10) -> str:
    """
    Get the difficulty history over a number of difficulty adjustment periods
    
    Args:
        blocks: Number of difficulty adjustment periods to analyze
        
    Returns:
        JSON string with difficulty history
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # Get current blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        current_height = blockchain_info.get("blocks", 0)
        
        # Bitcoin adjusts difficulty every 2016 blocks
        adjustment_interval = 2016
        
        # Calculate the heights to check
        heights = []
        for i in range(blocks):
            # Find height of most recent adjustment block at or before current height
            adjustment_height = (current_height // adjustment_interval) * adjustment_interval
            # Go back i adjustment periods
            height = max(0, adjustment_height - (i * adjustment_interval))
            heights.append(height)
            
        # Sort heights in ascending order
        heights.sort()
        
        # Collect difficulty data
        difficulty_data = []
        
        for height in heights:
            try:
                # Get block hash
                block_hash = bitcoin.run_command(["getblockhash", str(height)])
                if isinstance(block_hash, dict) and "result" in block_hash:
                    block_hash = block_hash["result"]
                elif isinstance(block_hash, dict) and "error" in block_hash:
                    continue
                
                # Get block data
                block_data = bitcoin.run_command(["getblock", block_hash, "1"])
                if "error" in block_data:
                    continue
                    
                # Extract relevant data
                entry = {
                    "height": height,
                    "hash": block_data.get("hash", ""),
                    "time": block_data.get("time", 0),
                    "time_iso": datetime.fromtimestamp(block_data.get("time", 0)).isoformat(),
                    "difficulty": block_data.get("difficulty", 0),
                    "adjustment_interval": height // adjustment_interval
                }
                
                difficulty_data.append(entry)
            except Exception as block_error:
                logger.error(f"Error processing block at height {height}: {str(block_error)}")
                continue
                
        # Calculate difficulty changes
        for i in range(1, len(difficulty_data)):
            prev = difficulty_data[i-1]
            curr = difficulty_data[i]
            
            diff_change = curr["difficulty"] - prev["difficulty"]
            diff_change_pct = (diff_change / prev["difficulty"]) * 100 if prev["difficulty"] > 0 else 0
            
            curr["difficulty_change"] = diff_change
            curr["difficulty_change_percent"] = diff_change_pct
            
            # Calculate time between adjustments
            time_diff = curr["time"] - prev["time"]
            expected_time = adjustment_interval * 10 * 60  # 10 minutes per block
            time_diff_pct = (time_diff / expected_time) * 100 - 100
            
            curr["adjustment_time"] = time_diff
            curr["adjustment_time_days"] = round(time_diff / (24 * 60 * 60), 2)
            curr["time_deviation_percent"] = time_diff_pct
        
        result = {
            "current_height": current_height,
            "difficulty_adjustment_interval": adjustment_interval,
            "count": len(difficulty_data),
            "data": difficulty_data
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting difficulty history: {str(e)}")
        return json.dumps({"error": str(e)})

def get_fee_history(blocks: int = 10) -> str:
    """
    Get the fee history over a number of recent blocks
    
    Args:
        blocks: Number of recent blocks to analyze
        
    Returns:
        JSON string with fee history data
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # Get current blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        current_height = blockchain_info.get("blocks", 0)
        
        # Limit number of blocks to protect against very large queries
        if blocks > 100:
            blocks = 100
            
        # Collect fee data from recent blocks
        fee_data = []
        
        for height in range(current_height - blocks + 1, current_height + 1):
            try:
                # Get block hash
                block_hash = get_block_hash(height)
                if not block_hash or (isinstance(block_hash, dict) and "error" in block_hash):
                    continue
                
                # Get block stats
                block_stats = bitcoin.run_command(["getblockstats", block_hash])
                if "error" in block_stats:
                    continue
                    
                # Get block data for additional info
                block_data = get_block(block_hash, 1)
                if "error" in block_data:
                    continue
                    
                # Extract relevant fee data
                entry = {
                    "height": height,
                    "hash": block_data.get("hash", ""),
                    "time": block_data.get("time", 0),
                    "time_iso": datetime.fromtimestamp(block_data.get("time", 0)).isoformat(),
                    "total_fee": block_stats.get("totalfee", 0),
                    "feerate_mean": block_stats.get("feerate_mean", 0),
                    "feerate_median": block_stats.get("feerate_median", 0),
                    "feerate_min": block_stats.get("minfeerate", 0),
                    "feerate_max": block_stats.get("maxfeerate", 0),
                    "txs": block_stats.get("txs", 0),
                    "size": block_data.get("size", 0),
                    "weight": block_data.get("weight", 0),
                }
                
                # Calculate fee per byte
                if entry["size"] > 0:
                    entry["fee_per_byte"] = entry["total_fee"] / entry["size"]
                else:
                    entry["fee_per_byte"] = 0
                    
                fee_data.append(entry)
            except Exception as block_error:
                logger.error(f"Error processing block at height {height}: {str(block_error)}")
                continue
                
        # Calculate aggregate statistics
        if fee_data:
            total_fee = sum(b["total_fee"] for b in fee_data)
            total_size = sum(b["size"] for b in fee_data)
            total_txs = sum(b["txs"] for b in fee_data)
            
            # Calculate average fees
            avg_feerate_mean = sum(b["feerate_mean"] for b in fee_data) / len(fee_data)
            avg_feerate_median = sum(b["feerate_median"] for b in fee_data) / len(fee_data)
            
            # Find min and max
            min_feerate = min(b["feerate_min"] for b in fee_data) if fee_data else 0
            max_feerate = max(b["feerate_max"] for b in fee_data) if fee_data else 0
            
            # Sort for percentiles
            sorted_mean_feerates = sorted([b["feerate_mean"] for b in fee_data])
            
            # Calculate percentiles
            p25_index = math.floor(len(sorted_mean_feerates) * 0.25)
            p75_index = math.floor(len(sorted_mean_feerates) * 0.75)
            p25_feerate = sorted_mean_feerates[p25_index] if p25_index < len(sorted_mean_feerates) else 0
            p75_feerate = sorted_mean_feerates[p75_index] if p75_index < len(sorted_mean_feerates) else 0
        else:
            total_fee = 0
            total_size = 0
            total_txs = 0
            avg_feerate_mean = 0
            avg_feerate_median = 0
            min_feerate = 0
            max_feerate = 0
            p25_feerate = 0
            p75_feerate = 0
        
        result = {
            "current_height": current_height,
            "blocks_analyzed": len(fee_data),
            "summary": {
                "total_fee": total_fee,
                "total_size_bytes": total_size,
                "total_transactions": total_txs,
                "avg_fee_per_block": total_fee / len(fee_data) if fee_data else 0,
                "avg_txs_per_block": total_txs / len(fee_data) if fee_data else 0,
                "avg_feerate_mean": avg_feerate_mean,
                "avg_feerate_median": avg_feerate_median,
                "min_feerate": min_feerate,
                "max_feerate": max_feerate,
                "p25_feerate": p25_feerate,
                "p75_feerate": p75_feerate
            },
            "data": fee_data
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting fee history: {str(e)}")
        return json.dumps({"error": str(e)})

def get_hashrate_estimate(blocks: int = 144) -> str:
    """
    Estimate the network hashrate based on recent blocks
    
    Args:
        blocks: Number of recent blocks to use for the estimate
        
    Returns:
        JSON string with hashrate estimates
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # Get current blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        current_height = blockchain_info.get("blocks", 0)
        
        # Limit number of blocks to protect against very large queries
        if blocks > 2016:
            blocks = 2016
            
        # Get the timestamp of the first block in our window
        start_height = current_height - blocks + 1
        start_hash = get_block_hash(start_height)
        if not start_hash or (isinstance(start_hash, dict) and "error" in start_hash):
            return json.dumps({"error": f"Could not get hash for block at height {start_height}"})
            
        start_block = get_block(start_hash, 1)
        if "error" in start_block:
            return json.dumps({"error": f"Could not get block data for block at height {start_height}"})
            
        start_time = start_block.get("time", 0)
        
        # Get the timestamp of the current block
        current_hash = get_block_hash(current_height)
        if not current_hash or (isinstance(current_hash, dict) and "error" in current_hash):
            return json.dumps({"error": f"Could not get hash for block at height {current_height}"})
            
        current_block = get_block(current_hash, 1)
        if "error" in current_block:
            return json.dumps({"error": f"Could not get block data for block at height {current_height}"})
            
        current_time = current_block.get("time", 0)
        
        # Calculate time difference in seconds
        time_diff = current_time - start_time
        if time_diff <= 0:
            return json.dumps({"error": "Invalid time difference between blocks"})
            
        # Get current difficulty
        difficulty = blockchain_info.get("difficulty", 0)
        
        # Estimate hashrate
        # Formula: hashrate = difficulty * 2^32 / 600
        # 600 seconds is the target time between blocks
        base_hashrate = difficulty * math.pow(2, 32) / 600
        
        # Adjust for actual time between blocks
        actual_time_per_block = time_diff / blocks
        adjusted_hashrate = base_hashrate * (600 / actual_time_per_block)
        
        # Convert to common units
        hashrate_th = adjusted_hashrate / 1_000_000_000_000  # Terahashes per second
        hashrate_ph = hashrate_th / 1_000  # Petahashes per second
        hashrate_eh = hashrate_ph / 1_000  # Exahashes per second
        
        result = {
            "current_height": current_height,
            "blocks_analyzed": blocks,
            "difficulty": difficulty,
            "time_span_seconds": time_diff,
            "time_span_hours": time_diff / 3600,
            "time_span_days": time_diff / (3600 * 24),
            "actual_time_per_block": actual_time_per_block,
            "target_time_per_block": 600,
            "hashrate_raw": adjusted_hashrate,
            "hashrate_th_s": hashrate_th,
            "hashrate_ph_s": hashrate_ph,
            "hashrate_eh_s": hashrate_eh,
            "period_start_height": start_height,
            "period_end_height": current_height,
            "period_start_time": start_time,
            "period_start_time_iso": datetime.fromtimestamp(start_time).isoformat(),
            "period_end_time": current_time,
            "period_end_time_iso": datetime.fromtimestamp(current_time).isoformat()
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error estimating hashrate: {str(e)}")
        return json.dumps({"error": str(e)})

def get_block_time_distribution(blocks: int = 144) -> str:
    """
    Analyze the distribution of block times over recent blocks
    
    Args:
        blocks: Number of recent blocks to analyze
        
    Returns:
        JSON string with block time distribution analysis
    """
    try:
        bitcoin = get_bitcoin_connection()
        
        # Get current blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        current_height = blockchain_info.get("blocks", 0)
        
        # Limit number of blocks to protect against very large queries
        if blocks > 1000:
            blocks = 1000
            
        # Collect block times
        block_times = []
        block_intervals = []
        
        for height in range(current_height - blocks + 1, current_height + 1):
            try:
                # Get block hash
                block_hash = get_block_hash(height)
                if not block_hash or (isinstance(block_hash, dict) and "error" in block_hash):
                    continue
                
                # Get block data
                block_data = get_block(block_hash, 1)
                if "error" in block_data:
                    continue
                    
                # Store block time
                block_times.append({
                    "height": height,
                    "time": block_data.get("time", 0)
                })
            except Exception as block_error:
                logger.error(f"Error processing block at height {height}: {str(block_error)}")
                continue
                
        # Sort by height to ensure proper order
        block_times.sort(key=lambda x: x["height"])
        
        # Calculate intervals between blocks
        for i in range(1, len(block_times)):
            interval = block_times[i]["time"] - block_times[i-1]["time"]
            block_intervals.append({
                "start_height": block_times[i-1]["height"],
                "end_height": block_times[i]["height"],
                "interval_seconds": interval,
                "interval_minutes": interval / 60
            })
            
        # Analyze the distribution
        if block_intervals:
            # Calculate basic statistics
            intervals = [i["interval_seconds"] for i in block_intervals]
            
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            # Sort for median and percentiles
            sorted_intervals = sorted(intervals)
            median_index = len(sorted_intervals) // 2
            median_interval = sorted_intervals[median_index]
            
            # Calculate percentiles
            p10_index = int(len(sorted_intervals) * 0.1)
            p25_index = int(len(sorted_intervals) * 0.25)
            p75_index = int(len(sorted_intervals) * 0.75)
            p90_index = int(len(sorted_intervals) * 0.9)
            
            p10_interval = sorted_intervals[p10_index]
            p25_interval = sorted_intervals[p25_index]
            p75_interval = sorted_intervals[p75_index]
            p90_interval = sorted_intervals[p90_index]
            
            # Create interval buckets (in minutes)
            buckets = {
                "0-1": 0,
                "1-2": 0,
                "2-5": 0,
                "5-10": 0,
                "10-15": 0,
                "15-30": 0,
                "30-60": 0,
                "60+": 0
            }
            
            for interval in intervals:
                minutes = interval / 60
                if minutes < 1:
                    buckets["0-1"] += 1
                elif minutes < 2:
                    buckets["1-2"] += 1
                elif minutes < 5:
                    buckets["2-5"] += 1
                elif minutes < 10:
                    buckets["5-10"] += 1
                elif minutes < 15:
                    buckets["10-15"] += 1
                elif minutes < 30:
                    buckets["15-30"] += 1
                elif minutes < 60:
                    buckets["30-60"] += 1
                else:
                    buckets["60+"] += 1
                    
            # Calculate percentage distribution
            bucket_percentages = {k: (v / len(intervals)) * 100 for k, v in buckets.items()}
            
            # Calculate standard deviation
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = math.sqrt(variance)
            
            # Find blocks with unusually long intervals (> avg + 2*std_dev)
            unusual_threshold = avg_interval + (2 * std_dev)
            unusual_blocks = [
                {
                    "start_height": block_intervals[i]["start_height"],
                    "end_height": block_intervals[i]["end_height"],
                    "interval_seconds": block_intervals[i]["interval_seconds"],
                    "interval_minutes": block_intervals[i]["interval_minutes"]
                }
                for i in range(len(block_intervals))
                if block_intervals[i]["interval_seconds"] > unusual_threshold
            ]
        else:
            avg_interval = 0
            min_interval = 0
            max_interval = 0
            median_interval = 0
            p10_interval = 0
            p25_interval = 0
            p75_interval = 0
            p90_interval = 0
            buckets = {}
            bucket_percentages = {}
            std_dev = 0
            unusual_blocks = []
        
        result = {
            "current_height": current_height,
            "blocks_analyzed": len(block_times),
            "intervals_analyzed": len(block_intervals),
            "target_interval": 600,  # 10 minutes in seconds
            "statistics": {
                "average_seconds": avg_interval,
                "average_minutes": avg_interval / 60,
                "median_seconds": median_interval,
                "median_minutes": median_interval / 60,
                "min_seconds": min_interval,
                "min_minutes": min_interval / 60,
                "max_seconds": max_interval,
                "max_minutes": max_interval / 60,
                "std_dev_seconds": std_dev,
                "std_dev_minutes": std_dev / 60,
                "p10_seconds": p10_interval,
                "p25_seconds": p25_interval,
                "p75_seconds": p75_interval,
                "p90_seconds": p90_interval
            },
            "distribution": {
                "count_by_minutes": buckets,
                "percentage_by_minutes": bucket_percentages
            },
            "unusual_intervals": unusual_blocks
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing block time distribution: {str(e)}")
        return json.dumps({"error": str(e)})

def analyze_blockchain(kwargs_str: str) -> str:
    """
    Perform a comprehensive analysis of the blockchain
    
    Args:
        kwargs_str: String containing parameters as key=value pairs or JSON
            Optional parameters:
            - timespan: Time period to analyze in hours (default: 24)
            - difficulty_periods: Number of difficulty periods to analyze (default: 5)
            - fee_blocks: Number of blocks to analyze for fees (default: 144)
            - hashrate_blocks: Number of blocks to analyze for hashrate (default: 144)
            - mempool_analysis: Whether to include mempool analysis (default: true)
            
    Returns:
        JSON string with comprehensive blockchain analysis
    """
    try:
        kwargs = parse_kwargs(kwargs_str)
        bitcoin = get_bitcoin_connection()
        
        # Parse parameters with defaults
        timespan_hours = kwargs.get("timespan", 24)
        difficulty_periods = kwargs.get("difficulty_periods", 5)
        fee_blocks = kwargs.get("fee_blocks", 144)
        hashrate_blocks = kwargs.get("hashrate_blocks", 144)
        mempool_analysis = kwargs.get("mempool_analysis", True)
        
        # Get current blockchain info
        blockchain_info = bitcoin.run_command(["getblockchaininfo"])
        if "error" in blockchain_info:
            return json.dumps(blockchain_info)
            
        # Get network info
        network_info = bitcoin.run_command(["getnetworkinfo"])
        
        # Get mempool info if requested
        mempool_info = None
        if mempool_analysis:
            mempool_info = bitcoin.run_command(["getmempoolinfo"])
            
        # Get latest block info
        current_height = blockchain_info.get("blocks", 0)
        latest_hash = get_block_hash(current_height)
        latest_block = None
        if latest_hash and not (isinstance(latest_hash, dict) and "error" in latest_hash):
            latest_block = get_block(latest_hash, 1)
            
        # Analyze difficulty history
        difficulty_data = json.loads(get_difficulty_history(difficulty_periods))
        
        # Analyze fees
        fee_data = json.loads(get_fee_history(fee_blocks))
        
        # Estimate hashrate
        hashrate_data = json.loads(get_hashrate_estimate(hashrate_blocks))
        
        # Analyze block time distribution (past 24 hours)
        blocks_per_day = 144  # ~144 blocks per day (10 minutes per block)
        block_time_data = json.loads(get_block_time_distribution(blocks_per_day))
        
        # Build the comprehensive analysis
        analysis = {
            "analysis_time": int(time.time()),
            "analysis_time_iso": datetime.now().isoformat(),
            "blockchain_state": {
                "chain": blockchain_info.get("chain", "unknown"),
                "blocks": blockchain_info.get("blocks", 0),
                "headers": blockchain_info.get("headers", 0),
                "difficulty": blockchain_info.get("difficulty", 0),
                "verification_progress": blockchain_info.get("verificationprogress", 0),
                "best_block_hash": blockchain_info.get("bestblockhash", ""),
                "size_on_disk": blockchain_info.get("size_on_disk", 0),
                "pruned": blockchain_info.get("pruned", False)
            },
            "network_state": {
                "version": network_info.get("version", 0),
                "subversion": network_info.get("subversion", ""),
                "connections": network_info.get("connections", 0),
                "connections_in": network_info.get("connections_in", 0),
                "connections_out": network_info.get("connections_out", 0)
            },
            "latest_block": latest_block,
            "hashrate_analysis": hashrate_data,
            "fee_analysis": {
                "summary": fee_data.get("summary", {}),
                "recent_trends": fee_data.get("data", [])[:10] if "data" in fee_data else []
            },
            "block_time_analysis": {
                "statistics": block_time_data.get("statistics", {}),
                "distribution": block_time_data.get("distribution", {})
            },
            "difficulty_analysis": {
                "current": blockchain_info.get("difficulty", 0),
                "history": difficulty_data.get("data", [])
            }
        }
        
        # Add mempool analysis if requested
        if mempool_analysis and mempool_info:
            # Get additional mempool details
            raw_mempool = bitcoin.run_command(["getrawmempool", "true"])
            
            # Calculate fee distribution if we have detailed mempool data
            fee_distribution = {}
            if isinstance(raw_mempool, dict) and not "error" in raw_mempool:
                fee_rates = []
                for txid, tx_data in raw_mempool.items():
                    if "fees" in tx_data and "modified" in tx_data["fees"]:
                        fee_rate = tx_data["fees"]["modified"] * 100000000  # Convert to satoshis
                        fee_rates.append(fee_rate)
                
                if fee_rates:
                    # Create fee buckets (in sat/vB)
                    fee_buckets = {
                        "0-1": 0,
                        "1-2": 0,
                        "2-5": 0,
                        "5-10": 0,
                        "10-20": 0,
                        "20-50": 0,
                        "50-100": 0,
                        "100+": 0
                    }
                    
                    for rate in fee_rates:
                        if rate < 1:
                            fee_buckets["0-1"] += 1
                        elif rate < 2:
                            fee_buckets["1-2"] += 1
                        elif rate < 5:
                            fee_buckets["2-5"] += 1
                        elif rate < 10:
                            fee_buckets["5-10"] += 1
                        elif rate < 20:
                            fee_buckets["10-20"] += 1
                        elif rate < 50:
                            fee_buckets["20-50"] += 1
                        elif rate < 100:
                            fee_buckets["50-100"] += 1
                        else:
                            fee_buckets["100+"] += 1
                            
                    fee_distribution = fee_buckets
            
            # Get fee estimates
            fee_estimate_1 = bitcoin.run_command(["estimatesmartfee", "1", "CONSERVATIVE"])
            fee_estimate_6 = bitcoin.run_command(["estimatesmartfee", "6", "CONSERVATIVE"])
            fee_estimate_24 = bitcoin.run_command(["estimatesmartfee", "24", "CONSERVATIVE"])
            
            analysis["mempool_analysis"] = {
                "size": mempool_info.get("size", 0),
                "bytes": mempool_info.get("bytes", 0),
                "usage": mempool_info.get("usage", 0),
                "max_memory": mempool_info.get("maxmempool", 0),
                "min_fee": mempool_info.get("mempoolminfee", 0),
                "fee_distribution": fee_distribution,
                "fee_estimates": {
                    "blocks_1": fee_estimate_1.get("feerate", 0) if isinstance(fee_estimate_1, dict) else 0,
                    "blocks_6": fee_estimate_6.get("feerate", 0) if isinstance(fee_estimate_6, dict) else 0,
                    "blocks_24": fee_estimate_24.get("feerate", 0) if isinstance(fee_estimate_24, dict) else 0
                }
            }
        
        return json.dumps(analysis, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing blockchain: {str(e)}")
        return json.dumps({"error": str(e)})
