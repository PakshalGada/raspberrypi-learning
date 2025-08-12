from modules.web.app import app, init_db

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    
