import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def interpolate_color(color1, color2, factor):
    """
    Interpolate between two hex colors. factor is between 0 and 1.
    """
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)]
        
    def rgb_to_hex(rgb_val):
        return '#' + ''.join(f'{int(round(c)):02x}' for c in rgb_val)

    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    c_interp = [c1[i] + (c2[i] - c1[i]) * factor for i in range(3)]
    # Clamp to [0, 255]
    c_interp = [min(max(c, 0), 255) for c in c_interp]
    return rgb_to_hex(c_interp)

def get_abc_color(abc_val, abc_colors=None):
    if abc_colors is None:
        abc_colors = {'A': '#e74c3c', 'B': '#f1c40f', 'C': '#2ecc71', 'Empty': '#ecf0f1'}
    
    # If it is a string (discrete)
    if isinstance(abc_val, str):
        return abc_colors.get(abc_val, abc_colors.get('C', '#2ecc71'))
        
    # If it is numerical average (0 to 3)
    val = float(abc_val)
    if val <= 0.0:
        return abc_colors.get('Empty', '#ecf0f1')
    elif val <= 1.0:
        # Interpolate between Empty and C
        factor = val
        return interpolate_color(abc_colors.get('Empty', '#ecf0f1'), abc_colors.get('C', '#2ecc71'), factor)
    elif val <= 2.0:
        # Interpolate between C and B
        factor = val - 1.0
        return interpolate_color(abc_colors.get('C', '#2ecc71'), abc_colors.get('B', '#f1c40f'), factor)
    elif val <= 3.0:
        # Interpolate between B and A
        factor = val - 2.0
        return interpolate_color(abc_colors.get('B', '#f1c40f'), abc_colors.get('A', '#e74c3c'), factor)
    else:
        return abc_colors.get('A', '#e74c3c')

class WarehouseVisualizer:
    def __init__(self, unit="mm", anchor_point="bottom_left_back"):
        """
        Initialize the Warehouse Visualizer.
        
        Parameters:
        - unit (str): The physical measurement unit (e.g., 'mm', 'cm', 'in'). Default is 'mm'.
        - anchor_point (str): Position anchor for coordinates. Either 'bottom_left_back' or 'center'.
        """
        self.unit = unit
        if anchor_point not in ["bottom_left_back", "center"]:
            raise ValueError("anchor_point must be 'bottom_left_back' or 'center'")
        self.anchor_point = anchor_point

    def _parse_rgba_for_matplotlib(self, color_str):
        if not isinstance(color_str, str):
            return color_str
        color_str = color_str.strip()
        if color_str.lower() == 'none':
            return 'none'
        if color_str.startswith('rgba'):
            try:
                parts = color_str.replace('rgba(', '').replace(')', '').split(',')
                r = int(parts[0].strip()) / 255.0
                g = int(parts[1].strip()) / 255.0
                b = int(parts[2].strip()) / 255.0
                a = float(parts[3].strip())
                return (r, g, b, a)
            except Exception:
                return color_str
        elif color_str.startswith('rgb'):
            try:
                parts = color_str.replace('rgb(', '').replace(')', '').split(',')
                r = int(parts[0].strip()) / 255.0
                g = int(parts[1].strip()) / 255.0
                b = int(parts[2].strip()) / 255.0
                return (r, g, b, 1.0)
            except Exception:
                return color_str
        return color_str

    def _get_end_address(self, loc_id):
        if not isinstance(loc_id, str):
            loc_id = str(loc_id)
        for delimiter in ['-', '_', '/', ' ']:
            if delimiter in loc_id:
                parts = loc_id.split(delimiter)
                for p in reversed(parts):
                    if p.strip():
                        val = p.strip()
                        return val[-3:] if len(val) >= 3 else val
        return loc_id[-3:] if len(loc_id) >= 3 else loc_id

    def _get_end_address_range(self, loc_ids, sep="\n"):
        if not loc_ids:
            return ""
        unique_ids = [x.strip() for x in loc_ids.split(',') if x.strip()]
        if not unique_ids:
            return ""
        if len(unique_ids) == 1:
            return self._get_end_address(unique_ids[0])
        
        first_end = self._get_end_address(unique_ids[0])
        last_end = self._get_end_address(unique_ids[-1])
        
        return f"{first_end}{sep}{last_end}"

    def _get_matplotlib_fontsize(self, ax, text, w, h, max_fs=9, min_fs=1):
        try:
            # Determine axis limits in data units
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            data_w = max(1.0, xlim[1] - xlim[0])
            data_h = max(1.0, ylim[1] - ylim[0])
            
            # Determine axes size in points
            fig = ax.get_figure()
            fig_w, fig_h = fig.get_size_inches()
            pos = ax.get_position()
            ax_w_pts = pos.width * fig_w * 72.0
            ax_h_pts = pos.height * fig_h * 72.0
            
            # Scale factor (data to points)
            scale_x = ax_w_pts / data_w
            scale_y = ax_h_pts / data_h
            
            # For equal aspect ratio, scale is limited by the tighter dimension
            scale = min(scale_x, scale_y)
            
            w_pts = w * scale
            h_pts = h * scale
            
            lines = text.split('\n')
            max_len = max(len(line) for line in lines) if lines else 1
            line_count = len(lines) if lines else 1
            
            fs_w = w_pts / (max_len * 0.85)
            fs_h = h_pts / (line_count * 1.4)
            
            fs = min(fs_w, fs_h)
            return min(max_fs, max(min_fs, int(fs)))
        except Exception:
            return 7

    def _get_plotly_fontsize(self, text, w, h, total_range_x, total_range_y, fig_width=1000, fig_height=900, max_fs=9, min_fs=1):
        try:
            # Deduct margins for inner plotting area
            inner_w = max(100.0, fig_width - 180.0)
            inner_h = max(100.0, fig_height - 150.0)
            
            scale_x = inner_w / total_range_x if total_range_x > 0 else 1.0
            scale_y = inner_h / total_range_y if total_range_y > 0 else 1.0
            scale = min(scale_x, scale_y)
            
            w_px = w * scale
            h_px = h * scale
            
            lines = text.split('\n')
            max_len = max(len(line) for line in lines) if lines else 1
            line_count = len(lines) if lines else 1
            
            fs_w = w_px / (max_len * 0.85)
            fs_h = h_px / (line_count * 1.4)
            
            fs = min(fs_w, fs_h)
            return min(max_fs, max(min_fs, int(fs)))
        except Exception:
            return 7

    def _prepare_data(self, locations_df, parts_df=None, allocations_df=None):
        """
        Validates schemas, joins datasets, aggregates allocations for multi-SKU bins,
        and computes dimensions, volumes, weights, demands, pick trips, and ABC classes.
        """
        # Copy to avoid side effects
        locs = locations_df.copy()
        
        # Validate locations columns
        required_loc = ['loc_id', 'pos_x', 'pos_y', 'pos_z', 'loc_width', 'loc_depth', 'loc_height']
        for col in required_loc:
            if col not in locs.columns:
                raise ValueError(f"Locations DataFrame missing required column: {col}")

        # Handle coordinate anchor point
        if self.anchor_point == "center":
            locs['pos_x'] = locs['pos_x'] - locs['loc_width'] / 2.0
            locs['pos_y'] = locs['pos_y'] - locs['loc_depth'] / 2.0
            locs['pos_z'] = locs['pos_z'] - locs['loc_height'] / 2.0

        # If no allocations or parts, fill default values
        if allocations_df is None or allocations_df.empty:
            locs['total_occupied_volume'] = 0.0
            locs['volume_utilization'] = 0.0
            locs['total_weight'] = 0.0
            locs['total_demand'] = 0.0
            locs['total_trips'] = 0.0
            locs['abc_class'] = 'Empty'
            locs['allocated_skus'] = 'None'
            return locs

        allocs = allocations_df.copy()
        required_alloc = ['loc_id', 'item_id', 'alloc_qty']
        for col in required_alloc:
            if col not in allocs.columns:
                raise ValueError(f"Allocations DataFrame missing required column: {col}")

        # If parts_df is provided, merge parts details
        if parts_df is not None and not parts_df.empty:
            parts = parts_df.copy()
            required_parts = ['item_id', 'pkg_len', 'pkg_width', 'pkg_depth', 'pkg_weight', 'items_per_pkg']
            for col in required_parts:
                if col not in parts.columns:
                    raise ValueError(f"Parts DataFrame missing required column: {col}")
            
            # Merge allocations and parts
            merged_alloc = pd.merge(allocs, parts, on='item_id', how='left')
        else:
            # Create a parts DataFrame with default minimal columns if none provided
            merged_alloc = allocs.copy()
            merged_alloc['pkg_len'] = 0.0
            merged_alloc['pkg_width'] = 0.0
            merged_alloc['pkg_depth'] = 0.0
            merged_alloc['pkg_weight'] = 0.0
            merged_alloc['items_per_pkg'] = 1
            merged_alloc['demand'] = 0.0
            merged_alloc['abc_class'] = 'C'

        # Fill missing values for parts attributes with defaults
        fill_cols = {
            'pkg_len': 0.0, 'pkg_width': 0.0, 'pkg_depth': 0.0,
            'pkg_weight': 0.0, 'items_per_pkg': 1, 'demand': 0.0, 'abc_class': 'C'
        }
        for col, val in fill_cols.items():
            if col in merged_alloc.columns:
                merged_alloc[col] = merged_alloc[col].fillna(val)

        # Calculate allocation physical attributes
        merged_alloc['pkg_volume'] = merged_alloc['pkg_len'] * merged_alloc['pkg_width'] * merged_alloc['pkg_depth']
        merged_alloc['occupied_volume'] = merged_alloc['alloc_qty'] * merged_alloc['pkg_volume']
        merged_alloc['occupied_weight'] = merged_alloc['alloc_qty'] * merged_alloc['pkg_weight']
        
        # Calculate pick visits (trips)
        items_per_pkg = merged_alloc['items_per_pkg'].copy().astype(float)
        items_per_pkg = np.where(items_per_pkg <= 0, 1.0, items_per_pkg)
        merged_alloc['pick_trips'] = merged_alloc['demand'].astype(float) / items_per_pkg

        # Map ABC class to numeric for max priority resolution
        abc_map = {'A': 3, 'B': 2, 'C': 1, 'Empty': 0}
        merged_alloc['abc_val'] = merged_alloc['abc_class'].map(abc_map).fillna(1)

        # Group by location (handle mixed storage)
        def list_skus(series):
            unique_skus = series.dropna().unique()
            if len(unique_skus) == 0:
                return 'None'
            return ', '.join(map(str, unique_skus))

        agg_rules = {
            'occupied_volume': 'sum',
            'occupied_weight': 'sum',
            'demand': 'sum',
            'pick_trips': 'sum',
            'abc_val': 'max',
            'item_id': list_skus
        }
        
        loc_alloc = merged_alloc.groupby('loc_id', as_index=False).agg(agg_rules)
        loc_alloc.rename(columns={
            'occupied_volume': 'total_occupied_volume',
            'occupied_weight': 'total_weight',
            'demand': 'total_demand',
            'pick_trips': 'total_trips',
            'item_id': 'allocated_skus'
        }, inplace=True)

        # Map numeric ABC value back to string class
        rev_abc_map = {3: 'A', 2: 'B', 1: 'C', 0: 'Empty'}
        loc_alloc['abc_class'] = loc_alloc['abc_val'].map(rev_abc_map).fillna('C')
        loc_alloc.drop(columns=['abc_val'], inplace=True)

        # Merge back into locations
        final_df = pd.merge(locs, loc_alloc, on='loc_id', how='left')
        
        # Fill missing values for empty locations
        final_df['total_occupied_volume'] = final_df['total_occupied_volume'].fillna(0.0)
        final_df['total_weight'] = final_df['total_weight'].fillna(0.0)
        final_df['total_demand'] = final_df['total_demand'].fillna(0.0)
        final_df['total_trips'] = final_df['total_trips'].fillna(0.0)
        final_df['abc_class'] = final_df['abc_class'].fillna('Empty')
        final_df['allocated_skus'] = final_df['allocated_skus'].fillna('None')

        # Calculate volumetric utilization percentage
        loc_capacity = final_df['loc_width'] * final_df['loc_depth'] * final_df['loc_height']
        # Avoid division by zero
        loc_capacity = np.where(loc_capacity <= 0, 1.0, loc_capacity)
        final_df['volume_utilization'] = final_df['total_occupied_volume'] / loc_capacity
        
        return final_df

    def _get_continuous_color(self, value, thresholds=None):
        """
        Maps a continuous numerical value to a hex color using thresholds or defaults.
        """
        if value <= 0:
            return '#ecf0f1'  # Light grey for zero
            
        if thresholds is not None:
            # thresholds is expected to be a list of tuples: (limit, hex_color) sorted ascending
            # e.g., [(10, '#3498db'), (50, '#f1c40f'), (100, '#e74c3c')]
            for limit, color in thresholds:
                if value <= limit:
                    return color
            return thresholds[-1][1] if thresholds else '#e74c3c'
        else:
            # Default yellow-to-red gradient for heatmap
            max_val = 100.0
            val_norm = min(value / max_val, 1.0)
            return interpolate_color('#f1c40f', '#e74c3c', val_norm)

    def plot_top(self, locations_df, parts_df=None, allocations_df=None, color_mode="volume", 
                 demand_thresholds=None, volume_thresholds=None, abc_colors=None, engine="plotly",
                 show_labels=False, label_content="indicator", dotted_lines=None, custom_areas=None):
        """
        Renders a 2D top-down footprint map of the warehouse layout.
        """
        if label_content not in ["indicator", "address"]:
            raise ValueError("label_content must be 'indicator' or 'address'")

        # 1. Prepare data
        df = self._prepare_data(locations_df, parts_df, allocations_df)
        
        # 2. Map ABC to numeric for averaging
        abc_map = {'A': 3, 'B': 2, 'C': 1, 'Empty': 0}
        df['abc_num'] = df['abc_class'].map(abc_map)
        
        # 3. Collapse Z-axis: group by pos_x, pos_y
        agg_dict = {
            'loc_width': 'first',
            'loc_depth': 'first',
            'volume_utilization': 'mean',
            'total_weight': 'mean',
            'total_demand': 'mean',
            'total_trips': 'mean',
            'abc_num': 'mean',
            'allocated_skus': lambda s: ', '.join(set([sku for val in s for sku in str(val).split(', ') if sku != 'None'])) or 'None'
        }
        
        # Keep track of loc_id list in this vertical stack for tooltip
        agg_dict['loc_id'] = lambda s: ', '.join(s.unique())
        
        df_2d = df.groupby(['pos_x', 'pos_y'], as_index=False).agg(agg_dict)
        
        # Convert numerical abc_num back to string for categories
        rev_abc_map = {3: 'A', 2: 'B', 1: 'C', 0: 'Empty'}
        df_2d['abc_class_cat'] = df_2d['abc_num'].apply(lambda v: rev_abc_map.get(int(round(v)), 'C') if v > 0 else 'Empty')
        
        # Volume thresholds default
        if volume_thresholds is None:
            volume_thresholds = [0.5, 0.85]  # Green <= 0.5, Yellow <= 0.85, Red > 0.85

        if engine == "plotly":
            fig = go.Figure()
            shapes = []
            hover_x = []
            hover_y = []
            hover_text = []
            
            # Compute total range for Plotly font size calculation
            min_x = df_2d['pos_x'].min()
            max_x = (df_2d['pos_x'] + df_2d['loc_width']).max()
            min_y = df_2d['pos_y'].min()
            max_y = (df_2d['pos_y'] + df_2d['loc_depth']).max()
            total_range_x = max(1.0, max_x - min_x)
            total_range_y = max(1.0, max_y - min_y)
            
            label_x = []
            label_y = []
            label_texts = []
            label_sizes = []
            
            for _, row in df_2d.iterrows():
                px, py = row['pos_x'], row['pos_y']
                w, d = row['loc_width'], row['loc_depth']
                util = row['volume_utilization']
                
                hover_x.append(px + w / 2.0)
                hover_y.append(py + d / 2.0)
                
                txt = (f"Footprint Grid: X={px:.1f}, Y={py:.1f}<br>"
                       f"Bins in Stack: {row['loc_id']}<br>"
                       f"Avg Vol Util: {util*100:.1f}%<br>"
                       f"Avg Weight: {row['total_weight']:.1f}<br>"
                       f"Avg Demand: {row['total_demand']:.1f}<br>"
                       f"Avg Pick Trips: {row['total_trips']:.1f}<br>"
                       f"Avg ABC Val: {row['abc_num']:.2f} ({row['abc_class_cat']})<br>"
                       f"SKUs: {row['allocated_skus']}")
                hover_text.append(txt)
                
                bg_color = '#ecf0f1'
                border_color = '#2c3e50'
                
                if color_mode == "volume":
                    if util <= 0:
                        fill_color = '#ecf0f1'
                    elif util <= volume_thresholds[0]:
                        fill_color = '#2ecc71'
                    elif util <= volume_thresholds[1]:
                        fill_color = '#f1c40f'
                    else:
                        fill_color = '#e74c3c'
                elif color_mode == "abc":
                    fill_color = get_abc_color(row['abc_num'], abc_colors)
                elif color_mode == "demand":
                    fill_color = self._get_continuous_color(row['total_demand'], demand_thresholds)
                elif color_mode == "trips":
                    fill_color = self._get_continuous_color(row['total_trips'], demand_thresholds)
                elif color_mode == "weight":
                    fill_color = self._get_continuous_color(row['total_weight'], demand_thresholds)
                else:
                    fill_color = bg_color
                    
                if color_mode == "volume":
                    # Background Empty Box
                    shapes.append(dict(
                        type="rect", x0=px, y0=py, x1=px+w, y1=py+d,
                        line=dict(color=border_color, width=1),
                        fillcolor=bg_color
                    ))
                    # Filled Box proportional to util (fill from bottom up)
                    if util > 0:
                        fill_d = d * min(util, 1.0)
                        shapes.append(dict(
                            type="rect", x0=px, y0=py, x1=px+w, y1=py+fill_d,
                            line=dict(width=0),
                            fillcolor=fill_color
                        ))
                else:
                    shapes.append(dict(
                        type="rect", x0=px, y0=py, x1=px+w, y1=py+d,
                        line=dict(color=border_color, width=1),
                        fillcolor=fill_color
                    ))
                    
                if show_labels:
                    indicator = ""
                    if color_mode == "volume":
                        indicator = f"{util*100:.0f}%"
                    elif color_mode == "demand":
                        indicator = f"{row['total_demand']:.0f}"
                    elif color_mode == "trips":
                        indicator = f"{row['total_trips']:.0f}"
                    elif color_mode == "weight":
                        indicator = f"{row['total_weight']:.1f}"
                    
                    effective_label_content = label_content
                    if color_mode == "abc" and label_content == "indicator":
                        effective_label_content = "address"
                        
                    if effective_label_content == "address":
                        label_text = self._get_end_address_range(row['loc_id'], sep="<br>")
                    elif effective_label_content == "indicator":
                        label_text = indicator
                    else:
                        label_text = ""
                        
                    if label_text:
                        fs = self._get_plotly_fontsize(label_text.replace("<br>", "\n"), w, d, total_range_x, total_range_y)
                        label_x.append(px + w / 2.0)
                        label_y.append(py + d / 2.0)
                        label_texts.append(label_text)
                        label_sizes.append(fs)
                    
            fig.add_trace(go.Scatter(
                x=hover_x, y=hover_y,
                mode='markers',
                marker=dict(size=10, color='rgba(0,0,0,0)'),
                text=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
            
            if show_labels and label_texts:
                fig.add_trace(go.Scatter(
                    x=label_x, y=label_y,
                    mode='text',
                    text=label_texts,
                    textposition='middle center',
                    textfont=dict(size=label_sizes, color='#555555', family='Arial, sans-serif'),
                    showlegend=False
                ))
            
            has_legend = False

            if dotted_lines:
                for line in dotted_lines:
                    coord = line.get('coordinate')
                    axis = line.get('axis', 'x')
                    label = line.get('label', '')
                    color = line.get('color', '#7f8c8d')
                    linestyle = line.get('linestyle', '--')
                    linewidth = line.get('linewidth', 1.5)
                    
                    dash = 'dash' if linestyle == '--' else 'dot' if linestyle == ':' else 'solid'
                    
                    if axis == 'x':
                        shapes.append(dict(
                            type="line", x0=coord, y0=min_y, x1=coord, y1=max_y,
                            line=dict(color=color, width=linewidth, dash=dash)
                        ))
                    else: # y
                        shapes.append(dict(
                            type="line", x0=min_x, y0=coord, x1=max_x, y1=coord,
                            line=dict(color=color, width=linewidth, dash=dash)
                        ))

                    if label:
                        has_legend = True
                        fig.add_trace(go.Scatter(
                            x=[None], y=[None],
                            mode='lines',
                            line=dict(color=color, width=linewidth, dash=dash),
                            name=label,
                            showlegend=True
                        ))

            if custom_areas:
                for area in custom_areas:
                    ax0 = area.get('x0')
                    ax1 = area.get('x1')
                    ay0 = area.get('y0')
                    ay1 = area.get('y1')
                    
                    ax0 = min_x if ax0 is None else ax0
                    ax1 = max_x if ax1 is None else ax1
                    ay0 = min_y if ay0 is None else ay0
                    ay1 = max_y if ay1 is None else ay1
                    
                    label = area.get('label', '')
                    fill_color = area.get('fill_color', 'rgba(52, 152, 219, 0.25)')
                    border_color = area.get('border_color', 'rgba(52, 152, 219, 0.3)')
                    border_style = area.get('border_style', '-')
                    border_width = area.get('border_width', 1.0)
                    
                    dash = 'dash' if border_style == '--' else 'dot' if border_style == ':' else 'solid'
                    
                    shapes.append(dict(
                        type="rect", x0=ax0, y0=ay0, x1=ax1, y1=ay1,
                        fillcolor=fill_color,
                        line=dict(color=border_color, width=border_width, dash=dash) if border_color != 'none' else dict(width=0),
                        layer="above"
                    ))
                    
                    if label:
                        has_legend = True
                        fig.add_trace(go.Scatter(
                            x=[None], y=[None],
                            mode='markers',
                            marker=dict(
                                size=12,
                                color=fill_color,
                                symbol='square',
                                line=dict(color=border_color, width=border_width) if border_color != 'none' else dict(width=0)
                            ),
                            name=label,
                            showlegend=True
                        ))

            fig.update_layout(
                shapes=shapes,
                showlegend=has_legend,
                title=f"Warehouse Top View Footprint (Color Mode: {color_mode.capitalize()})",
                xaxis=dict(title=f"X coordinate ({self.unit})", showgrid=True, zeroline=False),
                yaxis=dict(title=f"Y coordinate ({self.unit})", scaleanchor="x", scaleratio=1, showgrid=True, zeroline=False, autorange="reversed"),
                plot_bgcolor='white',
                width=1000,
                height=900
            )
            return fig
            
        elif engine == "matplotlib":
            fig, ax = plt.subplots(figsize=(12, 10))
            ax.set_facecolor('white')
            
            for _, row in df_2d.iterrows():
                px, py = row['pos_x'], row['pos_y']
                w, d = row['loc_width'], row['loc_depth']
                util = row['volume_utilization']
                
                bg_color = '#ecf0f1'
                border_color = '#2c3e50'
                
                if color_mode == "volume":
                    if util <= 0:
                        fill_color = '#ecf0f1'
                    elif util <= volume_thresholds[0]:
                        fill_color = '#2ecc71'
                    elif util <= volume_thresholds[1]:
                        fill_color = '#f1c40f'
                    else:
                        fill_color = '#e74c3c'
                elif color_mode == "abc":
                    fill_color = get_abc_color(row['abc_num'], abc_colors)
                elif color_mode == "demand":
                    fill_color = self._get_continuous_color(row['total_demand'], demand_thresholds)
                elif color_mode == "trips":
                    fill_color = self._get_continuous_color(row['total_trips'], demand_thresholds)
                elif color_mode == "weight":
                    fill_color = self._get_continuous_color(row['total_weight'], demand_thresholds)
                else:
                    fill_color = bg_color
                    
                if color_mode == "volume":
                    # Draw background rectangle
                    ax.add_patch(patches.Rectangle((px, py), w, d, linewidth=0.5, edgecolor=border_color, facecolor=bg_color))
                    if util > 0:
                        # Draw filled proportional patch
                        fill_d = d * min(util, 1.0)
                        ax.add_patch(patches.Rectangle((px, py), w, fill_d, linewidth=0, facecolor=fill_color))
                else:
                    ax.add_patch(patches.Rectangle((px, py), w, d, linewidth=0.5, edgecolor=border_color, facecolor=fill_color))
            
            ax.autoscale()
            ax.set_aspect('equal')
            ax.invert_yaxis()
            ax.set_xlabel(f"X coordinate ({self.unit})")
            ax.set_ylabel(f"Y coordinate ({self.unit})")
            ax.set_title(f"Warehouse Top View Footprint (Color Mode: {color_mode.capitalize()})")
            
            if show_labels:
                for _, row in df_2d.iterrows():
                    px, py = row['pos_x'], row['pos_y']
                    w, d = row['loc_width'], row['loc_depth']
                    util = row['volume_utilization']
                    
                    indicator = ""
                    if color_mode == "volume":
                        indicator = f"{util*100:.0f}%"
                    elif color_mode == "demand":
                        indicator = f"{row['total_demand']:.0f}"
                    elif color_mode == "trips":
                        indicator = f"{row['total_trips']:.0f}"
                    elif color_mode == "weight":
                        indicator = f"{row['total_weight']:.1f}"
                    
                    effective_label_content = label_content
                    if color_mode == "abc" and label_content == "indicator":
                        effective_label_content = "address"
                        
                    if effective_label_content == "address":
                        label_text = self._get_end_address_range(row['loc_id'], sep="\n")
                    elif effective_label_content == "indicator":
                        label_text = indicator
                    else:
                        label_text = ""
                        
                    if label_text:
                        fs = self._get_matplotlib_fontsize(ax, label_text, w, d)
                        ax.text(px + w / 2.0, py + d / 2.0, label_text, 
                                ha='center', va='center', fontsize=fs, color='#555555')
            
            legend_handles = []

            if dotted_lines:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                min_x, max_x = min(xlim), max(xlim)
                min_y, max_y = min(ylim), max(ylim)
                for line in dotted_lines:
                    coord = line.get('coordinate')
                    axis = line.get('axis', 'x')
                    label = line.get('label', '')
                    color = line.get('color', '#7f8c8d')
                    linestyle = line.get('linestyle', '--')
                    linewidth = line.get('linewidth', 1.5)
                    
                    if axis == 'x':
                        ax.axvline(x=coord, color=color, linestyle=linestyle, linewidth=linewidth)
                    else: # y
                        ax.axhline(y=coord, color=color, linestyle=linestyle, linewidth=linewidth)

                    if label:
                        import matplotlib.lines as mlines
                        legend_handles.append(mlines.Line2D(
                            [], [], color=color, linestyle=linestyle, linewidth=linewidth, label=label
                        ))

            if custom_areas:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                min_x, max_x = min(xlim), max(xlim)
                min_y, max_y = min(ylim), max(ylim)
                for area in custom_areas:
                    ax0 = area.get('x0')
                    ax1 = area.get('x1')
                    ay0 = area.get('y0')
                    ay1 = area.get('y1')
                    
                    ax0 = min_x if ax0 is None else ax0
                    ax1 = max_x if ax1 is None else ax1
                    ay0 = min_y if ay0 is None else ay0
                    ay1 = max_y if ay1 is None else ay1
                    
                    label = area.get('label', '')
                    fill_color = self._parse_rgba_for_matplotlib(area.get('fill_color', 'rgba(52, 152, 219, 0.25)'))
                    border_color = self._parse_rgba_for_matplotlib(area.get('border_color', 'rgba(52, 152, 219, 0.3)'))
                    border_style = area.get('border_style', '-')
                    border_width = area.get('border_width', 1.0)
                    
                    rect = patches.Rectangle((ax0, ay0), ax1 - ax0, ay1 - ay0, 
                                             linewidth=border_width, edgecolor=border_color, 
                                             facecolor=fill_color, linestyle=border_style)
                    ax.add_patch(rect)
                    
                    if label:
                        legend_handles.append(patches.Patch(
                            facecolor=fill_color, edgecolor=border_color, linestyle=border_style, linewidth=border_width, label=label
                        ))

            if legend_handles:
                ax.legend(handles=legend_handles, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
            
            return fig
        else:
            raise ValueError("Engine must be 'plotly' or 'matplotlib'")

    def plot_front(self, locations_df, parts_df=None, allocations_df=None, color_mode="volume", 
                   demand_thresholds=None, volume_thresholds=None, abc_colors=None, 
                   use_physical_spacing=False, engine="plotly",
                   show_labels=False, label_content="indicator", seq_gap=2.0, corridor_gap=15.0,
                   dotted_lines=None, custom_areas=None):
        """
        Renders the vertical layout of a specific row or section of racks.
        """
        if label_content not in ["indicator", "address"]:
            raise ValueError("label_content must be 'indicator' or 'address'")

        # 1. Prepare data
        df = self._prepare_data(locations_df, parts_df, allocations_df)
        
        # 2. Determine physical horizontal extension based on variance
        # 2. Determine corridor orientation by comparing median coordinate gaps
        uniq_x = np.sort(df['pos_x'].unique())
        uniq_y = np.sort(df['pos_y'].unique())
        
        diff_x = np.diff(uniq_x) if len(uniq_x) > 1 else []
        diff_y = np.diff(uniq_y) if len(uniq_y) > 1 else []
        
        med_diff_x = np.median(diff_x) if len(diff_x) > 0 else float('inf')
        med_diff_y = np.median(diff_y) if len(diff_y) > 0 else float('inf')
        
        if med_diff_x <= med_diff_y:
            horiz_col = 'pos_x'
            depth_col = 'pos_y'
        else:
            horiz_col = 'pos_y'
            depth_col = 'pos_x'
            
        width_col = 'loc_width'
            
        # 3. Sort locations vertically (pos_z), by depth, and horizontally (horiz_col)
        df_sorted = df.sort_values(by=[depth_col, horiz_col, 'pos_z'])
        
        # Group by unique physical stack (pos_x, pos_y)
        groups = list(df_sorted.groupby([horiz_col, depth_col], sort=False))
        
        # Volume thresholds default
        if volume_thresholds is None:
            volume_thresholds = [0.5, 0.85]

        if engine == "plotly":
            fig = go.Figure()
            shapes = []
            hover_x = []
            hover_y = []
            hover_text = []
            
            label_x = []
            label_y = []
            label_texts = []
            label_sizes = []
            
            # First pass: calculate coordinates to find ranges for font scaling
            coords_x = []
            coords_y = []
            cur_seq_x = 0
            prev_depth_coord = None
            
            for (h_val, d_val), group in groups:
                row0 = group.iloc[0]
                w = row0[width_col]
                
                if use_physical_spacing:
                    draw_x = h_val
                else:
                    if prev_depth_coord is not None and d_val != prev_depth_coord:
                        cur_seq_x += corridor_gap
                    draw_x = cur_seq_x
                    cur_seq_x += w + seq_gap
                    prev_depth_coord = d_val
                    
                coords_x.append(draw_x)
                coords_x.append(draw_x + w)
                for _, row in group.iterrows():
                    pz = row['pos_z']
                    h = row['loc_height']
                    coords_y.append(pz)
                    coords_y.append(pz + h)
                    
            min_x = min(coords_x) if coords_x else 0.0
            max_x = max(coords_x) if coords_x else 1.0
            min_y = min(coords_y) if coords_y else 0.0
            max_y = max(coords_y) if coords_y else 1.0
            total_range_x = max(1.0, max_x - min_x)
            total_range_y = max(1.0, max_y - min_y)
            
            # Reset for main loop
            cur_seq_x = 0
            prev_depth_coord = None
            
            for (h_val, d_val), group in groups:
                row0 = group.iloc[0]
                w = row0[width_col]
                
                if use_physical_spacing:
                    draw_x = h_val
                else:
                    if prev_depth_coord is not None and d_val != prev_depth_coord:
                        cur_seq_x += corridor_gap
                    draw_x = cur_seq_x
                    cur_seq_x += w + seq_gap
                    prev_depth_coord = d_val
                
                for _, row in group.iterrows():
                    pz = row['pos_z']
                    h = row['loc_height']
                    util = row['volume_utilization']
                    
                    hover_x.append(draw_x + w / 2.0)
                    hover_y.append(pz + h / 2.0)
                    
                    txt = (f"Location ID: {row['loc_id']}<br>"
                           f"Position: Horiz={h_val:.1f}, Depth={d_val:.1f}, Z={pz:.1f}<br>"
                           f"Vol Utilization: {util*100:.1f}%<br>"
                           f"Weight: {row['total_weight']:.1f}<br>"
                           f"Demand: {row['total_demand']:.1f}<br>"
                           f"Pick Trips: {row['total_trips']:.1f}<br>"
                           f"ABC Class: {row['abc_class']}<br>"
                           f"SKUs: {row['allocated_skus']}")
                    hover_text.append(txt)
                    
                    bg_color = '#ecf0f1'
                    border_color = '#2c3e50'
                    
                    # Determine colors
                    if color_mode == "volume":
                        if util <= 0:
                            fill_color = '#ecf0f1'
                        elif util <= volume_thresholds[0]:
                            fill_color = '#2ecc71'
                        elif util <= volume_thresholds[1]:
                            fill_color = '#f1c40f'
                        else:
                            fill_color = '#e74c3c'
                    elif color_mode == "abc":
                        fill_color = get_abc_color(row['abc_class'], abc_colors)
                    elif color_mode == "demand":
                        fill_color = self._get_continuous_color(row['total_demand'], demand_thresholds)
                    elif color_mode == "trips":
                        fill_color = self._get_continuous_color(row['total_trips'], demand_thresholds)
                    elif color_mode == "weight":
                        fill_color = self._get_continuous_color(row['total_weight'], demand_thresholds)
                    else:
                        fill_color = bg_color
                        
                    if color_mode == "volume":
                        # Background box
                        shapes.append(dict(
                            type="rect", x0=draw_x, y0=pz, x1=draw_x+w, y1=pz+h,
                            line=dict(color=border_color, width=1),
                            fillcolor=bg_color
                        ))
                        # Proportional fill from bottom up
                        if util > 0:
                            fill_h = h * min(util, 1.0)
                            shapes.append(dict(
                                type="rect", x0=draw_x, y0=pz, x1=draw_x+w, y1=pz+fill_h,
                                line=dict(width=0),
                                fillcolor=fill_color
                            ))
                    else:
                        shapes.append(dict(
                            type="rect", x0=draw_x, y0=pz, x1=draw_x+w, y1=pz+h,
                            line=dict(color=border_color, width=1),
                            fillcolor=fill_color
                        ))
                        
                    if show_labels:
                        indicator = ""
                        if color_mode == "volume":
                            indicator = f"{util*100:.0f}%"
                        elif color_mode == "demand":
                            indicator = f"{row['total_demand']:.0f}"
                        elif color_mode == "trips":
                            indicator = f"{row['total_trips']:.0f}"
                        elif color_mode == "weight":
                            indicator = f"{row['total_weight']:.1f}"
                        
                        effective_label_content = label_content
                        if color_mode == "abc" and label_content == "indicator":
                            effective_label_content = "address"
                            
                        if effective_label_content == "address":
                            label_text = self._get_end_address(row['loc_id'])
                        elif effective_label_content == "indicator":
                            label_text = indicator
                        else:
                            label_text = ""
                            
                        if label_text:
                            fs = self._get_plotly_fontsize(label_text, w, h, total_range_x, total_range_y, fig_width=1200, fig_height=700)
                            label_x.append(draw_x + w / 2.0)
                            label_y.append(pz + h / 2.0)
                            label_texts.append(label_text)
                            label_sizes.append(fs)
                    
            fig.add_trace(go.Scatter(
                x=hover_x, y=hover_y,
                mode='markers',
                marker=dict(size=10, color='rgba(0,0,0,0)'),
                text=hover_text,
                hoverinfo='text',
                showlegend=False
            ))
            
            if show_labels and label_texts:
                fig.add_trace(go.Scatter(
                    x=label_x, y=label_y,
                    mode='text',
                    text=label_texts,
                    textposition='middle center',
                    textfont=dict(size=label_sizes, color='#555555', family='Arial, sans-serif'),
                    showlegend=False
                ))
            
            has_legend = False

            if dotted_lines:
                for line in dotted_lines:
                    coord = line.get('coordinate')
                    axis = line.get('axis', 'x')
                    label = line.get('label', '')
                    color = line.get('color', '#7f8c8d')
                    linestyle = line.get('linestyle', '--')
                    linewidth = line.get('linewidth', 1.5)
                    
                    dash = 'dash' if linestyle == '--' else 'dot' if linestyle == ':' else 'solid'
                    
                    if axis == 'x':
                        shapes.append(dict(
                            type="line", x0=coord, y0=min_y, x1=coord, y1=max_y,
                            line=dict(color=color, width=linewidth, dash=dash)
                        ))
                    else: # y
                        shapes.append(dict(
                            type="line", x0=min_x, y0=coord, x1=max_x, y1=coord,
                            line=dict(color=color, width=linewidth, dash=dash)
                        ))

                    if label:
                        has_legend = True
                        fig.add_trace(go.Scatter(
                            x=[None], y=[None],
                            mode='lines',
                            line=dict(color=color, width=linewidth, dash=dash),
                            name=label,
                            showlegend=True
                        ))

            if custom_areas:
                for area in custom_areas:
                    ax0 = area.get('x0')
                    ax1 = area.get('x1')
                    ay0 = area.get('y0')
                    ay1 = area.get('y1')
                    
                    ax0 = min_x if ax0 is None else ax0
                    ax1 = max_x if ax1 is None else ax1
                    ay0 = min_y if ay0 is None else ay0
                    ay1 = max_y if ay1 is None else ay1
                    
                    label = area.get('label', '')
                    fill_color = area.get('fill_color', 'rgba(52, 152, 219, 0.25)')
                    border_color = area.get('border_color', 'rgba(52, 152, 219, 0.3)')
                    border_style = area.get('border_style', '-')
                    border_width = area.get('border_width', 1.0)
                    
                    dash = 'dash' if border_style == '--' else 'dot' if border_style == ':' else 'solid'
                    
                    shapes.append(dict(
                        type="rect", x0=ax0, y0=ay0, x1=ax1, y1=ay1,
                        fillcolor=fill_color,
                        line=dict(color=border_color, width=border_width, dash=dash) if border_color != 'none' else dict(width=0),
                        layer="above"
                    ))
                    
                    if label:
                        has_legend = True
                        fig.add_trace(go.Scatter(
                            x=[None], y=[None],
                            mode='markers',
                            marker=dict(
                                size=12,
                                color=fill_color,
                                symbol='square',
                                line=dict(color=border_color, width=border_width) if border_color != 'none' else dict(width=0)
                            ),
                            name=label,
                            showlegend=True
                        ))

            fig.update_layout(
                shapes=shapes,
                showlegend=has_legend,
                title=f"Warehouse Front elevation view (Color Mode: {color_mode.capitalize()})",
                xaxis=dict(title=f"Horizontal position ({self.unit})", showgrid=True, zeroline=False),
                yaxis=dict(title=f"Elevation Z ({self.unit})", scaleanchor="x", scaleratio=1, showgrid=True, zeroline=False),
                plot_bgcolor='white',
                width=1200,
                height=700
            )
            return fig
            
        elif engine == "matplotlib":
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.set_facecolor('white')
            
            cur_seq_x = 0
            prev_depth_coord = None
            
            for (h_val, d_val), group in groups:
                row0 = group.iloc[0]
                w = row0[width_col]
                
                if use_physical_spacing:
                    draw_x = h_val
                else:
                    if prev_depth_coord is not None and d_val != prev_depth_coord:
                        cur_seq_x += corridor_gap
                    draw_x = cur_seq_x
                    cur_seq_x += w + seq_gap
                    prev_depth_coord = d_val
                    
                for _, row in group.iterrows():
                    pz = row['pos_z']
                    h = row['loc_height']
                    util = row['volume_utilization']
                    
                    bg_color = '#ecf0f1'
                    border_color = '#2c3e50'
                    
                    if color_mode == "volume":
                        if util <= 0:
                            fill_color = '#ecf0f1'
                        elif util <= volume_thresholds[0]:
                            fill_color = '#2ecc71'
                        elif util <= volume_thresholds[1]:
                            fill_color = '#f1c40f'
                        else:
                            fill_color = '#e74c3c'
                    elif color_mode == "abc":
                        fill_color = get_abc_color(row['abc_class'], abc_colors)
                    elif color_mode == "demand":
                        fill_color = self._get_continuous_color(row['total_demand'], demand_thresholds)
                    elif color_mode == "trips":
                        fill_color = self._get_continuous_color(row['total_trips'], demand_thresholds)
                    elif color_mode == "weight":
                        fill_color = self._get_continuous_color(row['total_weight'], demand_thresholds)
                    else:
                        fill_color = bg_color
                        
                    if color_mode == "volume":
                        ax.add_patch(patches.Rectangle((draw_x, pz), w, h, linewidth=0.5, edgecolor=border_color, facecolor=bg_color))
                        if util > 0:
                            fill_h = h * min(util, 1.0)
                            ax.add_patch(patches.Rectangle((draw_x, pz), w, fill_h, linewidth=0, facecolor=fill_color))
                    else:
                        ax.add_patch(patches.Rectangle((draw_x, pz), w, h, linewidth=0.5, edgecolor=border_color, facecolor=fill_color))
            
            ax.autoscale()
            ax.set_aspect('equal')
            ax.set_xlabel(f"Horizontal position ({self.unit})")
            ax.set_ylabel(f"Elevation Z ({self.unit})")
            ax.set_title(f"Warehouse Front elevation view (Color Mode: {color_mode.capitalize()})")
            
            if show_labels:
                cur_seq_x = 0
                prev_depth_coord = None
                
                for (h_val, d_val), group in groups:
                    row0 = group.iloc[0]
                    w = row0[width_col]
                    
                    if use_physical_spacing:
                        draw_x = h_val
                    else:
                        if prev_depth_coord is not None and d_val != prev_depth_coord:
                            cur_seq_x += corridor_gap
                        draw_x = cur_seq_x
                        cur_seq_x += w + seq_gap
                        prev_depth_coord = d_val
                        
                    for _, row in group.iterrows():
                        pz = row['pos_z']
                        h = row['loc_height']
                        util = row['volume_utilization']
                        
                        indicator = ""
                        if color_mode == "volume":
                            indicator = f"{util*100:.0f}%"
                        elif color_mode == "demand":
                            indicator = f"{row['total_demand']:.0f}"
                        elif color_mode == "trips":
                            indicator = f"{row['total_trips']:.0f}"
                        elif color_mode == "weight":
                            indicator = f"{row['total_weight']:.1f}"
                        
                        effective_label_content = label_content
                        if color_mode == "abc" and label_content == "indicator":
                            effective_label_content = "address"
                            
                        if effective_label_content == "address":
                            label_text = self._get_end_address(row['loc_id'])
                        elif effective_label_content == "indicator":
                            label_text = indicator
                        else:
                            label_text = ""
                            
                        if label_text:
                            fs = self._get_matplotlib_fontsize(ax, label_text, w, h)
                            ax.text(draw_x + w / 2.0, pz + h / 2.0, label_text, 
                                    ha='center', va='center', fontsize=fs, color='#555555')
            
            legend_handles = []

            if dotted_lines:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                min_x, max_x = min(xlim), max(xlim)
                min_y, max_y = min(ylim), max(ylim)
                for line in dotted_lines:
                    coord = line.get('coordinate')
                    axis = line.get('axis', 'x')
                    label = line.get('label', '')
                    color = line.get('color', '#7f8c8d')
                    linestyle = line.get('linestyle', '--')
                    linewidth = line.get('linewidth', 1.5)
                    
                    if axis == 'x':
                        ax.axvline(x=coord, color=color, linestyle=linestyle, linewidth=linewidth)
                    else: # y
                        ax.axhline(y=coord, color=color, linestyle=linestyle, linewidth=linewidth)

                    if label:
                        import matplotlib.lines as mlines
                        legend_handles.append(mlines.Line2D(
                            [], [], color=color, linestyle=linestyle, linewidth=linewidth, label=label
                        ))

            if custom_areas:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                min_x, max_x = min(xlim), max(xlim)
                min_y, max_y = min(ylim), max(ylim)
                for area in custom_areas:
                    ax0 = area.get('x0')
                    ax1 = area.get('x1')
                    ay0 = area.get('y0')
                    ay1 = area.get('y1')
                    
                    ax0 = min_x if ax0 is None else ax0
                    ax1 = max_x if ax1 is None else ax1
                    ay0 = min_y if ay0 is None else ay0
                    ay1 = max_y if ay1 is None else ay1
                    
                    label = area.get('label', '')
                    fill_color = self._parse_rgba_for_matplotlib(area.get('fill_color', 'rgba(52, 152, 219, 0.25)'))
                    border_color = self._parse_rgba_for_matplotlib(area.get('border_color', 'rgba(52, 152, 219, 0.3)'))
                    border_style = area.get('border_style', '-')
                    border_width = area.get('border_width', 1.0)
                    
                    rect = patches.Rectangle((ax0, ay0), ax1 - ax0, ay1 - ay0, 
                                             linewidth=border_width, edgecolor=border_color, 
                                             facecolor=fill_color, linestyle=border_style)
                    ax.add_patch(rect)
                    
                    if label:
                        legend_handles.append(patches.Patch(
                            facecolor=fill_color, edgecolor=border_color, linestyle=border_style, linewidth=border_width, label=label
                        ))

            if legend_handles:
                ax.legend(handles=legend_handles, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
            
            return fig
        else:
            raise ValueError("Engine must be 'plotly' or 'matplotlib'")
