from flask import Flask, render_template, g
import sqlite3

app = Flask(__name__)
DATABASE = 'cinema.db'

# Hàm kết nối đến database SQLite
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

# Hàm lấy thông tin chi tiết của bộ phim
def get_movie_details(movie_id):
    db = get_db()
    cur = db.execute('SELECT * FROM movie WHERE IDmovie = ?', (movie_id,))
    movie = cur.fetchone()
    return movie

# Route chi tiết phim
@app.route('/<int:movie_id>')
def movie_detail(movie_id):
    movie = get_movie_details(movie_id)
    if movie is None:
        return "Movie not found", 404
    return render_template('chitietphim.html', movie=movie)

if __name__ == '__main__':
    app.run(debug=True)
