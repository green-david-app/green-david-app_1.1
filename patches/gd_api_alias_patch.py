# Alias so old "/gd/api/tasks" works exactly like "/api/tasks"
@app.route("/gd/api/tasks", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def gd_api_tasks_alias():
    return api_tasks()
