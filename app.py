import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Set up the page
st.set_page_config(layout="wide")
st.title("Анализ отзывов на продукты и категории")

# Load the data functions from your notebook
def load_db(db_file):
    with sqlite3.connect(db_file) as conn:
        tables = list(pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)['name'])
        db = {table: pd.read_sql_query(f"SELECT * from {table}", conn) for table in tables}
    return db

# Load the data
db_reviews = load_db("reviews.db")
reviews = db_reviews['reviews'].copy()
categs = db_reviews['categs'].copy()
goods = db_reviews['goods'].copy()

# Tab layout
tab1, tab2, tab3 = st.tabs(["Анализ продуктов", "Анализ категорий", "Общая статистика"])

with tab1:
    st.header("Анализ изменения рейтингов продуктов")
    
    # Query for product rating changes
    with sqlite3.connect('reviews.db') as conn:
        query = """
        WITH avg_rating_window as (
            SELECT
                GoodDesc,
                Date,
                AVG(Rating) OVER (PARTITION BY GoodNum ORDER BY Date) as Avg,
                FIRST_VALUE(AVG(Rating)) OVER (PARTITION BY GoodDesc ORDER BY Date) as first_avg,
                LAST_VALUE(AVG(Rating)) OVER (PARTITION BY GoodDesc ORDER BY Date) as last_avg
            FROM reviews AS r
                JOIN goods AS g USING(GoodNum)
            GROUP BY GoodDesc, Date
        )

        SELECT
            GoodDesc as Product,
            MAX(Avg) - MIN(Avg) as RatingRange,
            MAX(Avg)/MIN(Avg) as RatingRatio,
            last_avg - first_avg as RatingChange,
            last_avg/first_avg as RatingChangeRatio
        FROM avg_rating_window
        GROUP BY GoodDesc
        ORDER BY RatingChange DESC
        """
        product_rating_changes = pd.read_sql(query, conn)
    
    # Display top and bottom products by rating change
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ-5 продуктов с ростом рейтинга")
        top_products = product_rating_changes.head(5)
        st.dataframe(top_products)
        
        fig = px.bar(top_products, 
                     x='Product', 
                     y='RatingChange',
                     title='Продукты с наибольшим ростом рейтинга')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Топ-5 продуктов с падением рейтинга")
        bottom_products = product_rating_changes.tail(5).sort_values('RatingChange')
        st.dataframe(bottom_products)
        
        fig = px.bar(bottom_products, 
                     x='Product', 
                     y='RatingChange',
                     title='Продукты с наибольшим падением рейтинга')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Анализ изменения рейтингов категорий")
    
    # Query for category rating changes
    with sqlite3.connect('reviews.db') as conn:
        query = """
        WITH avg_rating_window as (
            SELECT
                ProductCatDesc,
                Date,
                AVG(Rating) OVER (PARTITION BY ProductCatDesc ORDER BY Date) as Avg,
                FIRST_VALUE(AVG(Rating)) OVER (PARTITION BY ProductCatDesc ORDER BY Date) as first_avg,
                LAST_VALUE(AVG(Rating)) OVER (PARTITION BY ProductCatDesc ORDER BY Date) as last_avg
            FROM reviews AS r
                JOIN goods AS g USING(GoodNum)
                    JOIN categs AS c USING(ProductCatNum)
            GROUP BY ProductCatDesc, Date
        )

        SELECT
            ProductCatDesc as Category,
            MAX(Avg) - MIN(Avg) as RatingRange,
            MAX(Avg)/MIN(Avg) as RatingRatio,
            last_avg - first_avg as RatingChange,
            last_avg/first_avg as RatingChangeRatio
        FROM avg_rating_window
        GROUP BY ProductCatDesc
        ORDER BY RatingChange DESC
        """
        category_rating_changes = pd.read_sql(query, conn)
    
    # Display top and bottom categories by rating change
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Топ-3 категории с ростом рейтинга")
        top_categories = category_rating_changes.head(3)
        st.dataframe(top_categories)
        
        fig = px.bar(top_categories, 
                     x='Category', 
                     y='RatingChange',
                     title='Категории с наибольшим ростом рейтинга')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Топ-3 категории с падением рейтинга")
        bottom_categories = category_rating_changes.tail(3).sort_values('RatingChange')
        st.dataframe(bottom_categories)
        
        fig = px.bar(bottom_categories, 
                     x='Category', 
                     y='RatingChange',
                     title='Категории с наибольшим падением рейтинга')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Общая статистика отзывов")
    
    # Basic statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Распределение оценок")
        rating_dist = reviews['Rating'].value_counts().sort_index()
        fig = px.pie(rating_dist, 
                     names=rating_dist.index, 
                     values=rating_dist.values,
                     title='Распределение оценок')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Средний рейтинг по месяцам")
        reviews['Date'] = pd.to_datetime(reviews['Date'])
        monthly_avg = reviews.groupby(pd.Grouper(key='Date', freq='M'))['Rating'].mean().reset_index()
        fig = px.line(monthly_avg, 
                      x='Date', 
                      y='Rating',
                      title='Средний рейтинг по месяцам')
        st.plotly_chart(fig, use_container_width=True)
    
    # Products with highest/lowest average ratings
    st.subheader("Продукты с самыми высокими и низкими рейтингами")
    products_avg_rating = (
        reviews
        .merge(goods)
        .groupby('GoodDesc', as_index=False)
        .agg(AvgRating=('Rating', 'mean'))
    )
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Топ-5 продуктов по рейтингу")
        top_rated = products_avg_rating.sort_values('AvgRating', ascending=False).head(5)
        st.dataframe(top_rated)
    
    with col2:
        st.write("5 продуктов с самым низким рейтингом")
        bottom_rated = products_avg_rating.sort_values('AvgRating').head(5)
        st.dataframe(bottom_rated)
