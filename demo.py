import os
import pandas as pd
import matplotlib.pyplot as plt
from src.ware_viz import WarehouseVisualizer

def run_demo():
    print("Initializing demo run for ware-viz library...")
    
    # 1. Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    plots_dir = os.path.join(base_dir, "plots")
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
    
    # 4. Generate and save Top View - Volume Fill (Matplotlib)
    print("Generating Top View footprint (Volume Utilization)...")
    fig_top_vol = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="volume", engine="matplotlib", show_labels=True)
    top_vol_path = os.path.join(plots_dir, "top_view_volume_utilization.png")
    fig_top_vol.savefig(top_vol_path, bbox_inches='tight', dpi=150)
    plt.close(fig_top_vol)
    print(f"Saved: {top_vol_path}")
    
    # 5. Generate and save Top View - ABC Class (Matplotlib)
    print("Generating Top View footprint (ABC Class Heatmap)...")
    fig_top_abc = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="abc", engine="matplotlib", show_labels=True)
    top_abc_path = os.path.join(plots_dir, "top_view_abc_heatmap.png")
    fig_top_abc.savefig(top_abc_path, bbox_inches='tight', dpi=150)
    plt.close(fig_top_abc)
    print(f"Saved: {top_abc_path}")
    
    # 6. Filter for Aisle A1 and generate Front View - Volume Fill (Matplotlib)
    print("Filtering locations for Aisle A1...")
    df_loc_aisle = df_loc[df_loc['loc_id'].str.startswith('A1')]
    
    print("Generating Front View elevation for Aisle A1 (Volume Utilization)...")
    fig_front_vol = viz.plot_front(df_loc_aisle, df_parts, df_alloc, color_mode="volume", engine="matplotlib", show_labels=True)
    front_vol_path = os.path.join(plots_dir, "front_view_aisle_a1_volume.png")
    fig_front_vol.savefig(front_vol_path, bbox_inches='tight', dpi=150)
    plt.close(fig_front_vol)
    print(f"Saved: {front_vol_path}")
    
    # 7. Generate and save Front View - ABC Class (Matplotlib)
    print("Generating Front View elevation for Aisle A1 (ABC Class)...")
    fig_front_abc = viz.plot_front(df_loc_aisle, df_parts, df_alloc, color_mode="abc", engine="matplotlib", show_labels=True)
    front_abc_path = os.path.join(plots_dir, "front_view_aisle_a1_abc.png")
    fig_front_abc.savefig(front_abc_path, bbox_inches='tight', dpi=150)
    plt.close(fig_front_abc)
    print(f"Saved: {front_abc_path}")
    
    print("\nDemo run completed successfully! Saved all layouts in the 'plots/' directory.")

if __name__ == "__main__":
    run_demo()
