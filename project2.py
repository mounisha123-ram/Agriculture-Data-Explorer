
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import pymysql
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from plotly.subplots import make_subplots

# Database Connection Settings
HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
PORT = 4000
USER = "jynBzNA54kSWeXs.root"
PASSWORD = "iLlH6q8wVdsYWZQ9"
DATABASE = "project2"
SSL_CERT = r"C:\Users\LENOVO\Desktop\DataScience\streamlit\env\CA cert from Tibd cloud.pem"

# Create SQLAlchemy Engine
try:
    engine = create_engine(
        f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?ssl_ca={SSL_CERT}",
        connect_args={'ssl': {'ca': SSL_CERT}}  # Explicitly pass SSL context
    )
except Exception as e:
    st.error(f"Error connecting to the database: {e}")
    # It's crucial to stop execution here if the database connection fails.
    st.stop()

# Function to Fetch Data
def get_data(query):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error executing query: {query}. Error: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error to avoid crashing


# --- Streamlit App Configuration ---
st.set_page_config(page_title="Agriculture Data Dashboard", layout="wide")

# --- Set Background Image using Inline CSS ---
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# *** IMPORTANT: Replace 'YOUR_IMAGE_URL' with the actual path or URL of your image ***
image_url = "https://images.unsplash.com/photo-1501618265512-2b19150656b7?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"  # Example URL, replace this!
set_background(image_url)

# Streamlit App
st.set_page_config(page_title="Agriculture Data Dashboard", layout="wide")
st.title("🌾 Agriculture Data Analysis Dashboard")

# Sidebar Menu
option = st.sidebar.radio("Select Category", ["Home", "SQL Insights", "EDA Charts", "About"])

# --- HOME PAGE ---
if option == "Home":
    st.markdown("Welcome to the Agriculture Data Dashboard! Use the sidebar to explore SQL insights and visual analysis.")

# --- SQL INSIGHTS PAGE ---
elif option == "SQL Insights":
    st.header("📌 SQL-Based Insights")
    sql_queries_with_plots = {
        "1. Year-wise Trend of Rice Production Across Top 3 States": {
            "query": """
                SELECT year, state_name, total_rice_production
                FROM (
                    SELECT
                        year,
                        state_name,
                        SUM(rice_production) AS total_rice_production,
                        RANK() OVER (PARTITION BY year ORDER BY SUM(rice_production) DESC) AS rank_in_year
                    FROM agri
                    GROUP BY year, state_name
                ) AS ranked
                WHERE rank_in_year <= 3
                ORDER BY year, rank_in_year
            """,
            "plot_type": "line",
            "x": "year",
            "y": "total_rice_production",
            "color": "state_name",
            "labels": {"year": "Year", "total_rice_production": "Total Rice Production", "state_name": "State"},
            "title": "Year-wise Trend of Rice Production Across Top 3 States"
        },
        "2. Top 5 Districts by Wheat Yield Increase Over the Last 5 Years": {
            "query": """
                SELECT
                    dist_code,
                    dist_name,
                    MAX(CASE WHEN year = (SELECT MAX(year) FROM agri) THEN wheat_yield END) AS latest_year_wheat_yield,
                    MAX(CASE WHEN year = (SELECT MAX(year) FROM agri) - 5 THEN wheat_yield END) AS past_year_wheat_yield,
                    (MAX(CASE WHEN year = (SELECT MAX(year) FROM agri) THEN wheat_yield END) -
                     MAX(CASE WHEN year = (SELECT MAX(year) FROM agri) - 5 THEN wheat_yield END)
                    ) AS wheat_yield_increase,
                    (SELECT MAX(year) FROM agri) AS latest_year,
                    (SELECT MAX(year) FROM agri) - 5 AS past_year
                FROM agri
                WHERE
                    year IN ((SELECT MAX(year) FROM agri), (SELECT MAX(year) FROM agri) - 5)
                GROUP BY
                    dist_code, dist_name
                HAVING
                    COUNT(DISTINCT year) = 2  -- District should have data for both years
                ORDER BY
                    wheat_yield_increase DESC
                LIMIT 5
            """,
            "plot_type": "bar",
            "x": "dist_name",
            "y": "wheat_yield_increase",
            "labels": {"dist_name": "District", "wheat_yield_increase": "Wheat Yield Increase"},
            "title": "Top 5 Districts by Wheat Yield Increase (Last 5 Years)"
        },
        "3. States with the Highest Growth in Oilseed Production (5-Year Growth Rate)": {
            "query": """
                SELECT
                    state_name,
                    SUM(CASE WHEN year = (SELECT MAX(year) FROM agri) THEN oilseeds_production END) AS latest_production,
                    SUM(CASE WHEN year = (SELECT MAX(year) FROM agri) - 5 THEN oilseeds_production END) AS past_production,
                    ROUND(
                        (SUM(CASE WHEN year = (SELECT MAX(year) FROM agri) THEN oilseeds_production END) -
                         SUM(CASE WHEN year = (SELECT MAX(year) FROM agri) - 5 THEN oilseeds_production END)) * 100.0 /
                        NULLIF(SUM(CASE WHEN year = (SELECT MAX(year) FROM agri) - 5 THEN oilseeds_production END), 0),
                    2) AS growth_rate_percentage
                FROM agri
                WHERE
                    year IN ((SELECT MAX(year) FROM agri), (SELECT MAX(year) FROM agri) - 5)
                GROUP BY state_name
                HAVING COUNT(DISTINCT year) = 2
                ORDER BY growth_rate_percentage DESC
                LIMIT 10
            """,
            "plot_type": "bar",
            "x": "state_name",
            "y": "growth_rate_percentage",
            "labels": {"state_name": "State", "growth_rate_percentage": "Growth Rate (%)"},
            "title": "States with Highest Oilseed Production Growth (Last 5 Years)"
        },
        "4. District-wise Correlation Between Area and Production for Major Crops (Rice, Wheat, and Maize)": {
            "query": """
                SELECT
                    dist_code,
                    dist_name,
                    AVG(rice_area) AS avg_rice_area,
                    AVG(rice_production) AS avg_rice_production,
                    AVG(wheat_area) AS avg_wheat_area,
                    AVG(wheat_production) AS avg_wheat_production,
                    AVG(maize_area) AS avg_maize_area,
                    AVG(maize_production) AS avg_maize_production
                FROM agri
                GROUP BY dist_code, dist_name
                ORDER BY dist_code
                LIMIT 10
            """,
            "plot_type": "scatter",
            "x": "avg_rice_area",
            "y": "avg_rice_production",
            "color": "dist_name",
            "labels": {"avg_rice_area": "Avg Rice Area", "avg_rice_production": "Avg Rice Production", "dist_name": "District"},
            "title": "District-wise Correlation: Rice Area vs Production"
        },
        "5. Yearly Production Growth of Cotton in Top 5 Cotton Producing States": {
            "query": """
                SELECT
                    year,
                    state_name,
                    SUM(cotton_production) AS total_cotton_production,
                    state_name AS states
                FROM agri
                GROUP BY year, state_name
                ORDER BY total_cotton_production DESC
                LIMIT 5
            """,
            "plot_type": "line",
            "x": "year",
            "y": "total_cotton_production",
            "color": "states",
            "labels": {"year": "Year", "total_cotton_production": "Total Cotton Production", "states": "State"},
            "title": "Yearly Cotton Production in Top 5 States"
        },
        "6. Districts with the Highest Groundnut Production in 1996": {
            "query": """
                SELECT
                    dist_name AS districts,
                    SUM(groundnut_production) AS highest_groundnut_production
                FROM agri
                WHERE year = 1996
                GROUP BY dist_name
                ORDER BY highest_groundnut_production DESC
                LIMIT 10
            """,
            "plot_type": "bar",
            "x": "districts",
            "y": "highest_groundnut_production",
            "labels": {"districts": "District", "highest_groundnut_production": "Total Groundnut Production"},
            "title": "Districts with Highest Groundnut Production in 1996"
        },
        "7. Annual Average Maize Yield Across All States": {
            "query": """
                SELECT year,AVG(maize_yield) AS avg_maize_yield
                FROM agri
                GROUP BY year
                ORDER BY year
                DESC LIMIT 10
            """,
            "plot_type": "line",
            "x": "year",
            "y": "avg_maize_yield",
            "labels": {"year": "Year", "avg_maize_yield": "Average Maize Yield"},
            "title": "Annual Average Maize Yield Across All States"
        },
        "8. Total Area Cultivated for Oilseeds in Each State": {
            "query": """
                SELECT
                    state_name,
                    SUM(oilseeds_area) AS total_oilseeds_area
                FROM agri
                GROUP BY state_name
                ORDER BY total_oilseeds_area
                DESC LIMIT 10
            """,
            "plot_type": "bar",
            "x": "state_name",
            "y": "total_oilseeds_area",
            "labels": {"state_name": "State", "total_oilseeds_area": "Total Oilseeds Area"},
            "title": "Total Area Cultivated for Oilseeds in Each State"
        },
        "9. Districts with the Highest Rice Yield": {
            "query": """
                SELECT
                    dist_name,
                    SUM(rice_yield) AS Highest_Rice_Yield
                FROM agri
                GROUP BY dist_name
                ORDER BY Highest_Rice_Yield DESC
                LIMIT 10
            """,
            "plot_type": "bar",
            "x": "dist_name",
            "y": "Highest_Rice_Yield",
            "labels": {"dist_name": "District", "Highest_Rice_Yield": "Total Rice Yield"},
            "title": "Districts with the Highest Rice Yield"
        },
        "10. Compare the Production of Wheat and Rice for the Top 5 States Over 10 Years": {
            "query": """
                SELECT
                    year,
                    state_name,
                    SUM(wheat_production) AS total_wheat_production,
                    SUM(rice_production) AS total_rice_production
                FROM
                    agri
                WHERE
                    state_name IN (SELECT state_name FROM agri GROUP BY state_name ORDER BY SUM(rice_production) DESC LIMIT 5)
                GROUP BY
                    year, state_name
                ORDER BY
                    year, state_name;
            """,
            "plot_type": "line",
            "x": "year",
            "y": ["total_wheat_production", "total_rice_production"],
            "color": "state_name",
            "labels": {"year": "Year", "total_wheat_production": "Total Wheat Production", "total_rice_production": "Total Rice Production", "state_name": "State"},
            "title": "Comparison of Wheat and Rice Production (Top 5 States Over Years)"
        }
    }

    selected_query_sql = st.selectbox("Choose a SQL query:", list(sql_queries_with_plots.keys()))
    if st.button("Run SQL Query"):
        query_info = sql_queries_with_plots[selected_query_sql]
        df_sql = get_data(query_info["query"])
        if df_sql is not None and not df_sql.empty: # Check if the df_sql is valid
            st.dataframe(df_sql)
            if "plot_type" in query_info:
                try:
                    if query_info["plot_type"] == "line":
                        fig = px.line(df_sql, x=query_info["x"], y=query_info["y"], color=query_info.get("color"), labels=query_info["labels"], title=query_info["title"])
                        st.plotly_chart(fig, use_container_width=True)
                    elif query_info["plot_type"] == "bar":
                        fig = px.bar(df_sql, x=query_info["x"], y=query_info["y"], color=query_info.get("color"), labels=query_info["labels"], title=query_info["title"])
                        st.plotly_chart(fig, use_container_width=True)
                    elif query_info["plot_type"] == "scatter":
                        fig = px.scatter(df_sql, x=query_info["x"], y=query_info["y"], color=query_info.get("color"), labels=query_info["labels"], title=query_info["title"])
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating plot: {e}")
        else:
            st.warning("No data returned from the query.")

# --- EDA CHARTS PAGE ---
elif option == "EDA Charts":
    st.header("📈 EDA Visualizations")
    df_eda = get_data("SELECT state_name, year, rice_production, wheat_production, oilseeds_production, sunflower_production, sugarcane_production, pearl_millet_production, finger_millet_production, kharif_sorghum_production, rabi_sorghum_production, groundnut_production, soyabean_production, soyabean_area, oilseeds_area, rice_area, wheat_area, maize_area, maize_production, rice_yield, wheat_yield, dist_name FROM agri") # Ensuring dist_name and maize_production are fetched
    if df_eda is None or df_eda.empty:
        st.warning("No data available for EDA charts.")
        st.stop()

    eda_plots = {
        "1. Top 7 Rice Producing States (Bar Plot)": {
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name')['rice_production'].sum().nlargest(7).reset_index(),
            "x": "state_name",
            "y": "rice_production",
            "color": "state_name",
            "labels": {"state_name": "State", "rice_production": "Total Rice Production"},
            "title": "Top 7 Rice Producing States"
        },
        "2. Top 5 Wheat Producing States (Bar Chart)": {
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name')['wheat_production'].sum().nlargest(5).reset_index(),
            "x": "state_name",
            "y": "wheat_production",
            "color": "wheat_production",
            "labels": {"state_name": "State", "wheat_production": "Total Wheat Production"},
            "title": "Top 5 Wheat Producing States"
        },
        "3. Top 5 Oilseed Producing States (Bar Plot)": {
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name')['oilseeds_production'].sum().nlargest(5).reset_index(),
            "x": "state_name",
            "y": "oilseeds_production",
            "color": "oilseeds_production",
            "labels": {"state_name": "State", "oilseeds_production": "Total Oilseed Production"},
            "title": "Top 5 Oilseed Producing States"
        },
        "4. Top 7 Sunflower Producing States (Bar Plot)": {
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name')['sunflower_production'].sum().nlargest(7).reset_index(),
            "x": "state_name",
            "y": "sunflower_production",
            "color": "sunflower_production",
            "labels": {"state_name": "State", "sunflower_production": "Total Sunflower Production"},
            "title": "Top 7 Sunflower Producing States"
        },
        "5. India's Sugarcane Production Over Years (Line Plot)": {
            "plot_function": px.line,
            "data": df_eda.groupby('year')['sugarcane_production'].sum().reset_index(),
            "x": "year",
            "y": "sugarcane_production",
            "labels": {"year": "Year", "sugarcane_production": "Total Sugarcane Production"},
            "title": "India's Sugarcane Production Over Years"
        },
        "6. Rice Production vs. Wheat Production Over Years (Line Plot)": {
            "plot_function": px.line,
            "data": df_eda.groupby('year')[['rice_production', 'wheat_production']].sum().reset_index(),
            "x": "year",
            "y": ["rice_production", "wheat_production"],
            "labels": {"year": "Year", "rice_production": "Total Rice Production", "wheat_production": "Total Wheat Production"},
            "title": "Rice Production vs. Wheat Production Over Years"
        },
        "7. Rice Production By West Bengal Districts (Bar Plot)": {
            "plot_function": px.bar,
            "data": df_eda[df_eda['state_name'] == 'West Bengal'].groupby('dist_name')['rice_production'].sum().reset_index(),
            "x": "dist_name",
            "y": "rice_production",
            "labels": {"dist_name": "District", "rice_production": "Total Rice Production"},
            "title": "Rice Production by District in West Bengal"
        },
        "8. Top 10 Wheat Production Years From 1990 (Bar Plot)": {
            "plot_function": px.bar,
            "data": df_eda[df_eda['year'] >= 1990].groupby('year')['wheat_production'].sum().nlargest(10).reset_index(),
            "x": "year",
            "y": "wheat_production",
            "labels": {"year": "Year", "wheat_production": "Total Wheat Production"},
            "title": "Top 10 Wheat Production Years (From 1990 Onward)"
        },
        "9. Millet Production (Last 50y)":{
            "plot_function": px.line,
            "data": df_eda.groupby('year')[['pearl_millet_production', 'finger_millet_production']].sum().reset_index(),
            "x": "year",
            "y": ['pearl_millet_production', 'finger_millet_production'],
            "labels": {"year": "Year", "pearl_millet_production": "Pearl Millet Production", "finger_millet_production":"Finger Millet Production"},
            "title": "Millet Production (Last 50 Years)"
        },
        "10. Sorghum Production (Kharif and Rabi) by Region":{
            "plot_function": px.line,
            "data": df_eda.groupby('year')[['kharif_sorghum_production', 'rabi_sorghum_production']].sum().reset_index(),
            "x": "year",
            "y": ['kharif_sorghum_production', 'rabi_sorghum_production'],
            "labels": {"year": "Year", "kharif_sorghum_production": "Kharif Sorghum Production", "rabi_sorghum_production":"Rabi Sorghum Production"},
            "title": "Sorghum Production (Kharif and Rabi) by Region"
        },
        "11. Top 7 States for Groundnut Production": {
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name')['groundnut_production'].sum().nlargest(7).reset_index(),
            "x": "state_name",
            "y": "groundnut_production",
            "color": "state_name",
            "labels": {"state_name": "State", "groundnut_production": "Total Groundnut Production"},
            "title": "Top 7 States for Groundnut Production"
        },
        "12. Soybean Production by Top 5 States and Yield Efficiency":{
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name').agg(
                soyabean_production = ('soyabean_production','sum'),
                soyabean_area = ('soyabean_area','sum')
            ).reset_index().assign(soyabean_yield = lambda x: x['soyabean_production'] / x['soyabean_area']).sort_values(by='soyabean_production',ascending = False).head(5),
            "x": "state_name",
            "y": ['soyabean_production','soyabean_yield'],
            "labels": {"state_name": "State", "soyabean_production": "Total Soyabean Production", "soyabean_yield":"Soyabean Yield"},
            "title": "Soybean Production by Top 5 States and Yield Efficiency"
        },
        "13. Oilseed Production in Major States":{
            "plot_function": px.bar,
            "data": df_eda.groupby('state_name').agg(
                oilseeds_production = ('oilseeds_production','sum'),
                oilseeds_area = ('oilseeds_area','sum')
            ).reset_index().assign(oilseeds_yield = lambda x: x['oilseeds_production'] / x['oilseeds_area']).sort_values(by='oilseeds_production',ascending = False).head(7),
            "x": "state_name",
            "y": ['oilseeds_production','oilseeds_yield'],
            "labels": {"state_name": "State", "oilseeds_production": "Total Oilseeds Production", "oilseeds_yield":"Oilseeds Yield"},
            "title": "Oilseed Production in Major States"
        },
        "14. Impact of Area Cultivated on Production (Rice, Wheat, Maize)": {
            "plot_function": "scatter_subplots",
            "data": df_eda,
            "x_vars": ['rice_area', 'wheat_area', 'maize_area'],
            "y_vars": ['rice_production', 'wheat_production', 'maize_production'],
            "titles": ['Rice: Area vs Production', 'Wheat: Area vs Production', 'Maize: Area vs Production'],
            "labels": {
                'rice_area': 'Rice Area (Ha)', 'rice_production': 'Rice Production (Tonnes)',
                'wheat_area': 'Wheat Area (Ha)', 'wheat_production': 'Wheat Production (Tonnes)',
                'maize_area': 'Maize Area (Ha)', 'maize_production': 'Maize Production (Tonnes)'
            }
        },
        "15. Rice vs. Wheat Yield Across States": {
            "plot_function": "bar_subplots",
            "data": df_eda.groupby('state_name')[['rice_yield', 'wheat_yield']].mean().reset_index(),
            "x": "state_name",
            "y_vars": ['rice_yield', 'wheat_yield'],
            "labels": {"state_name": "State", "rice_yield": "Rice Yield (Tonnes per Hectare)", "wheat_yield": "Wheat Yield (Tonnes per Hectare)"},
            "title": "Rice vs. Wheat Yield Across States"
        }
    }

    selected_eda_plot = st.selectbox("Choose an EDA plot:", list(eda_plots.keys()))

    if st.button("Get EDA"): # added the button here
        if selected_eda_plot:
            plot_info = eda_plots[selected_eda_plot]
            plot_data = plot_info["data"]

           
            try:
                if plot_info["plot_function"] == px.bar:
                    fig = px.bar(plot_data, x=plot_info["x"], y=plot_info["y"], color=plot_info.get("color"), labels=plot_info["labels"], title=plot_info["title"])
                    st.plotly_chart(fig, use_container_width=True)
                elif plot_info["plot_function"] == px.line:
                    fig = px.line(plot_data, x=plot_info["x"], y=plot_info["y"], markers=True, labels=plot_info["labels"], title=plot_info["title"])
                    st.plotly_chart(fig,use_container_width=True)
                elif plot_info["plot_function"] == px.histogram:
                    fig = px.histogram(plot_data, x=plot_info["x"], labels=plot_info["labels"], title=plot_info["title"])
                    st.plotly_chart(fig, use_container_width=True)
                elif plot_info["plot_function"] == px.scatter:
                    fig = px.scatter(plot_data, x=plot_info["x"], y=plot_info["y"], color=plot_info.get("color"), labels=plot_info["labels"], title=plot_info["title"])
                    st.plotly_chart(fig, use_container_width=True)
                elif plot_info["plot_function"] == "scatter_subplots":
                    fig = make_subplots(rows=1, cols=len(plot_info["x_vars"]), subplot_titles=plot_info["titles"])
                    for i, (x_var, y_var) in enumerate(zip(plot_info["x_vars"], plot_info["y_vars"]), start=1):
                        fig.add_trace(
                            px.scatter(plot_data, x=x_var, y=y_var, labels=plot_info["labels"]).data[0],
                            row=1, col=i
                        )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                elif plot_info["plot_function"] == "bar_subplots":
                    num_cols = len(plot_info["y_vars"])
                    fig = make_subplots(rows=1, cols=num_cols, subplot_titles=[plot_info["labels"][y_var] for y_var in plot_info["y_vars"]])
                    for i, y_var in enumerate(plot_info["y_vars"], start=1):
                        fig.add_trace(
                            px.bar(plot_data, x=plot_info["x"], y=y_var, labels=plot_info["labels"]).data[0],
                            row=1, col=i
                        )
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                elif plot_info["plot_function"] == "heatmap":
                    fig = px.imshow(plot_data,
                                    labels=dict(x=plot_info["x_label"], y=plot_info["y_label"], color="Value"),
                                    title=plot_info["title"])
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.error("Plot type not supported.")
            except Exception as e:
                st.error(f"Error creating plot: {e}")
        else:
            st.warning("Please select a plot to generate.")

# --- ABOUT PAGE ---
elif option == "About":
    st.header("ℹ️ About the Dashboard")
    st.markdown("This dashboard provides insights into agricultural data, including crop production and yield across various states and districts in India.  The data is sourced from a SQL database.  Use the navigation in the sidebar to explore different sections.")
    st.markdown("Key features include:")
    st.markdown("-   **SQL Insights**:  Predefined SQL queries and visualizations to answer specific agricultural questions.")
    st.markdown("-   **EDA Charts**:  Interactive exploratory data analysis visualizations to help you understand the data.")
    st.markdown("This project was created to help visualize and analyze agricultural data.")
