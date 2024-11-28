import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
import mplcursors

def load_and_clean_data(file_path):
    """Load and clean the air quality data."""
    data = pd.read_csv(file_path)
    
    # Data Cleaning
    data = data.drop(columns=['Message'])
    data['Start_Date'] = pd.to_datetime(data['Start_Date'], format='%m/%d/%Y')
    data['Data Value'] = pd.to_numeric(data['Data Value'], errors='coerce')
    data = data.dropna(subset=['Data Value'])
    
    # Assuming the data contains 'Season' or 'Year' columns if it's annual or seasonal
    # Here, we group by year or season instead of exact date
    data['Year'] = data['Start_Date'].dt.year
    # If 'Season' column is present, we can use that as well
    # For now, we assume the data contains a season column, if not, use 'Year'
    
    return data

def create_temporal_trends_figure(data, group_by='Year'):
    """Create interactive temporal trends figure, group by year or season."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Group data by the chosen temporal unit (year or season)
    if group_by == 'Year':
        data_grouped = data.groupby(['Year', 'Name'])['Data Value'].mean().reset_index()
    elif group_by == 'Season':
        data['Season'] = data['Start_Date'].dt.month % 12 // 3 + 1
        data_grouped = data.groupby(['Season', 'Name'])['Data Value'].mean().reset_index()
    
    # Create a dictionary to store line objects and their corresponding names
    line_dict = {}
    
    # Plot each indicator separately to maintain control over line objects
    for name in data_grouped['Name'].unique():
        mask = data_grouped['Name'] == name
        line = ax.plot(
            data_grouped[mask][group_by],
            data_grouped[mask]['Data Value'],
            label=name,
            marker='o'
        )[0]
        line_dict[line] = name
    
    # Customize appearance
    ax.set_title(f'Trends in Air Quality Indicators Over Time (Grouped by {group_by})', 
                fontsize=14, pad=20)
    ax.set_xlabel(group_by, fontsize=12)
    ax.set_ylabel('Data Value', fontsize=12)
    
    # Add legend
    ax.legend(
        title='Indicator Name',
        title_fontsize=12,
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        frameon=True
    )
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Add hover tooltips with correct names
    cursor = mplcursors.cursor(ax.lines, hover=True)
    
    @cursor.connect("add")
    def on_hover(sel):
        # Get the actual name from our line dictionary
        line_name = line_dict[sel.artist]
        x = sel.target[0]
        y = sel.target[1]
        sel.annotation.set_text(f'{line_name}\n{group_by}: {x}\nValue: {y:.2f}')
    
    plt.tight_layout()
    return fig


def create_geographic_trends_figure(data):
    """Create interactive geographic trends figure."""
    fig, ax = plt.subplots(figsize=(12, 8))  # Increased height for better readability
    
    # Calculate averages
    avg_geo_data = (data.groupby('Geo Place Name')['Data Value']
                   .mean()
                   .sort_values(ascending=True)
                   .reset_index())
    
    # Enhanced plotting
    bars = sns.barplot(
        data=avg_geo_data,
        x='Data Value',
        y='Geo Place Name',
        ax=ax,
        palette='viridis'
    )
    
    # Customize appearance
    ax.set_title('Average Air Quality by Region', 
                fontsize=14, pad=20)
    ax.set_xlabel('Average Data Value', fontsize=12)
    ax.set_ylabel('Region', fontsize=12)
    
    # Add hover tooltips
    cursor = mplcursors.cursor(bars.patches, hover=True)
    @cursor.connect("add")
    def on_hover(sel):
        bar_idx = bars.patches.index(sel.artist)
        region = avg_geo_data.iloc[bar_idx]['Geo Place Name']
        value = avg_geo_data.iloc[bar_idx]['Data Value']
        sel.annotation.set_text(f'Region: {region}\nValue: {value:.2f}')
    
    # Adjust layout for better visibility
    plt.margins(y=0.01)
    plt.tight_layout()
    
    return fig

class AirQualityApp:
    """Main application class for air quality visualization."""
    
    def __init__(self, root, temporal_fig, geographic_fig):
        self.root = root
        self.root.title("Air Quality Analysis Dashboard")
        
        # Store figures
        self.figures = {
            'temporal': temporal_fig,
            'geographic': geographic_fig
        }
        self.current_figure = 'temporal'
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface with navigation toolbar."""
        # Create main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(expand=True, fill='both')
        
        # Add title label
        title = tk.Label(
            main_frame,
            text="Air Quality Analysis Dashboard",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=(0, 10))
        
        # Initialize canvas
        self.canvas = FigureCanvasTkAgg(
            self.figures[self.current_figure],
            master=main_frame
        )
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill='both')
        
        # Add navigation toolbar for zoom functionality
        self.toolbar = NavigationToolbar2Tk(self.canvas, main_frame)
        self.toolbar.update()
        self.toolbar.pack(pady=5)
        
        # Create button with better styling
        self.switch_button = tk.Button(
            main_frame,
            text="Switch View",
            command=self.switch_graph,
            font=("Helvetica", 12),
            pady=5,
            padx=10
        )
        self.switch_button.pack(pady=10)
        
    def switch_graph(self):
        """Switch between temporal and geographic views."""
        # Clear current canvas and toolbar
        self.canvas_widget.pack_forget()
        self.toolbar.pack_forget()
        
        # Switch figures
        self.current_figure = ('geographic' if self.current_figure == 'temporal'
                             else 'temporal')
        
        # Update canvas
        self.canvas = FigureCanvasTkAgg(
            self.figures[self.current_figure],
            master=self.root
        )
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill='both')
        
        # Update toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.toolbar.pack(pady=5)
        
        self.canvas.draw()

def main():
    # Set style for better-looking graphs
    sns.set_theme(style="whitegrid")
    
    # Load and clean data
    file_path = r'C:\paid\Air_Quality.csv'
    data = load_and_clean_data(file_path)
    
    # Create figures with seasonal or annual grouping
    temporal_fig = create_temporal_trends_figure(data, group_by='Year')  # or 'Season'
    geographic_fig = create_geographic_trends_figure(data)
    
    # Initialize and run application
    root = tk.Tk()
    app = AirQualityApp(root, temporal_fig, geographic_fig)
    root.mainloop()

if __name__ == "__main__":
    main()
