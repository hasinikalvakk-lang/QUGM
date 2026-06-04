import os
import io
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
from data_manager import QUGMDataEngine

app = Flask(__name__, template_folder='templates')
CORS(app)
engine = QUGMDataEngine()

# This holds the active dataset for the current user session
current_session_df = pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_data', methods=['POST'])
def generate():
    global current_session_df
    count = int(request.json.get('count', 1000))
    current_session_df = engine.generate_synthetic_dataset(count)
    
    return jsonify({
        "stats": engine.get_statistics(current_session_df),
        "data": current_session_df.to_dict(orient='records')
    })

@app.route('/upload_csv', methods=['POST'])
def upload():
    global current_session_df
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    try:
        # Load the uploaded CSV into the session variable
        current_session_df = pd.read_csv(file)
        
        # Immediate verification of required columns
        required = ['glucose_value', 'ppg_amplitude', 'age']
        if not all(col in current_session_df.columns for col in required):
            return jsonify({"error": f"CSV missing required columns: {required}"}), 400

        return jsonify({
            "stats": engine.get_statistics(current_session_df),
            "data": current_session_df.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/export_report', methods=['GET'])
def export_report():
    global current_session_df
    if current_session_df.empty:
        return "No data loaded to export", 400
    
    # Create an in-memory buffer for the CSV
    proxy = io.StringIO()
    current_session_df.to_csv(proxy, index=False)
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name="QUGM_Active_Session_Report.csv"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)