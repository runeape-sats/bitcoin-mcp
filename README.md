# bitcoin-mcp

A streamlined Model Context Protocol (MCP) server implementation that interfaces with Bitcoin Core (full-node) through `bitcoin-cli`. This bitcoin-mcp server provides Claude Desktop (or other mcp clients) with direct access to Bitcoin blockchain data **WITHOUT wallet functionality**.

![screenshot-btc-mcp0](https://github.com/user-attachments/assets/a748869c-3d3f-4271-b871-1c3e8b1c56e6)


## Features
AI agent meets the most secure data ledger - Bitcoin.

- Query real-time Bitcoin blockchain information (via `bitcoin-cli`, but WITHOUT any wallet calls)
- Access mempool, blocks, and transaction data
- Generate 3D representation based on BitFeed

## Prerequisites
- Claude Desktop (or other mcp clients)
- Python 3.10+
- **Bitcoin full-node** (w. `bitcoin-cli`)
- (Windows)

## Installation

1. Install dependencies:
```bash
pip install fastmcp asyncio configparser
```

2. Make sure Bitcoin Core is up-to-date and running. Configure `.env` and add `BITCOIN_CLI_PATH` so that MCP server can find `bitcoin-cli`
- Have this line `BITCOIN_CLI_PATH=C:\\Program Files\\Bitcoin\\daemon\\bitcoin-cli` in `.env` 

3. Claude Desktop Configuration (standard setup for any mcp servers)
- update `path\\to\\` to your local `bitcoin-mcp` folder
```
{
  "mcpServers": {
    "bitcoin-mcp": {
      "command": "python",
      "args": ["path\\to\\bitcoin-mcp\\bitcoin_mcp_server.py"],
      "env": {}
    }
  }
}
```

## Test the server:
You can test the python server to see if it loads your btc full node.
```bash
python bitcoin_mcp_server.py
```

## Available Tools
Mainly for mcp clients like Claude Desktop to utilize Bitcoin blockchain info, so NO WALLET FUNCTIONS ARE INCLUDED.

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
| `get_bitfeed_3d_representation` | Get 3D representation of a BTC block based on TX data |

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
- `bitfeed.py`: 3D representations of BTC blocks

## Security Notes

- This mcp server **does not** include wallet functionality in Bitcoin Core (u can add those urself)
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

Generate 3D representation (note that context length may not fit all TXs, try blocks where TX number < 20 ):

```
Build a react threejs viewer for btc block 111111
```


## License

MIT License
