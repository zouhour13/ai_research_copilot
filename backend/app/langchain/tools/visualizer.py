import os
import uuid
import pandas as pd
import plotly.express as px
from langchain_core.tools import tool

STATIC_DIR = os.path.join(os.getcwd(), "static", "charts")
os.makedirs(STATIC_DIR, exist_ok=True)

@tool
def generate_chart_from_data(file_path: str, x_column: str, y_column: str, chart_type: str = "bar", title: str = "Data Visualization") -> str:
    """
    Generates a Plotly chart from a CSV or Excel file.
    Args:
        file_path: The absolute path to the uploaded data file (CSV/XLSX).
        x_column: The column name to use for the X-axis (or 'names' for pie charts).
        y_column: The column name to use for the Y-axis (or 'values' for pie charts).
        chart_type: The type of chart to generate ('bar', 'line', 'scatter', 'pie').
        title: The title of the chart.
    Returns:
        A markdown link to view the generated interactive chart, or an error message.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return "Error: Unsupported file format. Only CSV and Excel are supported."
            
        if x_column not in df.columns or y_column not in df.columns:
            return f"Error: Columns '{x_column}' or '{y_column}' not found in the dataset. Available columns: {', '.join(df.columns.tolist())}"

        if chart_type == "bar":
            fig = px.bar(df, x=x_column, y=y_column, title=title)
        elif chart_type == "line":
            fig = px.line(df, x=x_column, y=y_column, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_column, y=y_column, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_column, values=y_column, title=title)
        else:
            return f"Error: Unsupported chart type '{chart_type}'."
            
        chart_id = str(uuid.uuid4())[:8]
        filename = f"chart_{chart_id}.html"
        output_path = os.path.join(STATIC_DIR, filename)
        
        fig.write_html(output_path)
        
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        return f"Chart generated successfully! [View Interactive Chart]({api_url}/static/charts/{filename})"
    except Exception as e:
        return f"Error generating chart: {str(e)}"
