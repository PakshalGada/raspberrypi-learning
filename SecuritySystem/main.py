from modules.web.app import app,init_db,init_camera

if __name__ == '__main__':
    init_db()
    init_camera()
    app.run(debug=True, host='0.0.0.0', port=5000)

