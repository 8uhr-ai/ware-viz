import os
import pandas as pd
import pytest
from ware_viz import WarehouseVisualizer
import plotly.graph_objects as go
import matplotlib.pyplot as plt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@pytest.fixture
def datasets():
    loc_file = os.path.join(DATA_DIR, "locations.csv")
    parts_file = os.path.join(DATA_DIR, "parts.csv")
    alloc_file = os.path.join(DATA_DIR, "allocations.csv")
    
    # Check if files exist
    if not (os.path.exists(loc_file) and os.path.exists(parts_file) and os.path.exists(alloc_file)):
        pytest.skip("Converted CSV datasets not available yet.")
        
    df_loc = pd.read_csv(loc_file)
    df_parts = pd.read_csv(parts_file)
    df_alloc = pd.read_csv(alloc_file)
    return df_loc, df_parts, df_alloc

def test_visualizer_initialization():
    viz = WarehouseVisualizer(unit="cm", anchor_point="center")
    assert viz.unit == "cm"
    assert viz.anchor_point == "center"
    
    with pytest.raises(ValueError):
        WarehouseVisualizer(anchor_point="invalid")

def test_plot_top_plotly(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    # Plot volume fill
    fig = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="volume", engine="plotly")
    assert isinstance(fig, go.Figure)
    
    # Plot demand
    fig_demand = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="demand", engine="plotly")
    assert isinstance(fig_demand, go.Figure)

def test_plot_top_matplotlib(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    fig = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="volume", engine="matplotlib")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_plot_front_plotly(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    # Filter for a single aisle A1 to test front elevation
    df_loc_filtered = df_loc[df_loc['loc_id'].str.startswith('A1')]
    
    fig = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode="volume", engine="plotly")
    assert isinstance(fig, go.Figure)

def test_plot_front_matplotlib(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    df_loc_filtered = df_loc[df_loc['loc_id'].str.startswith('A1')]
    
    fig = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode="volume", engine="matplotlib")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

def test_labels_and_indicators(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    # Test top view with show_labels and different label_content configurations
    for content_mode in ["indicator", "address"]:
        for color_mode in ["volume", "demand", "trips", "weight", "abc"]:
            fig_plotly = viz.plot_top(df_loc, df_parts, df_alloc, color_mode=color_mode, 
                                      engine="plotly", show_labels=True, label_content=content_mode)
            assert isinstance(fig_plotly, go.Figure)
            
            fig_plt = viz.plot_top(df_loc, df_parts, df_alloc, color_mode=color_mode, 
                                   engine="matplotlib", show_labels=True, label_content=content_mode)
            assert isinstance(fig_plt, plt.Figure)
            plt.close(fig_plt)

    # Test front view with show_labels and different label_content configurations
    df_loc_filtered = df_loc[df_loc['loc_id'].str.startswith('A1')]
    for content_mode in ["indicator", "address"]:
        for color_mode in ["volume", "demand", "trips", "weight", "abc"]:
            fig_plotly = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode=color_mode, 
                                        engine="plotly", show_labels=True, label_content=content_mode)
            assert isinstance(fig_plotly, go.Figure)
            
            fig_plt = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode=color_mode, 
                                     engine="matplotlib", show_labels=True, label_content=content_mode)
            assert isinstance(fig_plt, plt.Figure)
            plt.close(fig_plt)

    # Verify that 'both' raises ValueError
    with pytest.raises(ValueError):
        viz.plot_top(df_loc, df_parts, df_alloc, show_labels=True, label_content="both")
    with pytest.raises(ValueError):
        viz.plot_front(df_loc_filtered, df_parts, df_alloc, show_labels=True, label_content="both")

def test_custom_overlays(datasets):
    df_loc, df_parts, df_alloc = datasets
    viz = WarehouseVisualizer(unit="mm", anchor_point="bottom_left_back")
    
    top_areas = [dict(x0=0, x1=1000, y0=0, y1=2000, label="Test Area", fill_color="rgba(0,0,255,0.1)")]
    top_lines = [dict(coordinate=1500, axis="x", label="Test Line", color="red")]
    
    fig_top = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="volume", 
                           engine="matplotlib", dotted_lines=top_lines, custom_areas=top_areas)
    assert isinstance(fig_top, plt.Figure)
    plt.close(fig_top)
    
    fig_top_plotly = viz.plot_top(df_loc, df_parts, df_alloc, color_mode="volume", 
                                  engine="plotly", dotted_lines=top_lines, custom_areas=top_areas)
    assert isinstance(fig_top_plotly, go.Figure)
    
    df_loc_filtered = df_loc[df_loc['loc_id'].str.startswith('A1')]
    fig_front = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode="volume", 
                               engine="matplotlib", dotted_lines=top_lines, custom_areas=top_areas)
    assert isinstance(fig_front, plt.Figure)
    plt.close(fig_front)
    
    fig_front_plotly = viz.plot_front(df_loc_filtered, df_parts, df_alloc, color_mode="volume", 
                                       engine="plotly", dotted_lines=top_lines, custom_areas=top_areas)
    assert isinstance(fig_front_plotly, go.Figure)



