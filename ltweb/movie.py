from flask import Flask, render_template, request, g,redirect,session,url_for,flash, jsonify
import sqlite3
from datetime import datetime


app = Flask(__name__)
DATABASE = 'cinema.db'
app.secret_key = '1234'

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
@app.route('/<int:movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    db = get_db()
    cur = db.execute('SELECT * FROM movie WHERE IDmovie = ?', (movie_id,))
    cur2 = db.execute('SELECT DISTINCT showDate FROM Showtime WHERE IDmovie = ?', (movie_id,))
    cur3 = db.execute('SELECT * FROM comment JOIN Customer ON comment.customerID = customer.customerID WHERE IDmovie = ?',(movie_id,))
    comments = cur3.fetchall()
    showdates = cur2.fetchall()
    movie = cur.fetchone()
    showtimes = None
    dtb = 0 
    i= 0
    

        
    for comment in comments:
        dtb += comment['diem']
        i+=1
    if comments:
        dtb = round(dtb/i, 2)
    if movie is None:
        return "Movie not found", 404
    db.execute(
            'UPDATE movie SET score = ? , voted = ? WHERE IDmovie = ?',
            (dtb,i,movie_id)
        )
    db.commit()


    # Handle POST request to fetch showtimes
    if request.method == 'POST':
        show_date = request.form['showDate']
        cur3 = db.execute('SELECT showTime, showtimeID FROM Showtime WHERE IDmovie = ? AND showDate = ?', (movie_id, show_date,))
        showtimes = cur3.fetchall()

    return render_template('chitietphim.html', movie=movie, showdates=showdates, showtimes=showtimes,comments=comments,dtb=dtb)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'customerID' not in session:
        return jsonify({"success": False, "error": "User not logged in"}), 401

    data = request.json
    rating = int(data.get('rating'))
    comment = data.get('comment')
    movie_id = data.get('movieId')
    customer_id = session['customerID']  

    db = get_db()
    cur = db.execute(
        'SELECT * FROM comment WHERE customerID = ? AND IDmovie = ?',(customer_id, movie_id)
    )
    existing_review = cur.fetchone()

    if existing_review:
        db.execute(
            'UPDATE comment SET diem = ? , binhluan = ? WHERE customerID = ? and IDmovie = ?',
            (rating,comment, customer_id, movie_id)
        )
        db.commit()
    else:
        db.execute(
            'INSERT INTO comment (customerID, IDmovie, diem, binhluan) VALUES (?, ?, ?, ?)',
            (customer_id, movie_id, rating, comment)
        )
        db.commit()

    return jsonify({"success": True})


@app.route('/<int:movie_id>/<int:showtime_id>', methods=['GET', 'POST'])
def book_ticket(movie_id, showtime_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM SeatBooking WHERE showtimeID = ?", (showtime_id,))
    cur = db.execute('SELECT * FROM movie WHERE IDmovie = ?', (movie_id,))
    cur3 = db.execute('SELECT * FROM Showtime WHERE IDmovie = ? AND showtimeID = ?', (movie_id, showtime_id))
    showtime = cur3.fetchone()
    movie = cur.fetchone()

    seats = cursor.fetchall()
    return render_template('seatbooking.html', seats=seats, movie=movie, showtime=showtime)

@app.route('/book_seats', methods=['POST'])
def book_seats():
    db = get_db()
    cursor = db.cursor()

    selected_seats = request.json.get('selectedSeats')
    customer_id = session.get('customerID')
    
    # Insert tickets into Ticket table
    for seat_id in selected_seats:
        cursor.execute("INSERT INTO Ticket (ticketID, bookingID, customerID) VALUES (?, ?, ?)", 
                       (seat_id, seat_id, customer_id))

    db.commit()

    return jsonify({"success": True})

# Route hiển thị Login và Signup
@app.route('/login_page')
def login_page():
    return render_template('login.html')

# Route login
@app.route('/login', methods=['POST'])
def login_user():
    customerEmail = request.form['customerEmail']
    customerPassword = request.form['customerPassword']
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT customerName, customerID FROM Customer WHERE customerEmail = ? AND customerPassword = ?', 
                   (customerEmail, customerPassword))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['customerName'] = user['customerName']
        session['customerID'] = user['customerID']
        print(f"Logged in as: {session['customerName']}") 
        return redirect(url_for('homepage'))
    else:
        session['alert_message'] = 'Thông tin đăng nhập không chính xác, vui lòng nhập lại'
        return redirect(url_for('login_page', form='login'))


# Route signup
@app.route('/signup', methods=['POST'])
def signup_user():
    username = request.form['username']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Customer (customerName, customerEmail, phoneNumber, customerPassword) VALUES (?, ?, ?, ?)", 
                   (username, email, phone, password))
    conn.commit()
    conn.close()

    session['customerEmail'] = email 
    return redirect(url_for('homepage'))

# Route logout
@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('homepage')) 

# Route rap
@app.route('/rap')
def rap():
    return render_template('rap.html')

# Route my ticket
@app.route('/myticket')
def myticket():
    customer_id = session.get('customerID')
    
    if not customer_id:
        return redirect(url_for('login_page'))

    db = get_db()
    query = """
    SELECT 
        Ticket.ticketID, 
        SeatBooking.seatID,
        Showtime.showDate,
        Showtime.showTime,
        Movie.movieName,
        Movie.poster,
        SeatBooking.status
    FROM Ticket
    JOIN SeatBooking ON Ticket.bookingID = SeatBooking.bookingID
    JOIN Showtime ON SeatBooking.showtimeID = Showtime.showtimeID
    JOIN Movie ON Showtime.IDmovie = Movie.IDmovie
    WHERE Ticket.customerID = ?
    """
    tickets = db.execute(query, (customer_id,)).fetchall()

    formatted_tickets = []
    for ticket in tickets:
        show_time = datetime.strptime(ticket['showTime'], '%H:%M')
        ticket_info = {
            'ticketID': ticket['ticketID'],
            'seatID': ticket['seatID'],
            'showDate': ticket['showDate'],
            'showTime': ticket['showTime'],
            'movieName': ticket['movieName'],
            'poster': ticket['poster'],
            'status': 'Paid' if ticket['status'] == "1" else 'Unpaid',
            'price': '75,000 VND' if show_time.hour >= 22 else '100,000 VND'
        }
        formatted_tickets.append(ticket_info)

    return render_template('myticket.html', tickets=formatted_tickets)

# Route to confirm payment
@app.route('/confirm_payment/<int:ticket_id>', methods=['POST'])
def confirm_payment(ticket_id):
    db = get_db()
    db.execute("""
        UPDATE SeatBooking 
        SET status = 1 
        WHERE bookingID = (SELECT bookingID FROM Ticket WHERE ticketID = ?)
    """, (ticket_id,))
    db.commit()
    print(f"Ticket with ID {ticket_id} has been marked as paid.")
    return {"success": True}

# Route xóa vé
@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
def delete_ticket(ticket_id):
    db = get_db()
    ticket_status = db.execute("""
        SELECT status FROM SeatBooking
        WHERE bookingID = (SELECT bookingID FROM Ticket WHERE ticketID = ?)
    """, (ticket_id,)).fetchone()
    
    if ticket_status and ticket_status['status'] == "0":
        db.execute("""
            UPDATE SeatBooking 
            SET status = 0 -- Hoặc giá trị khác để thể hiện vé bị hủy
            WHERE bookingID = (SELECT bookingID FROM Ticket WHERE ticketID = ?)
        """, (ticket_id,))

        db.execute("DELETE FROM Ticket WHERE ticketID = ?", (ticket_id,))
        db.commit()
        return {"success": True}
    else:
        # Nếu vé đã thanh toán hoặc không tồn tại
        return {"success": False, "message": "Ticket already paid, cannot delete."}
    
@app.route('/bxh', methods=['GET'])
def bxhpage():
    sort_type = request.args.get('sort')
    db = get_db()

    if sort_type == 'rating':
        cur = db.execute('SELECT * FROM movie ORDER BY score DESC')
    elif sort_type == 'ratings_count':
        cur = db.execute('SELECT * FROM movie ORDER BY voted DESC')
    else:
        cur = db.execute('SELECT * FROM movie ORDER BY score DESC')

    movies = cur.fetchall()
    return render_template('bxh.html', movies=movies)


if __name__ == '__main__':
    app.run(debug=True)

