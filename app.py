from shinywidgets import render_plotly
from shiny.ui import page_navbar
from functools import partial
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from shiny import reactive, render, req
from shiny.express import input, ui
import pandas as pd;
from ipyleaflet import Map  
from shiny.express import ui
from shinywidgets import render_widget  
from prophet import Prophet
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
        {"flat": "Flat", "linear": "Linear"},selected="flat"
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



  
with ui.navset_pill(id="tab"): 
    with ui.nav_panel("Historical"):
        @render.plot(alt="A scatterplot of the lowest temperature over time")  
        def plot():  
            
            coordinate,_ = process_data.get_weather_data(latitude=cities.at[int(input.city()),"lat"], longitude=cities.at[int(input.city()),"lng"], start_date=input.daterange()[0], end_date=input.daterange()[1], temperature_unit="fahrenheit" if input.units() == "1" else "celsius")
            
            df = coordinate
            df['date'] = pd.to_datetime(df['date'])
            fig, ax = plt.subplots()
            threshold = input.plot_temp()
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            if "Weekly Rolling Average" in input.time():
                weekly_rolling = df['temperature_2m'].rolling(window=7).mean()
                ax.plot(df['date'], weekly_rolling, color='orange')
            if "Monthly Rolling Average" in input.time():
                monthly_rolling = df['temperature_2m'].rolling(window=30).mean()
                ax.plot(df['date'], monthly_rolling, color='blue')
            # set those points which are below the temperature to be transparent
            colors = ['grey' if temp < threshold else 'black' for temp in df['temperature_2m']]
            alpha = [0.5 if temp < threshold else 1 for temp in df['temperature_2m']]
            ax.scatter(df['date'], df['temperature_2m'], c=colors, alpha=alpha, s=15)            
            plt.axhline(y=threshold, color='grey', linestyle='-',alpha=0.5)
            y_label = "Daily Minimum Temperature °F" if input.units() == "1" else "Daily Minimum Temperature °C"
            ax.set_ylabel(y_label)
            ax.yaxis.set_major_locator(MultipleLocator(base=25)) 
            plt.grid()


            return fig  
        
        
        
        # for coordinates data, generate a form including a table which have Temperature and Days below the temperature and proportion of days below the temperature
        
        @render.data_frame
        def temperature_table():
            # Calculate the temperature and days below the temperature
            # check out the column names of the dataframe
            
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
            return render.DataGrid(df, row_selection_mode='multiple', width= '100%', height='auto', summary='')
    with ui.nav_panel("Forcast"):
        @render.plot(alt="A forcast scatterplot of the lowest temperature over time")  
        def forecast():
            # get the forecast data
            coordinate,_ = process_data.get_weather_data(latitude=cities.at[int(input.city()),"lat"], longitude=cities.at[int(input.city()),"lng"], start_date=input.daterange()[0], end_date=input.daterange()[1], temperature_unit="fahrenheit" if input.units() == "1" else "celsius")
            df = coordinate
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            model = Prophet(growth=input.trend())
            df_prophet = df.rename(columns={"date": "ds", "temperature_2m": "y"})
            model.fit(df_prophet)
            future = model.make_future_dataframe(periods=365*int(input.numeric()))
            global forecast
            forecast = model.predict(future)
            last_date = df_prophet['ds'].max()

            forecast_future = forecast[forecast['ds'] > last_date]
            fig = model.plot(forecast_future)
            threshold = input.plot_temp()
            fig.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

            # set those points which are below the temperature to be transparent
            plt.axhline(y=threshold, color='grey', linestyle='-',alpha=0.5)
            y_label = "Daily Minimum Temperature °F" if input.units() == "1" else "Daily Minimum Temperature °C"
            # set the y label
            fig.gca().set_ylabel(y_label)

            return fig
        @render.data_frame
        def forcast_temperature_table():
            # reactive when the forecast is generated
            trend = input.trend()
            df = forecast
            min = input.slider()[0]
            max = input.slider()[1]
            temp_range = range(max, min-1, -1)
            results = []
            for temp in temp_range:
                # get the temperature and days below the temperature
                below = df["yhat_lower"] < temp
                proportion_of_below = below.mean().round(3)
                
                results.append({'Temp': temp,'Days Below':below.sum(),
                    'Proportion Below': proportion_of_below})
            df = pd.DataFrame(results)
            return render.DataGrid(df, row_selection_mode='multiple', width= '100%', height='auto', summary='')


    with ui.nav_panel("About"):
        "his is some text!"
