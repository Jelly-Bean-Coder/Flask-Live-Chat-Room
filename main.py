from flask import Flask, render_template, request, session, redirect, flash, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "bigpurplehuman"
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code


@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template(
                "home.html", error="Please enter a name", code=code, name=name
            )

        if join != False and not code:
            return render_template(
                "home.html", error="Please enter a room code", code=code, name=name
            )

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}

        elif code not in rooms:
            return render_template(
                "home.html", error="Room doesn't exist", code=code, name=name
            )  # for joining rooms, if create is false, join is true

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template(
        "room.html", room_code=room, messages=rooms[room]["messages"]
    )


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"],  # To save date history, sned the date in the data payload/JSON dict
        "date": data["date"],
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:  # * take away when integrating join any room code
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": f"has entred the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} has joined room {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    
    if room in rooms:
        leave_room(room)
        rooms[room]["members"] -= 1
        send({"name": name, "message": f"has left the room"}, to=room)
        print(f"{name} has left room {room}")
        
        if rooms[room]["members"] <= 0:
            del rooms[room]
                          

        


if __name__ == "__main__":
    socketio.run(app, debug=True)
