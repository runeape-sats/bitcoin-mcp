# Bitcoin MCP Server for Claude Desktop

A streamlined Model Context Protocol (MCP) server implementation that interfaces with Bitcoin Core through `bitcoin-cli`. This server provides Claude Desktop with direct access to Bitcoin blockchain data and analytics **WITHOUT wallet functionality**.

## Features
LLM meets the most secure data ledger

- Query real-time Bitcoin blockchain information
- Access block and transaction data
- Get network status and mempool information
- Perform advanced blockchain analytics
- Auto-detects bitcoin-cli in PATH
- Minimal configuration required

## Prerequisites
- Claude Desktop
- Python 3.10+
- Bitcoin full-node for `bitcoin-cli` access

## Installation

1. Install dependencies:
```bash
pip install fastmcp asyncio configparser
```

2. Make sure Bitcoin Core is running and configure `bitcoin-cli` so that MCP server can find it

3. Claude Desktop Configuration (standard setup for any mcp servers)
```
{
  "mcpServers": {
    "bitcoin-mcp": {
      "command": "uv",
      "args": ["--directory", "path\\to\\bitcoin-mcp", "run", "bitcoin_mcp_server.py"],
      "env": {}
    }
  }
}
```

## test the server:
You can test the python server to see if everything loads
```bash
python bitcoin_mcp_server.py
```

## Available Tools
Mainly for Claude to gather Bitcoin blockchain info, so NO WALLET FUNCTIONS ARE INCLUDED.

### Blockchain Information

| Tool | Description |
|------|-------------|
| `get_blockchain_info` | Get current blockchain state |
| `get_block_hash` | Get block hash for a specific height |
| `get_block` | Get block data by hash |
| `get_block_stats` | Get block statistics |
| `get_chain_tips` | Get information about chain tips |
| `get_chain_tx_stats` | Get chain transaction statistics |
| `get_difficulty` | Get current difficulty |
| `get_network_info` | Get network information |
| `get_blockchain_status` | Get comprehensive blockchain status |
| `get_detailed_block_info` | Get detailed block information |
| `search_blocks` | Search for blocks meeting criteria |

### Transaction Information

| Tool | Description |
|------|-------------|
| `get_mempool_info` | Get mempool information |
| `get_tx_out` | Get UTXO information |
| `get_tx_out_set_info` | Get UTXO set statistics |
| `get_raw_transaction` | Get raw transaction data |
| `decode_raw_transaction` | Decode raw transaction |
| `estimate_smart_fee` | Estimate transaction fee |
| `analyze_transaction` | Analyze transaction details |

### Analytics

| Tool | Description |
|------|-------------|
| `get_difficulty_history` | Get difficulty adjustment history |
| `get_fee_history` | Get transaction fee history |
| `get_hashrate_estimate` | Estimate network hashrate |
| `get_block_time_distribution` | Analyze block time distribution |
| `analyze_blockchain` | Comprehensive blockchain analysis |

### Configuration

| Tool | Description |
|------|-------------|
| `configure_bitcoin_cli` | Configure bitcoin-cli settings |
| `get_config_info` | Get current server configuration |
| `update_server_config` | Update server configuration |

## Code Structure

- `bitcoin_mcp_server.py`: Main server entry point
- `bitcoin_connection.py`: Bitcoin Core connection utilities
- `bitcoin_config.py`: Configuration management
- `bitcoin_transactions.py`: Transaction analysis utilities
- `bitcoin_utils.py`: Blockchain utilities
- `bitcoin_analytics.py`: Advanced blockchain analytics

## Security Notes

- This mcp server does not include wallet functionality in Bitcoin Core (u can add those urself)
- By default, the server only binds to localhost (127.0.0.1)
- Enables read-only access to blockchain data

## Example Usage

Get current blockchain information:

```
Tell me about the current state of the Bitcoin blockchain
```

Analyze a specific block:

```
Show me detailed information about block 800000
```

Get transaction fee history:

```
What have transaction fees been like over the past 24 hours?
```

Estimate hashrate:

```
What is the current estimated hashrate of the Bitcoin network?
```

## License

MIT License
