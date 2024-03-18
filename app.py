from shinywidgets import render_plotly

from shiny import reactive, render, req
from shiny.express import input, ui
import numpy as np;
import pandas as pd;

# Load data and compute static values
cities = pd.read_csv("data/cities.csv")

# Add page title and sidebar
ui.page_opts(title="Daily Heat Pump Efficiency Counter", fillable=True)
with ui.sidebar(width=400):
    # Add selectizeInput,defualt value is New York
    ui.input_selectize("city", "City", choices=cities["city_state"])
    # print the lat, lng of the selected city
    # make it inline and at the middle within the sidebar
    @render.text(inline=True)  
    def text():
        # return the lat, lng of the selected city
        city = input.city()
        lat_lng = ', '.join(map(str, cities.iloc[int(city)][["lat", "lng"]].values))
        return lat_lng
    ui.input_date_range("daterange", "Dates", min="2020-01-01" , max="2024-01-01", start="2022-01-01", end="2024-01-01") 
    ui.input_numeric("numeric", "Years to Forecast", 1, min=1, max=5)  
    ui.input_radio_buttons(  
        "trend",  
        "Forecast Trend",  
        {"1": "Flat", "2": "Linear"} 
    )  

        
    ui.input_radio_buttons(  
            "units",  
            "Units",  
            {"1": "Fahrenheit", "2": "Celsius"},
            selected="2"
    )  
    
    @render.ui
    def result():
        x = input.units()
        
        if "1" == x:
            return ui.input_slider("plot_temp", "Plot Temperature", min=-15, max=50,value=[15, 45]), ui.input_slider("slider", "Table Temperatures", min=-25, max=60,value=[35, 65])
        if "2" == x:
            return ui.input_slider("plot_temp", "Plot Temperature", min=-20, max=50,value=[15, 45]), ui.input_slider("slider", "Table Temperatures", min=-25, max=60,value=[35, 65])  

    
    ui.input_checkbox_group("time", "Plot Options", ["Weekly Rolling Average", "Monthly Rolling Average"], inline=True)
