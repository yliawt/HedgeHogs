from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, session, jsonify
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
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM profile")
    id_list = [row[0] for row in cur.fetchall()]
    return render_template('login.html', idlist=id_list)


@app.route('/mainpage')
def mainpage():
    user_id = session.get('username')
    cur = mysql.connection.cursor()
    cur.execute("SELECT name from profile where id=%s", (user_id,))
    name = cur.fetchone()
    name = name[0]
    return render_template('1Index.html', name=name)


@app.route('/lecpage')
def lecpage():
    return render_template('1lecIndex.html')


@app.route('/materials')
def materials():
    return render_template('2lecPilihTopik.html')

from flask import jsonify

@app.route('/search', methods=["POST"])
def search():
    search_query = request.form.get('search')  # Retrieve the 'name' field from the form
    print(search_query)
    cur = mysql.connection.cursor()
    cur.execute("SELECT topic, category, filename FROM materials WHERE topic LIKE %s OR category LIKE %s OR filename LIKE %s ORDER BY topic ASC",
                ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
    results = list(cur.fetchall())  # Convert the tuple to a list
    cur.close()

    updated_results = []  # Initialize an empty list to store updated results

    for result in results:
        result_list = list(result)  # Convert the tuple to a list
        if result_list[0] == "Perpuluhan":
            if result_list[1] == "Peta Minda":
                result_list.append("/perpuluhan/nota_minda")
            elif result_list[1] == "PDF":
                result_list.append("/perpuluhan/nota_pdf")
            elif result_list[1] == "Video":
                result_list.append("/perpuluhan/nota_video")
            elif result_list[1] == "Gerbang Kata":
                result_list.append("/perpuluhan/nota_kata")
            elif result_list[1] == "Latihan":
                result_list.append("/perpuluhan/latihan_link")
        elif result_list[0] == "Tingkatan 3: Matematik Pengguna I":
            if result_list[1] == "Peta Minda":
                result_list.append("/tingkatan3/nota_minda")
            elif result_list[1] == "PDF":
                result_list.append("/tingkatan3/nota_pdf")
            elif result_list[1] == "Video":
                result_list.append("/tingkatan3/nota_video")
            elif result_list[1] == "Gerbang Kata":
                result_list.append("tingkatan3/nota_kata")
            elif result_list[1] == "Latihan":
                result_list.append("/tingkatan3/latihan_link")
        elif result_list[0] == "Tingkatan 4: Matematik Pengguna II":
            if result_list[1] == "Peta Minda":
                result_list.append("/tingkatan4/nota_minda")
            elif result_list[1] == "PDF":
                result_list.append("/tingkatan4/nota_pdf")
            elif result_list[1] == "Video":
                result_list.append("/tingkatan4/nota_video")
            elif result_list[1] == "Gerbang Kata":
                result_list.append("/tingkatan4/nota_kata")
            elif result_list[1] == "Latihan":
                result_list.append("/tingkatan4/latihan_link")
        updated_results.append(result_list)  # Append the updated list to the new list

    # If you need the updated_results as a tuple again, you can convert it back
    updated_results_tuple = tuple(updated_results)

    return jsonify(updated_results_tuple)



@app.route('/lecChatBox')
def lecchatbox():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT id FROM profile")
    user_id = cur.fetchall()
    cur.close()
    return render_template("3lecChatBox.html", username=user_id)


@app.route('/selectedChatBox', methods=['POST', 'GET'])
def selectedChatBox():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT id FROM profile")
    std = cur.fetchall()
    user_id = session.get('username')
    username = request.args.get('username')
    cur = mysql.connection.cursor()
    cur.execute("SELECT roomcode FROM profile WHERE id = %s", (username,))
    roomcode_result = cur.fetchone()
    roomcode = roomcode_result[0]
    session['room'] = roomcode
    cur.execute("SELECT sender, message, timestamp FROM chatbox WHERE roomcode = %s ORDER BY timestamp ASC",
                (roomcode,))
    messages = cur.fetchall()
    cur.close()
    username = str(username)
    return render_template('3lecChatBox.html', room=roomcode, username=std, user=user_id, messages=messages)


@app.route('/chatbox')
def chatbox():
    user_id = session.get('username')
    roomcode = session.get('room')
    # Retrieve the user's chat room from the user_rooms dictionary
    user_room = user_rooms.get(roomcode, None)
    cur = mysql.connection.cursor()
    cur.execute("SELECT sender, message, timestamp FROM chatbox WHERE roomcode = %s ORDER BY timestamp ASC",
                (roomcode,))
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

    custom_formatted_time = current_time.strftime('%d/%m/%Y, %I:%M:%S %p')

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO chatbox (roomcode, sender, message, timestamp) VALUES (%s, %s, %s, %s)",
        (room, name, message_text, custom_formatted_time)
    )
    mysql.connection.commit()
    print("success")
    cur.close()


@socketio.on('disconnect')
def handle_disconnect():
    room = session.get("room")
    leave_room(room)


@app.route('/profile')
def profile():
    user_id = session.get("username")
    role = session.get["role"]
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT name, birth, gender, phone, email, school, alamat1, alamat2, poskod, negeri, huraian, photo FROM profile WHERE id=%s",
        (user_id,))
    info = cur.fetchone()
    photo = info[11]

    if photo:
        encoded_image = base64.b64encode(photo).decode("utf-8")
        return render_template('4profile.html', info=info, photo=encoded_image, role=role)
    else:
        return render_template('4profile.html', info=info)


@app.route('/about_us')
def about_us():
    role=session.get("role")
    return render_template('5AboutUs.html', role=role)


@app.route('/logout')
def logout():
    return render_template('000main.html')


@app.route('/stdmaterial')
def stdmaterial():
    id=session["username"]
    cur=mysql.connection.cursor()
    cur.execute("SELECT perpuluhan, tingkatan3, tingkatan4 FROM profile WHERE id=%s",(id,))
    score=cur.fetchall()
    return render_template('2pilihTopik.html', score=score)


@app.route('/perpuluhan')
def perpuluhan():
    role=session.get("role")
    return render_template('Perpuluhan_pilihAktiviti.html',role=role)


@app.route('/perpuluhan/nota')
def perpuluhan_nota():
    role = session.get("role")
    return render_template('Perpuluhan_pilihNota.html',role=role)


@app.route('/perpuluhan/nota_minda')
def perpuluhan_nota_minda():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute("SELECT content FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)

    return render_template('Perpuluhan_nota_peta.html', encoded_images=encoded_images,role=role)


@app.route('/perpuluhan/nota_kata')
def perpuluhan_nota_kata():
    role=session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_nota_kata.html', materials=materials,role=role)


@app.route('/perpuluhan/nota_video')
def perpuluhan_nota_video():
    role=session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('Perpuluhan_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence,role=role)


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
    role=session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Perpuluhan' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_nota_pdf.html', materials=materials,role=role)


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
    role = session.get("role")
    return render_template('Perpuluhan_latihan_pilihJenis.html', role=role)


@app.route('/perpuluhan/latihan_link')
def perpuluhan_latihan_link():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Perpuluhan' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('Perpuluhan_latihan_link.html', materials=materials,role=role)


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
    return render_template('Perpuluhan_latihan_game.html', game=game)


@app.route('/perpuluhan/kuiz')
def perpuluhan_kuiz():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute("SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'perpuluhan'")
    quiz = cur.fetchall()
    return render_template('Perpuluhan_kuiz.html', quiz=quiz, role=role)


@app.route('/tingakatan3')
def tingkatan3():
    role = session.get("role")
    return render_template('T3_pilihAktiviti.html',role=role)


@app.route('/tingkatan3/nota')
def tingkatan3_nota():
    role = session.get("role")
    return render_template('T3_pilihNota.html',role=role)


@app.route('/tingakatan3/nota_minda')
def tingkatan3_nota_minda():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)
    return render_template('T3_nota_peta.html', encoded_images=encoded_images,role=role)


@app.route('/tingakatan3/nota_kata')
def tingkatan3_nota_kata():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('T3_nota_kata.html', materials=materials,role=role)


@app.route('/tingkatan3/nota_video')
def tingkatan3_nota_video():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('T3_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence,role=role)


@app.route('/tingkatan3/nota_pdf')
def tingkatan3_nota_pdf():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('T3_nota_pdf.html', materials=materials,role=role)


@app.route('/tingkatan3/latihan')
def tingkatan3_latihan():
    role = session.get("role")
    return render_template('T3_pilihLatihan.html',role=role)


@app.route('/tingkatan3/latihan_link')
def tingkatan3_latihan_link():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Tingkatan 3: Matematik Pengguna I' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('T3_latihan_link.html', materials=materials,role=role)


@app.route('/tingkatan3/latihan_game')
def tingkatan3_latihan_game():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT words, hint FROM materials WHERE topic='Tingkatan 3: Matematik Pengguna I' AND category='Permainan'")
    game = cur.fetchall()
    return render_template('T3_latihan_game.html', game=game)


@app.route('/tingkatan3/kuiz')
def tingkatan3_kuiz():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'Tingkatan 3: Matematik Pengguna I'")
    quiz = cur.fetchall()
    return render_template('T3_kuiz.html', quiz=quiz,role=role)


@app.route('/tingkatan4')
def tingkatan4():
    role = session.get("role")
    return render_template('T4_pilihAktiviti.html',role=role)


@app.route('/tingkatan4/nota')
def tingkatan4_nota():
    role = session.get("role")
    return render_template('T4_pilihNota.html',role=role)


@app.route('/tingakatan4/nota_minda')
def tingkatan4_nota_minda():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Peta Minda' ")
    materials = cur.fetchall()
    encoded_images = []
    for material in materials:
        encoded_image = base64.b64encode(material[0]).decode("utf-8")
        encoded_images.append(encoded_image)
    return render_template('T4_nota_peta.html', encoded_images=encoded_images,role=role)


@app.route('/tingakatan4/nota_kata')
def tingkatan4_nota_kata():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Gerbang Kata' ")
    materials = cur.fetchall()
    return render_template('T4_nota_kata.html', materials=materials,role=role)


@app.route('/tingkatan4/nota_video')
def tingkatan4_nota_video():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='Video'")
    videos = cur.fetchall()
    videos_with_sequence = [(video, f"Video {index + 1:02d}") for index, video in enumerate(videos)]
    return render_template('T4_nota_video.html', videos=videos, videos_with_sequence=videos_with_sequence,role=role)


@app.route('/tingkatan4/nota_pdf')
def tingkatan4_nota_pdf():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT content, filename FROM materials WHERE type = 'note' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='PDF' ")
    materials = cur.fetchall()
    return render_template('T4_nota_pdf.html', materials=materials,role=role)


@app.route('/tingkatan4/latihan')
def tingkatan4_latihan():
    role = session.get("role")
    return render_template('T4_pilihLatihan.html',role=role)


@app.route('/Tingkatan4/latihan_link')
def tingkatan4_latihan_link():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT filename FROM materials WHERE type = 'latihan' AND topic='Tingkatan 4: Matematik Pengguna II' AND category='latihan' ")
    materials = cur.fetchall()
    return render_template('T4_latihan_link.html', materials=materials,role=role)


@app.route('/tingkatan4/latihan_game')
def tingkatan4_latihan_game():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT words, hint FROM materials WHERE topic='Tingkatan 4: Matematik Pengguna II' AND category='Permainan'")
    game = cur.fetchall()
    return render_template('T4_latihan_game.html', game=game)


@app.route('/tingkatan4/kuiz')
def tingkatan4_kuiz():
    role = session.get("role")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE topik = 'Tingkatan 4: Matematik Pengguna II'")
    quiz = cur.fetchall()
    return render_template('T4_kuiz.html', quiz=quiz,role=role)


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
    cur.execute("SELECT * FROM materials WHERE type = 'latihan' AND category='Permainan'")
    permainan = cur.fetchall()
    cur.close()
    return render_template('2lecPilihTopik_TambahLatihan.html', exercise=exercise, permainan=permainan)


@app.route('/upload/kuiz')
def upload_kuiz():
    cur = mysql.connection.cursor()
    cur.execute("SELECT topik, soalan, jawapan FROM quiz")
    quiz = cur.fetchall()
    cur.close()
    return render_template('2lecPilihTopik_TambahKuiz.html', quiz=quiz)


@app.route('/note_form')
def note_form():
    nota = {
        'topic': '',
        'category': '',
        'filename': '',
        'description': ''
    }
    return render_template(('2lecPilihTopik_TambahNota_form.html'), nota=nota)


@app.route('/delete_permainan')
def delete_permainan():
    soalan = request.args.get('soalan')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM materials WHERE soalan=%s", (soalan,))
    mysql.connection.commit()
    return render_template('2lecPilihTopik_TambahLatihan.html')


@app.route('/delete_nota')
def delete_nota():
    filename = request.args.get('name')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM materials WHERE  filename=%s", (filename,))
    mysql.connection.commit()
    return redirect(url_for('upload_note'))


@app.route('/modify_nota')
def modify_nota():
    filename = request.args.get('name')
    cur=mysql.connection.cursor()
    cur.execute("SELECT topic, category, filename, description FROM materials WHERE filename=%s",(filename,))
    nota=cur.fetchone()
    action="modify"
    return render_template('2lecPilihTopik_TambahNota_form.html', nota=nota, action=action)

@app.route('/modify_latihan')
def modify_latihan():
    filename = request.args.get('name')
    cur=mysql.connection.cursor()
    cur.execute("SELECT topic, category, filename, description FROM materials WHERE filename=%s",(filename,))
    nota=cur.fetchone()
    action="modify latihan"
    return render_template('2lecPilihTopik_TambahLatihan_form.html', nota=nota, action=action)

@app.route('/delete_latihan')
def delete_latihan():
    filename = request.args.get('name')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM materials WHERE  filename=%s", (filename,))
    mysql.connection.commit()
    return redirect(url_for('upload_exercise'))

@app.route('/modify_permainan')
def modify_permainan():
    soalan = request.args.get('soalan')
    cur = mysql.connection.cursor()
    cur.execute("SELECT topic, category, soalan, words, hint FROM materials WHERE soalan=%s", (soalan,))
    nota = cur.fetchone()
    action = "modify permainan"
    return render_template('2lecPilihTopik_TambahLatihan_form.html', nota=nota, action=action)

@app.route('/update_permainan', methods=['POST','GET'])
def update_permainan():
    if request.method=="POST":
        name=request.args.get('name')
        materials_type = request.form['type']
        topic = request.form['topic']
        words = request.form['perkataan']
        soalan = request.form['soalan']
        hint = request.form['hint']
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE materials SET type=%s, topic=%s, words=%s, soalan=%s, hint=%s WHERE soalan=%s",
            (materials_type, topic, words, soalan, hint, name))
        mysql.connection.commit()
    return redirect(url_for('upload_exercise'))

@app.route('/modify_materials',methods=['POST','GET'])
def modify_materials():
    if request.method == "POST":
        name = request.args.get('name')
        materials_type = request.form['type']
        topic = request.form['topic']
        category = request.form['category']
        if category == "Permainan":
            words = request.form['perkataan']
            soalan = request.form['soalan']
            hint = request.form['hint']
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE materials SET type=%s, topic=%s, category=%s, words=%s, soalan=%s, hint=%s WHERE soalan=%s",
                (materials_type, topic, category, words, soalan, hint,name))
            mysql.connection.commit()
        else:
            filename = request.form['filename']
            description = request.form['description']
            file = request.files['file']
            filetype = file.mimetype
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE materials SET type=%s, topic=%s, category=%s, filename=%s, description=%s, content=%s, filetype=%s WHERE filename=%s",
                (materials_type, topic, category, filename, description, file.read(), filetype, name))
            mysql.connection.commit()
    return render_template('2lecPilihTopik.html')

@app.route('/modify_quiz')
def modify_quiz():
    soalan = request.args.get('soalan')
    cur = mysql.connection.cursor()
    cur.execute("SELECT topik, soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan FROM quiz WHERE soalan=%s", (soalan,))
    quiz = cur.fetchone()
    action = "modify"
    return render_template('2lecPilihTopik_TambahKuiz_form.html', quiz=quiz, action=action)

@app.route('/update_quiz', methods=['POST','GET'])
def update_quiz():
    if request.method=="POST":
        name = request.args.get('name')
        topic = request.form['topic']
        soalan = request.form['soalan']
        pilihan1 = request.form['pilihan1']
        pilihan2 = request.form['pilihan2']
        pilihan3 = request.form['pilihan3']
        pilihan4 = request.form['pilihan4']
        jawapan = request.form['jawapan']
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE quiz SET topik=%s, soalan=%s, pilihan1=%s, pilihan2=%s, pilihan3=%s, pilihan4=%s, jawapan=%s WHERE soalan=%s",
            (topic, soalan, pilihan1, pilihan2, pilihan3, pilihan4, jawapan, name))
        mysql.connection.commit()
    return redirect(url_for('upload_kuiz'))

@app.route('/delete_quiz')
def delete_quiz():
    soalan = request.args.get('soalan')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM quiz WHERE soalan=%s", (soalan,))
    mysql.connection.commit()
    return redirect(url_for('upload_kuiz'))

@app.route('/exercise_form')
def exercise_form():
    nota={}
    return render_template('2lecPilihTopik_TambahLatihan_form.html',nota=nota)


@app.route('/quiz_form')
def quiz_form():
    quiz={}
    return render_template('2lecPilihTopik_TambahKuiz_form.html',quiz=quiz)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        room_code = generate_room_code(6, list(user_rooms.keys()))
        id = request.form["id"]
        password = request.form["password"]
        role = "Pelajar"
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO profile (id, password, role, roomcode) VALUES (%s, %s, %s, %s)",
                    (id, password, role, room_code))
        mysql.connection.commit()
        session['username'] = id
        return render_template('4Profile.html')


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
            session['username'] = id  # Use a unique key for the session, e.g., 'user_id'
            # Create a chat room for the user and store it in the user_rooms dictionary
            cur = mysql.connection.cursor()
            cur.execute("SELECT roomcode,role FROM profile WHERE id = %s", (id,))
            roomcode_result = cur.fetchone()
            roomcode = roomcode_result[0]
            session['role'] = roomcode_result[1]
            session['room'] = roomcode
            user_rooms[session['room']] = {
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
        cur = mysql.connection.cursor()
        if "name" in request.form or "photo" in request.form:
            name = request.form["name"]
            photo = request.files["photo"]
            cur.execute(
                "UPDATE profile SET name=%s, photo=%s WHERE id = %s",
                (name, photo.read(), user_id))
            mysql.connection.commit()
        elif "huraian" in request.form:
            huraian = request.form["huraian"]
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
            baris1 = request.form["baris1"]
            baris2 = request.form["baris2"]
            poskod = request.form["poskod"]
            negeri = request.form["negeri"]
            cur.execute(
                "UPDATE profile SET birth=%s, gender=%s, phone=%s, email=%s, school=%s, alamat1=%s, alamat2=%s, poskod=%s, negeri=%s WHERE id = %s",
                (birth, gender, phone_no, email, school, baris1, baris2, poskod, negeri, user_id))
            mysql.connection.commit()
        cur.close()
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


@app.route('/store-quiz-results', methods=['POST'])
def store_quiz_results():
    id = session['username']
    data = request.json
    correct_answers = data['correctAnswers']
    total_questions = data['totalQuestions']
    category = data['category']

    # Calculate the user's score
    score = (correct_answers / total_questions) * 100
    cur = mysql.connection.cursor()
    if category == "perpuluhan":
        cur.execute("SELECT perpuluhan FROM profile WHERE id=%s", (id,))
        ori = cur.fetchone()
        if score > ori[0]:
            cur.execute("UPDATE profile SET perpuluhan=%s WHERE id=%s", (score, id))
    elif category == "tingkatan3":
        print("testing")
        cur.execute("SELECT tingkatan3 FROM profile WHERE id=%s", (id,))
        ori = cur.fetchone()
        if score > ori[0]:
            cur.execute("UPDATE profile SET tingkatan3=%s WHERE id=%s", (score, id))
    elif category == "tingkatan4":
        cur.execute("SELECT tingkatan4 FROM profile WHERE id=%s", (id,))
        ori = cur.fetchone()
        if score > ori[0]:
            cur.execute("UPDATE profile SET tingkatan4=%s WHERE id=%s", (score, id))
    mysql.connection.commit()
    response_data = {
        'message': 'Quiz results stored successfully',
        'score': score
    }

    return jsonify(response_data), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
