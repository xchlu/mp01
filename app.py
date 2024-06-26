import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
from shiny import reactive, render, req
from shiny.express import input, ui
import pandas as pd
from ipyleaflet import Map, Marker
from shiny.express import ui
from shinywidgets import render_widget
from prophet import Prophet
import process_data

# Load data
cities = pd.read_csv("data/cities.csv")


@reactive.calc
def get_coordinate_and_lat_lng():
    return process_data.get_weather_data(latitude=cities.at[int(input.city()), "lat"],
                                         longitude=cities.at[int(input.city()), "lng"],
                                         start_date=input.daterange()[0],
                                         end_date=input.daterange()[1],
                                         temperature_unit="fahrenheit" if input.units() == "1" else "celsius")


# Add page title and sidebar
ui.page_opts(title="Daily Heat Pump Efficiency Counter", fillable=True)
with ui.sidebar(bg="#f8f8f8", width=400):
    # set the selected value to be Urbana, Illiois

    condition = cities['city_state'] == "Urbana, Illinois"
    urbana = cities[condition].index[0].item()

    ui.input_selectize("city", "City", choices=cities["city_state"], selected=urbana, width="100%")


    @render.text(inline=True)
    def text():
        coordinate, lat_lng = get_coordinate_and_lat_lng()
        lat_lng = lat_lng[12:]
        return lat_lng


    ui.input_date_range("daterange", "Dates", min="2020-01-01", max="2024-01-01", start="2022-01-01", end="2024-01-01")
    ui.input_numeric("numeric", "Years to Forecast", 1, min=1, max=5)
    ui.input_radio_buttons(
        "trend",
        "Forecast Trend",
        {"flat": "Flat", "linear": "Linear"}, selected="flat"
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
            return ui.input_slider("plot_temp", "Plot Temperature", min=-15, max=50, value=5), ui.input_slider("slider",
                                                                                                               "Table "
                                                                                                               "Temperatures",
                                                                                                               min=-25,
                                                                                                               max=60,
                                                                                                               value=[0,
                                                                                                                      15])
        if "2" == x:
            return ui.input_slider("plot_temp", "Plot Temperature", min=-25, max=10, value=-15), ui.input_slider(
                "slider", "Table Temperatures", min=-30, max=15, value=[-20, -10])


    @render_widget
    def map():
        coordinate, lat_lng = get_coordinate_and_lat_lng()

        latlng = lat_lng.split(" ")
        lat = str(latlng[0][:-2])
        lng = str(latlng[1][:-2])
        # print(lat, lng)
        point = Marker(location=(lat, lng), draggable=False)
        map = Map(center=(lat, lng), zoom=12)
        map.add_layer(point)
        return map

with ui.navset_pill(id="tab"):
    with ui.nav_panel("Historical"):
        @render.plot(alt="A scatterplot of the lowest temperature over time")
        def plot():

            df, _ = get_coordinate_and_lat_lng()
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
            plt.axhline(y=threshold, color='grey', linestyle='-', alpha=0.5)
            y_label = "Daily Minimum Temperature °F" if input.units() == "1" else "Daily Minimum Temperature °C"
            ax.set_ylabel(y_label)
            ax.yaxis.set_major_locator(MultipleLocator(base=25))
            plt.grid()

            return fig


        @render.data_frame
        @reactive.calc
        def temperature_table():
            # Calculate the temperature and days below the temperature
            coordinate, _ = get_coordinate_and_lat_lng()
            min = input.slider()[0]
            max = input.slider()[1]
            temp_range = range(max, min - 1, -1)
            results = []
            for temp in temp_range:
                below = coordinate["temperature_2m"] < temp
                proportion_of_below = below.mean().round(3)

                results.append({'Temp': temp, 'Days Below': below.sum(),
                                'Proportion Below': proportion_of_below})
            df = pd.DataFrame(results)
            return render.DataGrid(df, row_selection_mode='multiple', width='100%', height='auto', summary='')

    with ui.nav_panel("Forcast"):
        @render.plot(alt="A forcast scatterplot of the lowest temperature over time")
        def forecast():
            coordinate, _ = get_coordinate_and_lat_lng()
            df = coordinate
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

            model = Prophet(growth=input.trend(), interval_width=0.95)
            df_prophet = df.rename(columns={"date": "ds", "temperature_2m": "y"})
            model.fit(df_prophet)
            future = model.make_future_dataframe(periods=365 * int(input.numeric()))
            global forecast
            forecast = model.predict(future)

            last_date = df_prophet['ds'].max()

            forecast_future = forecast[forecast['ds'] > last_date]
            fig = model.plot(forecast_future)
            threshold = input.plot_temp()
            fig.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

            # set those points which are below the temperature to be transparent
            plt.axhline(y=threshold, color='grey', linestyle='-', alpha=0.5)
            y_label = "Daily Minimum Temperature °F" if input.units() == "1" else "Daily Minimum Temperature °C"
            fig.gca().set_ylabel(y_label)

            return fig


        @render.data_frame
        def forcast_temperature_table():
            get_coordinate_and_lat_lng()
            df = forecast
            min = input.slider()[0]
            max = input.slider()[1]
            temp_range = range(max, min - 1, -1)
            results = []
            for temp in temp_range:
                below = df["yhat_lower"] < temp
                proportion_of_below = below.mean().round(3)

                results.append({'Temp': temp, 'Days Below': below.sum(),
                                'Proportion Below': proportion_of_below})
            df = pd.DataFrame(results)
            return render.DataGrid(df, row_selection_mode='multiple', width='100%', height='auto', summary='')

    with ui.nav_panel("About"):
        ui.markdown(
            """
            # About this application
            ## Context
            This is an application designed for potential heat pump customers to
            make informed decisions on their choices. As the efficacy of heap pump is
            affected by temperature, it is important for customers to check munufacturers'
            performance specifications and learn if the heat pump works well in extremely
            cold environments.

            This application provides users with historical daily minimum temperature data (a plot and a table) from 
            cities in the whole United States. Additionally, you are able to access forecast data
            up to **five years**. Hope this will help you decide which heat pump suits you best,
            or maybe get a furnace.

            ## Usage instructions
            There is a sidebar on the left for you to set the options. You can select your city, 
            the date range of data you want to get, how many years you want to predict,
            the trend of forecast model, and options for plot and table. You will also
            see a map showing your location. 

            There are three navigation bar on the right of the side bar. As the name suggests,
            the 'Historical' section shows a plot and a table for historical data, while 'the Forecast' section
            shows a plot and a table for forecast data. The 'About' section is what you are 
            seeing at this moment.
            

            ## Citation
            Location data source: This application is using the free tier US cities data 
            from [Simple Maps](https://simplemaps.com/data/us-cities).

            Weather data source: Our weather data is from [Open-Meteo](https://open-meteo.com/) 
            and their[Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).
            """
        )
