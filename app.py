from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from utils.video_validation import validate_video_metadata, adjust_video

app = Flask(__name__)
CORS(app)

# Constants
OUTPUT_DIR = './sign_language_data/'
GESTURES = ["aleji", "ambulance", "daktari", "damu", "dawa", "homa"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Ensure gesture folders exist
for gesture in GESTURES:
    os.makedirs(os.path.join(OUTPUT_DIR, gesture), exist_ok=True)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'API is running'}), 200


@app.route('/gestures', methods=['GET'])
def list_gestures():
    """List available gestures."""
    return jsonify({'gestures': GESTURES}), 200


@app.route('/upload', methods=['POST'])
def upload_video():
    """Handles video upload with relaxed validation."""
    try:
        gesture = request.form.get('gesture')
        file = request.files.get('file')

        if gesture not in GESTURES:
            return jsonify({'error': 'Invalid gesture name.'}), 400

        if not file:
            return jsonify({'error': 'No file provided.'}), 400

        temp_filepath = os.path.join(OUTPUT_DIR, f'temp_{file.filename}')
        file.save(temp_filepath)

        # Relax validation: Accept all videos
        logging.info("Relaxed validation: Allowing all videos to pass.")

        # Save to gesture folder
        count = len(os.listdir(os.path.join(OUTPUT_DIR, gesture)))
        final_filename = os.path.join(OUTPUT_DIR, gesture, f"{gesture}_{count + 1}.webm")
        os.rename(temp_filepath, final_filename)

        logging.info(f"Video submitted successfully: {final_filename}")
        return jsonify({'message': 'Video submitted successfully!', 'filename': final_filename}), 200
    except Exception as e:
        logging.error(f"Internal server error during video upload: {e}")
        return jsonify({'error': 'Internal server error occurred. Please check logs for details.'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
