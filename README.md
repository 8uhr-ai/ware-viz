# `ware-viz` (Warehouse Layout Visualization Library)

`ware-viz` is a lightweight, pure Python visualization library designed for engineers and researchers working on warehouse slotting optimization, simulation, and reinforcement learning. It renders clean 2D layout diagrams (Top footprint view and Front elevation view) of inventory allocations, supporting both interactive Plotly figures and static Matplotlib plots.

## Installation

Install in editable/development mode inside your project directory:
```bash
pip install -e .
```

## Standardized Schemas

The library follows the **Separation of Concerns** principle: the user filters or preprocesses the data using Pandas/Polars and passes the relevant DataFrame slices to the visualization API. The visualizer expects the following schemas:

### 1. Locations Dataset
Contains the physical parameters and positioning of storage locations (bins/shelves).
*   `loc_id` (str): Unique identifier of the location.
*   `pos_x` (float): X coordinate (horizontal positioning).
*   `pos_y` (float): Y coordinate (aisle depth positioning).
*   `pos_z` (float): Z coordinate (vertical shelf level elevation).
*   `loc_width` (float): Physical width of the slot.
*   `loc_depth` (float): Physical depth of the slot.
*   `loc_height` (float): Physical height of the slot.

*Note: By default, `(pos_x, pos_y, pos_z)` represent the **bottom-left-back corner** of the bin (coordinate minimums). This can be customized to the **center** on visualizer initialization.*

### 2. Parts Dataset (Optional)
Defines inventory item metadata and physical dimensions of the packaging.
*   `item_id` (str/int): Unique identifier of the SKU.
*   `pkg_len` (float): Package length.
*   `pkg_width` (float): Package width.
*   `pkg_depth` (float): Package depth.
*   `pkg_weight` (float): Package weight (used for weight maps & safety policy highlighting).
*   `items_per_pkg` (int): Number of items contained in one package.
*   `demand` (float, optional): Annual item-level demand (in units).
*   `abc_class` (str, optional): Categorical slotting class (`'A'`, `'B'`, `'C'`).

### 3. Allocations Dataset (Optional)
Maps items to their storage locations.
*   `loc_id` (str): Storage location ID.
*   `item_id` (str/int): SKU ID.
*   `alloc_qty` (int): Quantity of packages currently stored.

---

## Key Features & Layout Rules

### Mixed Storage (Multi-SKU Bins)
When a location stores multiple items, the library automatically aggregates attributes:
*   **Volume Occupied:** Sum of volumes of all allocated packages: $\sum (\text{alloc\_qty} \times \text{pkg\_len} \times \text{pkg\_width} \times \text{pkg\_depth})$.
*   **Total Weight:** Sum of package weights: $\sum (\text{alloc\_qty} \times \text{pkg\_weight})$.
*   **Pick trips:** Sum of pick visits computed per SKU: $\sum (\text{demand} / \text{items\_per\_pkg})$.
*   **ABC Class:** Priority-resolved class (`A` > `B` > `C` > `Empty`).

### Automatic Orientation Detection (Front View)
The Front elevation view automatically detects the horizontal axis layout. It checks the variance of coordinates in the provided slice. If coordinates vary more along the X-axis, X is mapped to the horizontal axis of the plot; if they vary more along the Y-axis, Y is mapped. No manual parameters are required.

### 2D Top View Projection
For top-down footprint projections:
*   **Continuous variables** (volume fill, weight, demand) are calculated as the **average** of all locations sitting in the same vertical axis footprint.
*   **ABC Class** is numerically averaged (`A`=3, `B`=2, `C`=1, `Empty`=0) across the vertical axis and mapped back to the closest class category or a continuous gradient.

---

## Example Usage

```python
import pandas as pd
from ware_viz import WarehouseVisualizer

# 1. Load your standardized datasets
df_loc = pd.read_csv("data/locations.csv")
df_parts = pd.read_csv("data/parts.csv")
df_alloc = pd.read_csv("data/allocations.csv")

# 2. Initialize the visualizer
# Supported units: 'mm', 'cm', 'in', etc.
# Supported anchors: 'bottom_left_back', 'center'
viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")

# 3. Render Top View Footprint (returns a Plotly Figure)
fig_top = viz.plot_top(
    locations_df=df_loc,
    parts_df=df_parts,
    allocations_df=df_alloc,
    color_mode="volume",  # Options: 'volume', 'abc', 'demand', 'trips', 'weight'
    engine="plotly"       # Options: 'plotly', 'matplotlib'
)
fig_top.show()

# 4. Filter for a specific aisle and render Front Elevation View
# (It is recommended to filter locations to a single rack row/aisle slice)
df_aisle = df_loc[df_loc['loc_id'].str.startswith('A1')]

fig_front = viz.plot_front(
    locations_df=df_aisle,
    parts_df=df_parts,
    allocations_df=df_alloc,
    color_mode="abc",
    engine="plotly",
    use_physical_spacing=True  # Renders bins to true physical scale
)
fig_front.show()
```

## Demo Run

A sample script is provided in the repository. Run it to load the test datasets and output top/front layouts directly to a `plots/` folder:
```bash
python demo.py
```

## Testing

Run the test suite using `pytest`:
```bash
pytest tests/
```
