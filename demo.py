import os
import pandas as pd
import matplotlib.pyplot as plt
from src.ware_viz import WarehouseVisualizer

def run_demo():
    print("Initializing demo run for ware-viz library...")
    
    # 1. Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    plots_dir = os.path.join(base_dir, "plot_samples")
    os.makedirs(plots_dir, exist_ok=True)
    
    # 2. Load standardized datasets
    loc_file = os.path.join(data_dir, "locations.csv")
    parts_file = os.path.join(data_dir, "parts.csv")
    alloc_file = os.path.join(data_dir, "allocations.csv")
    
    if not (os.path.exists(loc_file) and os.path.exists(parts_file) and os.path.exists(alloc_file)):
        print("Error: Converted test datasets not found in 'data/' directory.")
        return
        
    df_loc = pd.read_csv(loc_file)
    df_parts = pd.read_csv(parts_file)
    df_alloc = pd.read_csv(alloc_file)
    
    # 3. Initialize visualizer
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    # Define custom lines and transparent area overlays for demo purposes
    # Top View: Divide warehouse into Zone 1 (Small, Y from top to half the last corridor) and Zone 2 (Bulk, rest)
    # Plus a vertical dotted line over the first 25% left of the warehouse (X = 600) representing Fast Zone.
    top_areas = [
        dict(x0=None, x1=None, y0=-100, y1=4250, label="Zone 1: Small", 
             fill_color="rgba(231, 76, 60, 0.25)", border_color="rgba(231, 76, 60, 0.45)", border_style="-"),
        dict(x0=None, x1=None, y0=4250, y1=6600, label="Zone 2: Bulk", 
             fill_color="rgba(52, 152, 219, 0.25)", border_color="rgba(52, 152, 219, 0.45)", border_style="-")
    ]
    top_lines = [
        dict(coordinate=600, axis="x", label="Fast Zone", color="#9b59b6", linestyle=":", linewidth=1.5)
    ]
    
    # Front View: Define standard optimal reach ergonomics zone (700mm to 1500mm height)
    front_areas = [
        dict(x0=None, x1=None, y0=700, y1=1500, label="Ergo Zone (700-1500mm)", 
             fill_color="rgba(46, 204, 113, 0.25)", border_color="rgba(46, 204, 113, 0.45)", border_style="-")
    ]
    front_lines = []
    
    # 4. Generate Top Footprint Views (Matplotlib, show_labels=True, label_content="indicator")
    color_modes = ["volume", "demand", "trips", "weight", "abc"]
    for mode in color_modes:
        print(f"Generating Top View footprint (color_mode={mode})...")
        fig = viz.plot_top(df_loc, df_parts, df_alloc, color_mode=mode, engine="matplotlib", 
                           show_labels=True, label_content="indicator", dotted_lines=top_lines, custom_areas=top_areas)
        path = os.path.join(plots_dir, f"top_view_{mode}.png")
        fig.savefig(path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        print(f"Saved: {path}")
        
    # 5. Define Front Elevation View Filter
    df_loc_aisle = df_loc
    
    # 6. Generate Front Elevation Views (Matplotlib, show_labels=True, label_content="indicator")
    for mode in color_modes:
        print(f"Generating Front View elevation (color_mode={mode})...")
        fig = viz.plot_front(df_loc_aisle, df_parts, df_alloc, color_mode=mode, engine="matplotlib", 
                             show_labels=True, label_content="indicator", dotted_lines=front_lines, custom_areas=front_areas)
        path = os.path.join(plots_dir, f"front_view_{mode}.png")
        fig.savefig(path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        print(f"Saved: {path}")
        
    # 7. Generate Front Elevation View with Address Labels (Matplotlib, show_labels=True, label_content="address")
    print("Generating Front View elevation with address labels...")
    fig = viz.plot_front(df_loc_aisle, df_parts, df_alloc, color_mode="volume", engine="matplotlib", 
                         show_labels=True, label_content="address", dotted_lines=front_lines, custom_areas=front_areas)
    path = os.path.join(plots_dir, "front_view_address.png")
    fig.savefig(path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"Saved: {path}")
    
    print(f"\nDemo run completed successfully! Saved all layouts in the '{plots_dir}' directory.")

if __name__ == "__main__":
    run_demo()
