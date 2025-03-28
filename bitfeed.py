"""
BTC Bitfeed 3D block visualization.
based on https://github.com/bitfeed-project/bitfeed/blob/d2272e720c48fe098653c9e39b8204ff3e4000ce/client/src/models/TxMondrianPoolScene.js#L65
"""

import math
import requests
import json
import asyncio
import logging
import traceback
from bitcoin_utils import get_block_hash, get_block

logger = logging.getLogger("BitfeedPython")


class MondrianLayout:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x_max = 0
        self.y_max = 0
        self.row_offset = 0
        self.rows = []
        self.tx_map = []

    def get_size(self):
        return {
            "width": self.x_max,
            "height": self.y_max,
        }

    def get_row(self, position):
        index = position["y"] - self.row_offset
        return self.rows[index] if index < len(self.rows) else None

    def get_slot(self, position):
        row = self.get_row(position)
        if row is not None and position["x"] in row["map"]:
            return row["map"][position["x"]]
        return None

    def add_row(self):
        new_row = {
            "y": len(self.rows) + self.row_offset,
            "slots": [],
            "map": {},
            "max": 0,
        }
        self.rows.append(new_row)
        return new_row

    def add_slot(self, slot):
        if slot["r"] <= 0:
            return None

        existing_slot = self.get_slot(slot["position"])
        if existing_slot is not None:
            existing_slot["r"] = max(existing_slot["r"], slot["r"])
            return existing_slot
        else:
            row = self.get_row(slot["position"])
            if row is None:
                return None

            # Find insert position
            insert_at = next(
                (
                    i
                    for i, s in enumerate(row["slots"])
                    if s["position"]["x"] > slot["position"]["x"]
                ),
                -1,
            )

            if insert_at == -1:
                row["slots"].append(slot)
            else:
                row["slots"].insert(insert_at, slot)

            row["map"][slot["position"]["x"]] = slot
            return slot

    def remove_slot(self, slot):
        row = self.get_row(slot["position"])
        if row is not None:
            if slot["position"]["x"] in row["map"]:
                del row["map"][slot["position"]["x"]]

            index = next(
                (
                    i
                    for i, s in enumerate(row["slots"])
                    if s["position"]["x"] == slot["position"]["x"]
                ),
                -1,
            )

            if index != -1:
                row["slots"].pop(index)

    def fill_slot(self, slot, square_width):
        square = {
            "left": slot["position"]["x"],
            "right": slot["position"]["x"] + square_width,
            "bottom": slot["position"]["y"],
            "top": slot["position"]["y"] + square_width,
        }

        self.remove_slot(slot)

        for row_index in range(slot["position"]["y"], square["top"]):
            row = self.get_row({"x": slot["position"]["x"], "y": row_index})
            if row is not None:
                collisions = []
                max_excess = 0

                for test_slot in row["slots"]:
                    if not (
                        test_slot["position"]["x"] + test_slot["r"] < square["left"]
                        or test_slot["position"]["x"] >= square["right"]
                    ):
                        collisions.append(test_slot)
                        excess = max(
                            0,
                            test_slot["position"]["x"]
                            + test_slot["r"]
                            - (slot["position"]["x"] + slot["r"]),
                        )
                        max_excess = max(max_excess, excess)

                if square["right"] < self.width and square["right"] not in row["map"]:
                    self.add_slot(
                        {
                            "position": {"x": square["right"], "y": row_index},
                            "r": slot["r"] - square_width + max_excess,
                        }
                    )

                for collision in collisions:
                    collision["r"] = slot["position"]["x"] - collision["position"]["x"]

                    if collision["r"] == 0:
                        self.remove_slot(collision)
            else:
                self.add_row()
                if slot["position"]["x"] > 0:
                    self.add_slot(
                        {
                            "position": {"x": 0, "y": row_index},
                            "r": slot["position"]["x"],
                        }
                    )
                if square["right"] < self.width:
                    self.add_slot(
                        {
                            "position": {"x": square["right"], "y": row_index},
                            "r": self.width - square["right"],
                        }
                    )

        for row_index in range(
            max(0, slot["position"]["y"] - square_width), slot["position"]["y"]
        ):
            row = self.get_row({"x": slot["position"]["x"], "y": row_index})
            if row is None:
                continue

            for i in range(len(row["slots"])):
                test_slot = row["slots"][i]

                if (
                    test_slot["position"]["x"] < slot["position"]["x"] + square_width
                    and test_slot["position"]["x"] + test_slot["r"]
                    > slot["position"]["x"]
                    and test_slot["position"]["y"] + test_slot["r"]
                    >= slot["position"]["y"]
                ):
                    old_slot_width = test_slot["r"]
                    test_slot["r"] = slot["position"]["y"] - test_slot["position"]["y"]

                    remaining = {
                        "x": test_slot["position"]["x"] + test_slot["r"],
                        "y": test_slot["position"]["y"],
                        "width": old_slot_width - test_slot["r"],
                        "height": test_slot["r"],
                    }

                    while remaining["width"] > 0 and remaining["height"] > 0:
                        if remaining["width"] <= remaining["height"]:
                            self.add_slot(
                                {
                                    "position": {
                                        "x": remaining["x"],
                                        "y": remaining["y"],
                                    },
                                    "r": remaining["width"],
                                }
                            )
                            remaining["y"] += remaining["width"]
                            remaining["height"] -= remaining["width"]
                        else:
                            self.add_slot(
                                {
                                    "position": {
                                        "x": remaining["x"],
                                        "y": remaining["y"],
                                    },
                                    "r": remaining["height"],
                                }
                            )
                            remaining["x"] += remaining["height"]
                            remaining["width"] -= remaining["height"]

        return {"position": slot["position"], "r": square_width}

    def place(self, size):
        tx = {}
        found = False
        square_slot = None

        for row in self.rows:
            for slot in row["slots"]:
                if slot["r"] >= size:
                    found = True
                    square_slot = self.fill_slot(slot, size)
                    break

            if found:
                break

        if not found:
            row = self.add_row()
            slot = self.add_slot({"position": {"x": 0, "y": row["y"]}, "r": self.width})
            square_slot = self.fill_slot(slot, size)

        for x in range(square_slot["r"]):
            for y in range(square_slot["r"]):
                self.set_tx_map_cell(
                    {
                        "x": square_slot["position"]["x"] + x,
                        "y": square_slot["position"]["y"] + y,
                    },
                    tx,
                )

        if square_slot["position"]["x"] + square_slot["r"] > self.x_max:
            self.x_max = square_slot["position"]["x"] + square_slot["r"]

        if square_slot["position"]["y"] + square_slot["r"] > self.y_max:
            self.y_max = square_slot["position"]["y"] + square_slot["r"]

        return square_slot

    def set_tx_map_cell(self, coord, tx):
        offset_y = coord["y"] - self.row_offset
        if (
            offset_y >= 0
            and offset_y < self.height
            and coord["x"] >= 0
            and coord["x"] < self.width
        ):
            index = offset_y * self.width + coord["x"]
            if index >= 0 and index < len(self.tx_map):
                self.tx_map[index] = tx


def get_tx_parcel_size(value):
    """
    Calculate the parcel size for a transaction based on its value

    Args:
        value (int): Transaction value in satoshis

    Returns:
        int: Parcel size
    """
    if value == 0:
        return 1
    scale = math.ceil(math.log10(value)) - 5
    return max(1, scale)


async def get_bitfeed_3d(block_height, size=1.0, parcel_color="#f7931a"):
    """
    Generate 3D representation of Bitcoin block transactions

    Args:
        block_height (int): Bitcoin block height to visualize
        size (float, optional): Size scaling factor. Defaults to 1.0.
        parcel_color (str, optional): Hex color for parcels. Defaults to "#f7931a".

    Returns:
        dict: Block representation with parcels, dimensions and metadata
    """
    try:
        tx_list = []

        # Fetch transaction data from the Bitfeed API
        logger.info(f"Fetching transaction data for block {block_height}")

        # Get the block hash
        block_hash = get_block_hash(block_height)

        # Fetch the block data with verbosity level 2
        block_data = get_block(block_hash, 2)

        for tx_idx, tx in enumerate(block_data.get("tx", [])):
            # Process vout array to add calculated value for each output
            if "vout" in tx:
                for vout in tx["vout"]:
                    # The value is already in the vout object, but we'll ensure it's there
                    if "value" not in vout:
                        vout["value"] = 0.0

                # Calculate total output value for the transaction (for information)
                total_output_value = sum(vout.get("value", 0.0) for vout in tx["vout"])

            tx_list.append(
                {
                    "value": int(total_output_value * 100000000),
                    "size": get_tx_parcel_size(total_output_value * 100000000),
                }
            )

        logger.info(f"Processing {len(tx_list)} parcels")

        # Calculate block weight
        block_weight = 0
        for tx in tx_list:
            block_weight += tx["size"] * tx["size"]

        platform_thickness = size * 0.1
        margin = size * 0.5
        block_width = math.ceil(math.sqrt(block_weight))
        mondrian = MondrianLayout(block_width, block_width)
        parcels = []
        parcelsMML = ""

        # Create parcels for each transaction
        for i in range(len(tx_list)):
            slot = mondrian.place(tx_list[i]["size"])
            parcel = {
                "size": slot["r"],
                "id": i,
                "width": slot["r"] * size * 0.9,
                "height": platform_thickness * slot["r"],
                "depth": slot["r"] * size * 0.9,
                "x": (slot["position"]["x"] + slot["r"] - block_width / 2) * size
                - margin * slot["r"],
                "z": (0.1 * slot["r"]) / 2,
                "y": (slot["position"]["y"] + slot["r"] - block_width / 2) * size
                - margin * slot["r"],
            }
            parcels.append(parcel)

        logger.info(f"Generated {len(parcels)} parcels with block width {block_width}")

        # Return the full representation
        output = {
            "parcels": parcels,
            "totalWidth": block_width,
            "parcelColor": parcel_color,
            "blockNumber": block_height,
            "totalParcels": len(parcels),
        }
        logger.info(output)
        return output
    except Exception as e:
        logger.error(f"Error generating Bitfeed 3D representation: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}
