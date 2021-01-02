import json
from quart import Quart, jsonify, request, redirect, url_for
import pg8000
from quart.templating import render_template
import os
from database import get_database_connection

app = Quart(__name__)

@app.route("/", methods=["GET", "POST"])
async def index_route():
    if request.method == "POST":
        form = await request.form
        data = await request.get_data()
        print(form, data)

    return await render_template("hello.html")

@app.route("/create", methods=["POST"])
async def create_poll_route():
    form = await request.form
    json_data = {key: form[key] for key in form.keys()}
    results = {form[key]: 0 for key in json_data.keys() if key != "title"}
    print(json_data)

    conn = get_database_connection()
    query_result = conn.run(
        "insert into pollster (id, results, title) values (uuid_generate_v4(), :results, :title) returning id",
        title=json_data["title"],
        results=json.dumps(results)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("get_poll_route", id=query_result[0][0]))

@app.route("/poll/<id>", methods=["GET"])
async def get_poll_route(id):
    conn = get_database_connection()
    query_result = conn.run(
        "select id, title, results from pollster where id=:id",
        id=id
    )
    conn.close()

    print(query_result)

    poll_id = query_result[0][0]
    poll_title = query_result[0][1]
    poll_results = query_result[0][2]

    return await render_template("poll.html", title=poll_title, options=poll_results, poll_id=str(poll_id))

@app.route("/vote/<id>", methods=["POST"])
async def vote_route(id):

    form = await request.form
    print([k for k in form.keys()])
    vote = form["vote"]

    conn = get_database_connection()
    result_query = conn.run(
        "select results from pollster where id=:id",
        id=id
    )

    results = result_query[0][0]
    results[vote] += 1

    update_query = conn.run(
        "update pollster set results=:results where id=:id",
        id=id,
        results=json.dumps(results)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("results_route", id=id))

@app.route("/results/<id>", methods=["GET"])
async def results_route(id):
    conn = get_database_connection()
    query_result = conn.run(
        "select title, results from pollster where id=:id",
        id=id
    )
    conn.close()

    poll_title = query_result[0][0]
    poll_results = [{"category": key, "value": query_result[0][1][key]} for key in query_result[0][1].keys()]
    print(poll_results)

    return await render_template("results.html", poll_title=poll_title, poll_results=json.dumps(poll_results))

@app.route("/about", methods=["GET"])
async def about_route():
    return await render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", 5000))