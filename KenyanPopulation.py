import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import json

# Page configuration
st.set_page_config(
    page_title="Kenyan Counties Population",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# Load data
try:
    df_reshaped = pd.read_csv('Mydata.csv')
except FileNotFoundError:
    st.error("The file 'Mydata.csv' is not found.")
    raise

# Load GeoJSON data
try:
    with open('gadm41_KEN_1.geojson') as f:
        kenya_geojson = json.load(f)
except FileNotFoundError:
    st.error("The file 'gadm41_KEN_1.geojson' is not found.")
    raise

# Sidebar
with st.sidebar:
    st.title('📈 Kenyan Counties Population')

    year_list = list(df_reshaped.year.unique())[::-1]

    selected_year = st.selectbox('Select a year', year_list)
    df_selected_year = df_reshaped[df_reshaped.year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="population", ascending=False)

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo',
                        'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)


# Plots
def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = alt.Chart(input_df).mark_rect().encode(
        y=alt.Y(f'{input_y}:O',
                axis=alt.Axis(title="Year", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
        x=alt.X(f'{input_x}:O', axis=alt.Axis(title="", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'max({input_color}):Q', legend=None, scale=alt.Scale(scheme=input_color_theme)),
        stroke=alt.value('black'),
        strokeWidth=alt.value(0.25),
    ).properties(width=900).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    return heatmap


def make_choropleth(input_df, input_id, input_column, input_color_theme, geojson):
    choropleth = px.choropleth(input_df, geojson=geojson, locations=input_id, featureidkey="properties.id",
                               color=input_column,
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_year.population)),
                               labels={'population': 'Population'},
                               scope="africa")
    choropleth.update_geos(fitbounds="locations", visible=False)
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth


def make_donut(input_response, input_text, input_color):
    chart_color = {
        'blue': ['#29b5e8', '#155F7A'],
        'green': ['#27AE60', '#12783D'],
        'orange': ['#F39C12', '#875A12'],
        'red': ['#E74C3C', '#781F16']
    }[input_color]

    source = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100 - input_response, input_response]
    })
    source_bg = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100, 0]
    })

    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta="% value",
        color=alt.Color("Topic:N", scale=alt.Scale(domain=[input_text, ''], range=chart_color), legend=None),
    ).properties(width=130, height=130)

    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700,
                          fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="% value",
        color=alt.Color("Topic:N", scale=alt.Scale(domain=[input_text, ''], range=chart_color), legend=None),
    ).properties(width=130, height=130)
    return plot_bg + plot + text


def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'


def calculate_population_difference(input_df, input_year):
    selected_year_data = input_df[input_df['year'] == input_year].reset_index()
    previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
    selected_year_data['population_difference'] = selected_year_data.population.sub(previous_year_data.population,
                                                                                    fill_value=0)
    return pd.concat([selected_year_data.counties, selected_year_data.id, selected_year_data.population,
                      selected_year_data.population_difference], axis=1).sort_values(by="population_difference",
                                                                                     ascending=False)


# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown('#### Gains/Losses')

    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)

    if selected_year > 2010:
        first_county_name = df_population_difference_sorted.counties.iloc[0]
        first_county_population = format_number(df_population_difference_sorted.population.iloc[0])
        first_county_delta = format_number(df_population_difference_sorted.population_difference.iloc[0])
    else:
        first_county_name = '-'
        first_county_population = '-'
        first_county_delta = ''
    st.metric(label=first_county_name, value=first_county_population, delta=first_county_delta)

    if selected_year > 2010:
        last_county_name = df_population_difference_sorted.counties.iloc[-1]
        last_county_population = format_number(df_population_difference_sorted.population.iloc[-1])
        last_county_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])
    else:
        last_county_name = '-'
        last_county_population = '-'
        last_county_delta = ''
    st.metric(label=last_county_name, value=last_county_population, delta=last_county_delta)

    st.markdown('#### Counties Migration')

    if selected_year > 2010:
        df_greater_50000 = df_population_difference_sorted[
            df_population_difference_sorted.population_difference > 50000]
        df_less_50000 = df_population_difference_sorted[df_population_difference_sorted.population_difference < -50000]

        countries_migration_greater = round(
            (len(df_greater_50000) / df_population_difference_sorted.counties.nunique()) * 100)
        countries_migration_less = round((len(df_less_50000) / df_population_difference_sorted.counties.nunique()) * 100)
        donut_chart_greater = make_donut(countries_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(countries_migration_less, 'Outbound Migration', 'red')
    else:
        countries_migration_greater = 0
        countries_migration_less = 0
        donut_chart_greater = make_donut(countries_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(countries_migration_less, 'Outbound Migration', 'red')

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write('Inbound')
        st.altair_chart(donut_chart_greater)
        st.write('Outbound')
        st.altair_chart(donut_chart_less)

with col[1]:
    st.markdown('#### Total Population')

    choropleth = make_choropleth(df_selected_year, 'id', 'population', selected_color_theme, kenya_geojson)
    st.plotly_chart(choropleth, use_container_width=True)

    heatmap = make_heatmap(df_reshaped, 'year', 'counties', 'population', selected_color_theme)
    st.altair_chart(heatmap, use_container_width=True)

with col[2]:
    st.markdown('#### Top Counties')

    st.dataframe(df_selected_year_sorted,
                 column_order=("counties", "population"),
                 hide_index=True,
                 width=None,
                 column_config={
                     "counties": st.column_config.TextColumn("Counties"),
                     "population": st.column_config.ProgressColumn("Population", format="%f", min_value=0,
                                                                   max_value=max(df_selected_year_sorted.population))}
                 )

    with st.expander('About', expanded=True):
        st.write('''
            - Data: [Kenyan National Bureau Of Statistics](https://www.knbs.or.ke/dataset.html).
            - :blue[**Gains/Losses**]: counties with high inbound/ outbound migration for selected year
            - :blue[**Counties Migration**]: percentage of counties with annual inbound/ outbound migration > 50,000
            ''')
