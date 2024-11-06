from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)
DATABASE = 'cinema.db'

# Kết nối SQLite
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # Để truy cập cột theo tên
    return db

# Đóng kết nối khi ứng dụng kết thúc
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Hàm lấy danh sách phim
def get_movies(page=1, per_page=10):
    db = get_db()
    cursor = db.cursor()
    
    # Tính toán vị trí bắt đầu (offset) cho phân trang
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT * FROM movie LIMIT ? OFFSET ?", (per_page, offset))
    movies = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM movie")
    total_movies = cursor.fetchone()[0]
    
    return movies, total_movies

# Hàm lấy thông tin chi tiết của bộ phim
def get_movie_details(movie_id):
    db = get_db()
    cur = db.execute('SELECT * FROM movie WHERE IDmovie = ?', (movie_id,))
    movie = cur.fetchone()
    return movie

# Route trang chủ
@app.route('/')
def homepage():
    page = request.args.get('page', 1, type=int)  # Lấy trang từ query string
    movies, total_movies = get_movies(page)
    
    total_pages = (total_movies + 9) // 10  # Tính số trang cần thiết
    
    return render_template('homepage.html', movies=movies, page=page, total_pages=total_pages)

# Route chi tiết phim
@app.route('/<int:movie_id>')
def movie_detail(movie_id):
    movie = get_movie_details(movie_id)
    if movie is None:
        return "Movie not found", 404
    return render_template('chitietphim.html', movie=movie)

if __name__ == '__main__':
    app.run(debug=True)

