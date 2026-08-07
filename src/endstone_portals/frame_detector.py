"""Portal frame detection — scans blocks around a position to find rectangular frames."""


def normalize_block_type(block_type):
    """Normalize block type strings for comparison."""
    if not block_type:
        return ""
    return block_type.lower().replace("minecraft:", "")


def detect_vertical_frame(dimension, center_x, center_y, center_z,
                          border_type="minecraft:obsidian", max_scan=8):
    """
    Detect a vertical rectangular frame (nether portal style) near a position.

    Scans a cube around the player to find all border-type blocks, then tries
    to identify a valid rectangular frame from them.

    Returns dict with 'frame_blocks' and 'inner_blocks' or None.
    """
    normalized = normalize_block_type(border_type)

    # Scan a volume around the player and collect all matching border blocks
    border_positions = set()

    for dx in range(-max_scan, max_scan + 1):
        for dy in range(-max_scan, max_scan + 1):
            for dz in range(-max_scan, max_scan + 1):
                bx = center_x + dx
                by = center_y + dy
                bz = center_z + dz
                try:
                    block = dimension.get_block_at(bx, by, bz)
                    if block and normalize_block_type(block.type) == normalized:
                        border_positions.add((bx, by, bz))
                except Exception:
                    pass

    if len(border_positions) < 6:
        return None

    # Try to form rectangular frames from the collected blocks
    # A vertical frame lives in a single XZ plane (fixed Z or fixed X)

    # Group blocks by their Z coordinate (portal facing east-west, spans X axis)
    z_planes = {}
    for bx, by, bz in border_positions:
        z_planes.setdefault(bz, []).append((bx, by))

    # Group blocks by their X coordinate (portal facing north-south, spans Z axis)
    x_planes = {}
    for bx, by, bz in border_positions:
        x_planes.setdefault(bx, []).append((bz, by))

    # Try each plane to find a valid rectangular frame
    for fixed_z, blocks_2d in sorted(z_planes.items(),
                                      key=lambda kv: abs(kv[0] - center_z)):
        result = _try_find_rect_in_plane(blocks_2d, "x", fixed_z,
                                          center_x, center_y, dimension, normalized,
                                          orientation="north")
        if result:
            return result

    for fixed_x, blocks_2d in sorted(x_planes.items(),
                                      key=lambda kv: abs(kv[0] - center_x)):
        result = _try_find_rect_in_plane(blocks_2d, "z", fixed_x,
                                          center_z, center_y, dimension, normalized,
                                          orientation="west")
        if result:
            return result

    return None


def _try_find_rect_in_plane(blocks_2d, axis, fixed_coord, center_h, center_v,
                             dimension, normalized, orientation="north"):
    """
    Given a set of 2D (horizontal, vertical) block positions in a single plane,
    try to identify a valid rectangular portal frame.

    blocks_2d: list of (h, v) where h is the horizontal axis and v is vertical (Y)
    axis: "x" means h=X,fixed=Z  or "z" means h=Z,fixed=X
    orientation: cardinal facing direction to include in the result dict
    """
    if len(blocks_2d) < 6:
        return None

    block_set = set(blocks_2d)

    # Find the bounding box of all blocks
    all_h = [b[0] for b in blocks_2d]
    all_v = [b[1] for b in blocks_2d]

    min_h, max_h = min(all_h), max(all_h)
    min_v, max_v = min(all_v), max(all_v)

    # Try all possible rectangular sub-frames within the bounding box
    # We look for rectangles where the border is made of our block type
    # and the interior is NOT our block type (it's air or other)

    best_result = None
    best_inner_count = 0

    # Iterate possible left edges
    h_values = sorted(set(all_h))
    v_values = sorted(set(all_v))

    for left in h_values:
        for right in h_values:
            if right - left < 2:  # Need at least 1 inner column
                continue

            for bottom in v_values:
                for top_val in v_values:
                    if top_val - bottom < 2:  # Need at least 1 inner row
                        continue

                    inner_w = right - left - 1
                    inner_h = top_val - bottom - 1

                    if inner_w < 1 or inner_h < 1:
                        continue
                    if inner_w > 23 or inner_h > 23:
                        continue

                    # Check if this rectangle forms a valid frame
                    frame_blocks = []
                    frame_valid = True

                    # Check top and bottom rows
                    for h in range(left, right + 1):
                        if (h, bottom) not in block_set:
                            frame_valid = False
                            break
                        if (h, top_val) not in block_set:
                            frame_valid = False
                            break

                    if not frame_valid:
                        continue

                    # Check left and right columns
                    for v in range(bottom, top_val + 1):
                        if (left, v) not in block_set:
                            frame_valid = False
                            break
                        if (right, v) not in block_set:
                            frame_valid = False
                            break

                    if not frame_valid:
                        continue

                    # Collect frame and inner blocks
                    for h in range(left, right + 1):
                        for v in range(bottom, top_val + 1):
                            is_edge = (h == left or h == right or
                                       v == bottom or v == top_val)
                            if is_edge:
                                if axis == "x":
                                    frame_blocks.append([h, v, fixed_coord])
                                else:
                                    frame_blocks.append([fixed_coord, v, h])

                    inner_blocks = []
                    for h in range(left + 1, right):
                        for v in range(bottom + 1, top_val):
                            if axis == "x":
                                inner_blocks.append([h, v, fixed_coord])
                            else:
                                inner_blocks.append([fixed_coord, v, h])

                    inner_count = len(inner_blocks)

                    if len(frame_blocks) >= 6 and inner_count > 0:
                        # Prefer the largest valid frame closest to the player
                        if inner_count > best_inner_count:
                            best_inner_count = inner_count
                            best_result = {
                                "frame_blocks": frame_blocks,
                                "inner_blocks": inner_blocks,
                                "orientation": orientation,
                            }

    return best_result


def detect_horizontal_frame(dimension, center_x, center_y, center_z,
                            border_type="minecraft:obsidian", max_scan=8):
    """
    Detect a horizontal rectangular frame (end portal style) near a position.

    Scans a flat area around the player at multiple Y levels to find a valid frame.
    Returns dict with 'frame_blocks' and 'inner_blocks' or None.
    """
    normalized = normalize_block_type(border_type)

    # Scan a horizontal slab around the player (check a few Y levels)
    for dy in range(-3, 4):
        y = center_y + dy
        border_positions = []

        for dx in range(-max_scan, max_scan + 1):
            for dz in range(-max_scan, max_scan + 1):
                bx = center_x + dx
                bz = center_z + dz
                try:
                    block = dimension.get_block_at(bx, y, bz)
                    if block and normalize_block_type(block.type) == normalized:
                        border_positions.append((bx, bz))
                except Exception:
                    pass

        if len(border_positions) < 6:
            continue

        result = _try_find_horizontal_rect(border_positions, y)
        if result:
            return result

    return None


def _try_find_horizontal_rect(blocks_2d, fixed_y):
    """
    Given 2D (x, z) positions at a fixed Y, try to find a rectangular frame.
    """
    if len(blocks_2d) < 6:
        return None

    block_set = set(blocks_2d)

    all_x = sorted(set(b[0] for b in blocks_2d))
    all_z = sorted(set(b[1] for b in blocks_2d))

    best_result = None
    best_inner_count = 0

    for min_x in all_x:
        for max_x in all_x:
            if max_x - min_x < 2:
                continue

            for min_z in all_z:
                for max_z in all_z:
                    if max_z - min_z < 2:
                        continue

                    # Check frame edges
                    valid = True

                    for x in range(min_x, max_x + 1):
                        if (x, min_z) not in block_set or (x, max_z) not in block_set:
                            valid = False
                            break

                    if not valid:
                        continue

                    for z in range(min_z, max_z + 1):
                        if (min_x, z) not in block_set or (max_x, z) not in block_set:
                            valid = False
                            break

                    if not valid:
                        continue

                    frame_blocks = []
                    inner_blocks = []

                    for x in range(min_x, max_x + 1):
                        for z in range(min_z, max_z + 1):
                            is_edge = (x == min_x or x == max_x or
                                       z == min_z or z == max_z)
                            if is_edge:
                                frame_blocks.append([x, fixed_y, z])
                            else:
                                inner_blocks.append([x, fixed_y, z])

                    inner_count = len(inner_blocks)
                    if len(frame_blocks) >= 6 and inner_count > 0:
                        if inner_count > best_inner_count:
                            best_inner_count = inner_count
                            best_result = {
                                "frame_blocks": frame_blocks,
                                "inner_blocks": inner_blocks,
                                "orientation": "up",
                            }

    return best_result
