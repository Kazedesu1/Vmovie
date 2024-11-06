from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Kết nối SQLite
def get_db_connection():
    conn = sqlite3.connect(r'C:\Users\PC\Downloads\CODE\Python\ltw\db\cinema.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_movies(page=1, per_page=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tính toán vị trí bắt đầu (offset) cho phân trang
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT poster, movieName, genre, time, rated FROM movie LIMIT ? OFFSET ?", (per_page, offset))
    movies = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM movie")
    total_movies = cursor.fetchone()[0]
    
    conn.close()
    
    return movies, total_movies

@app.route('/')
def homepage():
    page = request.args.get('page', 1, type=int)  # Lấy trang từ query string
    movies, total_movies = get_movies(page)
    
    total_pages = (total_movies + 9) // 10  # Tính số trang cần thiết
    
    return render_template('homepage.html', movies=movies, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
