# Roadmap & Future Ideas: `ware-viz`

This document outlines the strategic vision, planned enhancements, and robustness goals for the `ware-viz` warehouse visualization library, organized by implementation priority.

---

## Critical & High Priority (Robustness, Scalability & Stress Testing)

*   **Dataset Geometric Validation Library:** Implement geometric validation of datasets (including slot overlap detection, outlier coordinate sanitization, and fallback values for missing coordinate fields) within a separate, dedicated validation library rather than inside the main visualizer engine.
*   **Extreme Layout Geometries:** 
    *   *Micro-slot Drawer Systems:* Stress test layout scaling and text size auto-fitting using drawers and parts bins of extremely small dimensions (e.g., 10x10mm boxes).
    *   *Mega Bulk Storage Zones:* Validate aspect ratios and label rendering for massive floor-storage regions (e.g., 50x50m zones).
*   **Layout Densities & Quantities:** Benchmark visualizer load times and memory footprints under massive layout quantities (e.g., 50,000+ slots in a single footprint map).
*   **Irregular Rack Gaps:** Ensure sequential corridor detection works correctly on irregular rack layouts (e.g., L-shaped warehouses, non-parallel corridors, or asymmetrical rack spacings).
*   **WebGL Plotting Engine:** Switch default Scatter rendering backends in Plotly to WebGL (`go.Scattergl`) when layout sizes exceed 5,000 locations to ensure smooth browser pan and zoom operations.

---

## Medium Priority (Feature Enhancements)

*   **Composite Slotting Index:** Implement a unified slotting index function that merges annual SKU demand with pick trip frequency to render a single, balanced slotting efficiency score.
*   **Asynchronous Corridor Rendering:** Render front elevation views progressively, loading corridors asynchronously to minimize initial CPU spikes on complex layouts.
*   **Rasterization Fallback:** Support automatic Matplotlib rasterization overrides for large datasets to reduce vector-based output file sizes when exporting high-DPI PNGs.

---

## Low Priority & Optional (Integrations & Tooling)

*   **Generic WMS Adaptors:** Build automated adapters to parse raw exports from popular Warehouse Management Systems (WMS) such as SAP WM, Manhattan, and Blue Yonder, automatically cleaning and standardizing column schemas.
*   **Interactive Web UI Dashboard:** Build a Streamlit or Dash application allowing slotting analysts to dynamically filter visualizers by corridor, level, ABC class, or custom search queries.
