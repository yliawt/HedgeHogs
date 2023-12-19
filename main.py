from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, session
from flask_mysqldb import MySQL
from flask_socketio import SocketIO, join_room, leave_room, send
from datetime import datetime
from string import ascii_letters
import random
import io
import base64

app = Flask(__name__, static_folder='assets')
app.secret_key = "flash_message"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'math'
mysql = MySQL(app)
app.config['SECRET_KEY'] = 'SDKFJSDFOWEIOF'
socketio = SocketIO(app)

user_id = ""
user_rooms = {}

@app.route('/')
def index():
    return render_template('000main.html')


@app.route('/login_page')
def login_page():
    return render_template('login.html')


@app.route('/mainpage')
def mainpage():
    return render_template('1Index.html')


@app.route('/lecpage')
def lecpage():
    return render_template('1lecIndex.html')


@app.route('/materials')
def materials():
    return render_template('2lecPilihTopik.html')

@app.route('/lecChatBox')
def lecchatbox():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT id FROM profile")
    user_id=cur.fetchall()
    cur.close()
    return render_template("3lecChatBox.html", username=user_id)

@app.route('/selectedChatBox',methods=['POST','GET'])
def selectedChatBox():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT id FROM profile")
    std = cur.fetchall()
    user_id = session.get('username')
    username=request.args.get('username')
    cur=mysql.connection.cursor()
    cur.execute("SELECT roomcode FROM profile WHERE id = %s",(username,))
    roomcode_result = cur.fetchone()
    roomcode = roomcode_result[0]
    session['room']=roomcode
    user_room = user_rooms.get(user_id, None)
    if user_room is None:
        # Handle the case where the user's chat room does not exist
        return redirect(url_for('login'))  # Redirect to login page or show an error message

    cur.execute("SELECT sender, message, timestamp FROM chatbox WHERE roomcode = %s ORDER BY timestamp ASC", (roomcode,))
    messages = cur.fetchall()
    cur.close()
    username=str(username)
    return render_template('3lecChatBox.html',room=roomcode, username=std, user=user_id, messages=messages)

@app.route('/chatbox')
def chatbox():
    user_id = session.get('username')
    # Retrieve the user's chat room from the user_rooms dictionary
    user_room = user_rooms.get(user_id, None)
    if user_room is None:
        # Handle the case where the user's chat room does not exist
        return redirect(url_for('login'))  # Redirect to login page or show an error message
    cur = mysql.connection.cursor()
    cur.execute("SELECT roomcode FROM profile WHERE id = %s", (user_id,))
    roomcode_result = cur.fetchone()
    roomcode = roomcode_result[0]
    session['room'] = roomcode

    cur = mysql.connection.cursor()
    cur.execute("SELECT sender, message, timestamp FROM chatbox WHERE roomcode = %s ORDER BY timestamp ASC", (roomcode,))
    messages = cur.fetchall()
    cur.close()

    return render_template('3ChatBox.html', room=roomcode, user=user_id, messages=messages)

@socketio.on('connect')
def handle_connect():
    room = session.get('roomcode')
    join_room(room)

@socketio.on('message')
def handle_message(payload):
    room = session.get('room')
    name = session.get('username')
    message_text = payload["message"]
    current_time = datetime.now()
    message = {
        "sender": name,
        "message": message_text
    }
    send(message, to=room)
    user_rooms[room]["messages"].append(message)
    custom_formatted_time = current_time.strftime('%d/%m/%Y, %I:%M:%S %p')

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO chatbox (roomcode, sender, message, timestamp) VALUES (%s, %s, %s, %s)",
        (room, name, message_text, custom_formatted_time)
    )
    mysql.connection.commit()
    cur.close()

@socketio.on('disconnect')
def handle_disconnect():
    room = session.get("room")
    leave_room(room)

@app.route('/profile')
def profile():
    user_id=session.get("username")
    print(user_id)
    cur=mysql.connection.cursor()
    cur.execute("SELECT name, birth, gender, phone, email, school, alamat1, alamat2, poskod, negeri, huraian FROM profile WHERE id=%s", (user_id,))
    info= cur.fetchone()
    return render_template('4profile.html', info=info)


@app.route('/about_us')
def about_us():
    return render_template('5AboutUs.html')


@app.route('/logout')
def logout():
    return render_template('000main.html')


@app.route('/stdmaterial')
def stdmaterial():
    return render_template('2pilihTopik.html')


@app.route('/perpuluhan')
def perpuluhan():
    return render_template('Perpuluhan_pilihAktiviti.html')


@app.route('/perpuluhan/nota')
def perpuluhan_nota():
    return render_template('Perpuluhan_pilihNota.html')


@app.route('/perpuluhan/nota_minda')
def perpuluhan_nota_minda():
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)
    return render_template('Perpuluhan_nota_peta.html', encoded_images=encoded_images)


@app.route('/perpuluhan/nota_kata')
def perpuluhan_nota_kata():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_nota_kata.html', materials=materials)


@app.route('/perpuluhan/nota_video')
def perpuluhan_nota_video():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('Perpuluhan_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence)


@app.route('/serve_video/<filename>')
def serve_video(filename):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE filename = %s", (filename,))
    video_content = cur.fetchone()[0]

    response = make_response(video_content)
    response.headers['Content-Type'] = 'video/mp4'  # Adjust the content type as needed

    return response


@app.route('/perpuluhan/nota_pdf')
def perpuluhan_nota_pdf():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_nota_pdf.html', materials=materials)


@app.route('/serve_pdf/<filename>')
def serve_pdf(filename):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE filename = %s", (filename,))
    pdf_data = cur.fetchone()

    if pdf_data:
        response = make_response(pdf_data[0])
        response.headers['Content-Type'] = 'application/pdf'
        return response
    else:
        return "PDF not found", 404


@app.route('/perpuluhan/latihan')
def perpuluhan_latihan():
    return render_template('Perpuluhan_latihan_pilihJenis.html')


@app.route('/perpuluhan/latihan_link')
def perpuluhan_latihan_link():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Perpuluhan' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_latihan_link.html', materials=materials)


@app.route('/serve_latihan/<filename>')
def serve_latihan(filename):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE filename = %s", (filename,))
    pdf_data = cur.fetchone()

    if pdf_data:
        response = make_response(pdf_data[0])
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename={filename}'  # Specify the filename
        return response
    else:
        return "PDF not found", 404


@app.route('/perpuluhan/latihan_game')
def perpuluhan_latihan_game():
    cur = mysql.connection.cursor()
    cur.execute("SELECT words, soalan, hint FROM materials WHERE topic='Perpuluhan' AND category='Permainan'")
    game = cur.fetchall()
    return render_template('Perpuluhan_latihan_game.html',game=game)


@app.route('/perpuluhan/kuiz')
def perpuluhan_kuiz():
    cur = mysql.connection.cursor()
    cur.execute("SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'perpuluhan'")
    quiz = cur.fetchall()
    return render_template('Perpuluhan_kuiz.html', quiz=quiz)


@app.route('/tingakatan3')
def tingkatan3():
    return render_template('T3_pilihAktiviti.html')

@app.route('/tingkatan3/nota')
def tingkatan3_nota():
    return render_template('T3_pilihNota.html')

@app.route('/tingakatan3/nota_minda')
def tingkatan3_nota_minda():
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)
    return render_template('T3_nota_peta.html', encoded_images=encoded_images)

@app.route('/tingakatan3/nota_kata')
def tingkatan3_nota_kata():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('T3_nota_kata.html', materials=materials)

@app.route('/tingkatan3/nota_video')
def tingkatan3_nota_video():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('T3_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence)

@app.route('/tingkatan3/nota_pdf')
def tingkatan3_nota_pdf():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('T3_nota_pdf.html', materials=materials)


@app.route('/tingkatan3/latihan')
def tingkatan3_latihan():
    return render_template('T3_pilihLatihan.html')

@app.route('/Tingkatan3/latihan_link')
def tingkatan3_latihan_link():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('T3_latihan_link.html', materials=materials)

@app.route('/tingkatan3/latihan_game')
def tingkatan3_latihan_game():
    cur = mysql.connection.cursor()
    cur.execute("SELECT words, hint FROM materials WHERE topic='Tingkatan 3: Matematik Pengguna I' AND category='Permainan'")
    game = cur.fetchall()
    return render_template('T3_latihan_game.html', game=game)

@app.route('/tingkatan3/kuiz')
def tingkatan3_kuiz():
    cur = mysql.connection.cursor()
    cur.execute("SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'Tingkatan 3: Matematik Pengguna I'")
    quiz = cur.fetchall()
    return render_template('T3_kuiz.html', quiz=quiz)

@app.route('/tingkatan4')
def tingkatan4():
    return render_template('T4_pilihAktiviti.html')

@app.route('/tingkatan4/nota')
def tingkatan4_nota():
    return render_template('T4_pilihNota.html')

@app.route('/tingakatan4/nota_minda')
def tingkatan4_nota_minda():
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)
    return render_template('T4_nota_peta.html', encoded_images=encoded_images)

@app.route('/tingakatan4/nota_kata')
def tingkatan4_nota_kata():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('T4_nota_kata.html', materials=materials)

@app.route('/tingkatan4/nota_video')
def tingkatan4_nota_video():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('T4_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence)

@app.route('/tingkatan4/nota_pdf')
def tingkatan4_nota_pdf():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('T4_nota_pdf.html', materials=materials)


@app.route('/tingkatan4/latihan')
def tingkatan4_latihan():
    return render_template('T4_pilihLatihan.html')

@app.route('/Tingkatan4/latihan_link')
def tingkatan4_latihan_link():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('T4_latihan_link.html', materials=materials)

@app.route('/tingkatan4/latihan_game')
def tingkatan4_latihan_game():
    cur = mysql.connection.cursor()
    cur.execute("SELECT words, hint FROM materials WHERE topic='Tingkatan 4: Matematik Pengguna II' AND category='Permainan'")
    game = cur.fetchall()
    return render_template('T4_latihan_game.html', game=game)

@app.route('/tingkatan4/kuiz')
def tingkatan4_kuiz():
    cur = mysql.connection.cursor()
    cur.execute("SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'Tingkatan 4: Matematik Pengguna II'")
    quiz = cur.fetchall()
    return render_template('T4_kuiz.html', quiz=quiz)


@app.route('/upload_note')
def upload_note():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM materials WHERE type = 'note' ")
    note = cur.fetchall()
    cur.close()
    return render_template('2lecPilihTopik_TambahNota.html', note=note)


@app.route('/upload_exercise')
def upload_exercise():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM materials WHERE type = 'latihan' AND category='latihan'")
    exercise = cur.fetchall()
    cur.close()
    return render_template('2lecPilihTopik_TambahLatihan.html', exercise=exercise)


@app.route('/upload/kuiz')
def upload_kuiz():
    cur = mysql.connection.cursor()
    cur.execute("SELECT topik, soalan, jawapan FROM quiz")
    quiz = cur.fetchall()
    cur.close()
    return render_template('2lecPilihTopik_TambahKuiz.html', quiz=quiz)


@app.route('/note_form')
def note_form():
    return render_template(('2lecPilihTopik_TambahNota_form.html'))


@app.route('/exercise_form')
def exercise_form():
    return render_template(('2lecPilihTopik_TambahLatihan_form.html'))


@app.route('/quiz_form')
def quiz_form():
    return render_template(('2lecPilihTopik_TambahKuiz_form.html'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        room_code = generate_room_code(6, list(user_rooms.keys()))
        id = request.form["id"]
        password = request.form["password"]
        role = "Pelajar"
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO profile (id, password, role, roomcode) VALUES (%s, %s, %s, %s)", (id, password, role, room_code))
        mysql.connection.commit()
        session['username'] = id
        return render_template('4Profile.html')
    return render_template('login.html')

def generate_room_code(length: int, existing_codes: list[str]) -> str:
    while True:
        code_chars = [random.choice(ascii_letters) for _ in range(length)]
        code = ''.join(code_chars)

        if code not in existing_codes:
            return code



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        id = request.form["id"]
        password = request.form["password"]
        option = request.form["option"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT role FROM profile WHERE id = %s", (id,))
        role = cur.fetchone()
        cur.execute("SELECT password FROM profile WHERE id = %s", (id,))
        check_password = cur.fetchone()
        cur.close()
        if password == check_password[0] and role[0] == option:
            session['username'] = id
            # Create a chat room for the user and store it in the user_rooms dictionary
            user_rooms[id] = {
                'members': 0,
                'messages': []
            }
            if option == "Pelajar":
                return redirect(url_for('mainpage'))
            else:
                return redirect(url_for('lecpage'))
    return render_template('login.html')

@app.route("/insert", methods=["POST", "GET"])
def insert():
    user_id = session.get("username")
    if request.method == "POST":
        if "name" in request.form:
            name = request.form["name"]
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE profile SET name=%s WHERE id = %s",
                (name, user_id))
            mysql.connection.commit()
        elif "huraian" in request.form:
            huraian = request.form["huraian"]
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE profile SET huraian=%s WHERE id = %s",
                (huraian, user_id))
            mysql.connection.commit()
        else:
            birth = request.form["birth"]
            gender = request.form["gender"]
            phone_no = request.form["phoneNo"]
            email = request.form["email"]
            school = request.form["school"]
            baris1=request.form["baris1"]
            baris2 = request.form["baris2"]
            poskod = request.form["poskod"]
            negeri = request.form["negeri"]
            cur = mysql.connection.cursor()
            cur.execute("UPDATE profile SET birth=%s, gender=%s, phone=%s, email=%s, school=%s, alamat1=%s, alamat2=%s, poskod=%s, negeri=%s WHERE id = %s",
                        (birth, gender, phone_no, email, school, baris1, baris2, poskod, negeri, user_id))
            mysql.connection.commit()
        return redirect(url_for('mainpage'))
    return render_template("4profile.html")


@app.route('/upload_materials', methods=['POST', 'GET'])
def upload_materials():
    if request.method == "POST":
        materials_type = request.form['type']
        topic = request.form['topic']
        category = request.form['category']
        if category == "Permainan":
            words = request.form['perkataan']
            soalan = request.form['soalan']
            hint = request.form['hint']
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO materials (type, topic, category, words, soalan, hint) VALUES (%s, %s, %s, %s, %s, %s)",
                (materials_type, topic, category, words, soalan, hint))
            mysql.connection.commit()
        else:
            filename = request.form['filename']
            description = request.form['description']
            file = request.files['file']
            filetype = file.mimetype
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO materials (type, topic, category, filename, description, content, filetype) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (materials_type, topic, category, filename, description, file.read(), filetype))
            mysql.connection.commit()
    return render_template('2lecPilihTopik.html')


@app.route('/download/<filename>', methods=["GET"])
def download(filename):
    cur = mysql.connection.cursor()
    cur.execute("SELECT content, filetype FROM materials WHERE filename=%s", (filename,))
    file = cur.fetchone()
    if file[1] == "application/pdf":
        filetype = ".pdf"
    elif file[1] == "image/png":
        filetype = ".png"
    elif file[1] == "video/mp4":
        filetype = ".mp4"
    if file:
        return send_file(io.BytesIO(file[0]), download_name=filename + filetype, as_attachment=True)


@app.route('/upload/quiz', methods=["POST", "GET"])
def upload_quiz():
    if request.method == "POST":
        topic = request.form['topic']
        soalan = request.form['soalan']
        pilihan1 = request.form['pilihan1']
        pilihan2 = request.form['pilihan2']
        pilihan3 = request.form['pilihan3']
        pilihan4 = request.form['pilihan4']
        jawapan = request.form['jawapan']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO quiz (topik, soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (topic, soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan))
        mysql.connection.commit()
    return render_template('2lecPilihTopik.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
