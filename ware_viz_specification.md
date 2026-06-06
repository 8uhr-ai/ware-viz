# Project Specification: `ware-viz` (Warehouse Visualization Library)

**`ware-viz`** is a pure Python visualization library designed to be imported by engineers and researchers during prototyping, simulation, or optimization workflows to generate 2D warehouse layout diagrams.

**Note:** Dashboards, KPI metric calculations, and complex scoring engines have been intentionally kept out of this library. The focus is strictly on rendering physical layouts and allocations. Users can pass their calculated metrics to standard BI/dashboard tools if needed.

---

## 1. Library Inputs & Data Standardization

To handle huge warehouse datasets professionally without crashing memory, the library relies on the industry-standard principle of **Separation of Concerns**.

### User-Driven Filtering (Separation of Concerns)
Instead of the library trying to reinvent query logic or manage database connections, **the user is responsible for filtering the dataset before passing it to the visualizer.**
*   **Flexibility:** During an optimization loop, the "subset" a user wants to plot is often determined by complex algorithmic thresholds (e.g., "plot all bins where the optimization gradient > 0.5"). The plotting library remains "dumb" and simply draws the subset it is handed.
*   **Performance & Memory Safety:** Slicing a DataFrame in Pandas or Polars creates a memory-efficient "view." Passing this pre-filtered view into the plotting function introduces zero overhead, which is critical when the visualization function is called frequently inside an optimization loop.

### Standardized Schema & Physical Anchoring
All column names are standardized to a consistent `snake_case` format. Measurement units (mm, cm, in) have been stripped from the column names; instead, the user defines the global unit system when initializing the visualizer.

*   **Coordinate Reference Point (Physical Anchor):** By default, coordinates (`pos_x`, `pos_y`, `pos_z`) represent the **bottom-left-back corner** (the minimum boundary along each axis) of the bin in 3D space. However, this is user-definable (e.g. can be configured as `"center"` or `"bottom_left_back"` on visualizer initialization).

1.  **Locations Dataset:** 
    *   Provides bin dimensions and physical positioning.
    *   Expected columns: `loc_id`, `pos_x`, `pos_y`, `pos_z`, `loc_width`, `loc_depth`, `loc_height`.
2.  **Parts Dataset:** 
    *   Provides package properties and physical dimensions. Dimensions always refer to the package.
    *   Expected columns: `item_id`, `pkg_len`, `pkg_width`, `pkg_depth`, `pkg_weight`, `items_per_pkg`, `demand` (optional, in units), `abc_class` (optional).
    *   *Usage of `pkg_weight`:* Used to plot weight distribution heatmaps or to flag bins violating user-defined weight/safety policy thresholds.
    *   *Usage of `items_per_pkg`:* Used to convert item-level demand into pick visits (trips). The library calculates pick frequency as:
        $$\text{Pick Trips} = \frac{\text{Demand (units)}}{\text{items\_per\_pkg}}$$
        This represents the actual visit frequency of the picker to a location, which is the industry standard for mapping warehouse hotspots.
3.  **Allocations Dataset:** 
    *   Maps parts to locations and quantity of packages.
    *   Expected columns: `loc_id`, `item_id`, `alloc_qty` (in packages).
    *   **Mixed Storage (Multi-SKU Bins):** When a location contains multiple different items, the library aggregates their values:
        *   *Volume occupied:* Sum of the volumes of all packages allocated to that location.
        *   *Weight:* Sum of the weights of all packages allocated to that location (`alloc_qty * pkg_weight`).
        *   *Demand / Pick Trips:* Summed across all allocated SKUs in that location.
        *   *ABC Class:* Resolved by priority (`A` > `B` > `C` > `Empty`) to ensure high-priority items are highlighted.

---

## 2. Core Visualizations (Library Outputs)

The library will expose primary plotting methods attached to a main `WarehouseVisualizer` class. The visualizer is initialized with the global measurement unit (e.g., `unit="mm"`).

### A. Front View (Rack Elevation)
*   **Purpose:** Renders the vertical layout of a specific row or section of racks, showing bin heights and their contents.
*   **User-Defined Range:** The user passes a pre-filtered DataFrame (e.g., containing only the `loc_id`s for a specific aisle) directly into the plotting function.
*   **Automatic Axis Mapping:** The library automatically determines which physical axis represents the horizontal extension of the rack row by calculating coordinate variance. If the coordinates span further along the X-axis (larger range for `pos_x`), the horizontal axis of the plot is mapped to `pos_x`. If they span further along the Y-axis, it is mapped to `pos_y`. No manual orientation parameter is needed.
*   **Features:** Displays bins as rectangles stacked vertically (by `pos_z`) and horizontally. Supports both rendering modes (Full Box vs. Proportional Fill) detailed below.

### B. Top View (Footprint Layout)
*   **Purpose:** Renders a 2D top-down footprint map of the warehouse layout, flattening the vertical Z-axis.
*   **User-Defined Range:** The user passes a pre-filtered DataFrame bounded by their desired `pos_x` and `pos_y` coordinate limits.
*   **Features:** Displays the $(x, y)$ footprint of racks and aisles. Because multiple vertically-stacked bins share the same $(x, y)$ coordinates, values for the footprint cells are calculated using the 2D projection and aggregation rules detailed below.

### C. Visual Rendering & Color Toggles
Both views support toggling between rendering/coloring modes:

1.  **Full Boxes (Demand, Pick Frequency, ABC, or Weight):**
    *   **Rendering:** The location's rectangle is fully colored (100% filled).
    *   **Coloring - Demand / Pick Frequency / Weight:** Colors bins based on continuous values. The user **must** provide the threshold ranges and their corresponding colors.
    *   **Coloring - ABC Analysis:** Colors bins based on the `abc_class` (A, B, or C). The library provides default color coding (A = Red, B = Yellow, C = Green) but allows the user to override them.

2.  **Proportional Volume Fill (Volumetric Occupancy):**
    *   **Rendering:** Bins are filled proportionally to their volume utilization (e.g., a bin with 40% volume utilization is drawn with a color fill covering 40% of the box height, while the remaining 60% remains empty/transparent).
    *   **Coloring:** The filled portion is color-coded based on the utilization percentage (e.g., green, yellow, red).
    *   **Thresholds:** The user can specify custom thresholds. Default thresholds are: Green ($\le 50\%$), Yellow ($50-85\%$), Red ($> 85\%$).

### D. 2D Aggregation & Projection Logic for Footprints
In 2D views (specifically the Top View footprint projection which collapses the Z-axis):
*   For any given $(x, y)$ coordinate footprint, multiple locations (bins at different shelf levels $z$) might exist.
*   To render that footprint cell, values are aggregated across all locations sharing the same $(x, y)$ footprint:
    *   **Volume Fill & Continuous Metrics (Demand, Pick Trips, Weight):** Calculated as the **average** of the values of all locations sitting on that same vertical axis.
    *   **ABC Class:** Calculated as an **average** category. The library converts the classes to numerical values (e.g., `A` = 3, `B` = 2, `C` = 1, `Empty` = 0), averages them across the vertical axis, and maps the resulting numerical average back to the closest class category or a continuous color scale (from C to A).

---

## 3. Tech Stack

*   **Python:** Core language.
*   **Pandas / Polars (Data Interfaces):** The library will accept standard DataFrames or memory-efficient "views" passed by the user.
*   **Plotly (or Matplotlib):** The core rendering engines. Plotly is recommended for interactive zooming and hovering in notebooks.
*   **PyPI Packaging (`pyproject.toml`):** For building the library to be installed via `pip`.
