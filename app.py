from shinywidgets import render_plotly
from shiny.ui import page_navbar
from functools import partial
import matplotlib.pyplot as plt
from shiny import reactive, render, req
from shiny.express import input, ui
import pandas as pd;
from ipyleaflet import Map  
from shiny.express import ui
from shinywidgets import render_widget  
import process_data

# Load data and compute static values
cities = pd.read_csv("data/cities.csv")

# Add page title and sidebar
ui.page_opts(title="Daily Heat Pump Efficiency Counter", fillable=True)
with ui.sidebar(bg="#f8f8f8", width=400):  
    # Add selectizeInput,defualt value is New York
    ui.input_selectize("city", "City", choices=cities["city_state"])
    # print the lat, lng of the selected city
    # make it inline and at the middle within the sidebar
    @render.text(inline=True)  
    def text():
        # return the lat, lng of the selected city
        city = input.city()
        # lat_lng = ', '.join(map(str, cities.iloc[int(city)][["lat", "lng"]].values))
        # transform the lat, lng to a String without the brackets
        global coordinate
        coordinate, lat_lng  = process_data.get_weather_data(latitude=cities.at[int(city),"lat"], longitude=cities.at[int(city),"lng"], start_date=input.daterange()[0], end_date=input.daterange()[1], temperature_unit="fahrenheit" if input.units() == "1" else "celsius")

        return lat_lng[12:]
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
            selected="1"
    )  
    ui.input_checkbox_group("time", "Plot Options", ["Weekly Rolling Average", "Monthly Rolling Average"], inline=True)

    
    @render.ui
    def result():
        x = input.units()
        
        if "1" == x:
            return ui.input_slider("plot_temp", "Plot Temperature", min=-15, max=50,value=5), ui.input_slider("slider", "Table Temperatures", min=-25, max=60,value=[0, 15])
        if "2" == x:
            return ui.input_slider("plot_temp", "Plot Temperature", min=-25, max=10,value=-15), ui.input_slider("slider", "Table Temperatures", min=-30, max=15,value=[-20, -10])  
    
    @render_widget  
    def map():
        city = input.city()
        # get the lat, lng of the selected city
        lat_lng = cities.iloc[int(city)][["lat", "lng"]].values.tolist()
        return Map(center=lat_lng, zoom=10) 



with ui.navset_card_tab(id="tab"):  
    with ui.nav_panel("Historical"):
        @render.plot(alt="A scatterplot of the lowest temperature over time")  
        def plot():  
            df = coordinate
            
            fig, ax = plt.subplots()
            ax.hist(mass, input.n(), density=True)
            ax.set_title("Palmer Penguin Masses")
            ax.set_xlabel("Mass (g)")
            ax.set_ylabel("Density")

            return fig  
        
        
        
        # for coordinates data, generate a form including a table which have Temperature and Days below the temperature and proportion of days below the temperature
        
        @render.data_frame
        def temperature_table():
            # Calculate the temperature and days below the temperature
            # check out the column names of the dataframe
            print(coordinate)
            
            min = input.slider()[0]
            max = input.slider()[1]
            temp_range = range(max, min-1, -1)
            results = []
            for temp in temp_range:
                below = coordinate["temperature_2m"] < temp
                proportion_of_below = below.mean().round(3)
                
                results.append({'Temp': temp,'Days Below':below.sum(),
                    'Proportion Below': proportion_of_below})
            df = pd.DataFrame(results)
            return render.DataGrid(df)
    with ui.nav_panel("Forcast"):
        "Panel B content"

    with ui.nav_panel("About"):
        "his is some text!"
