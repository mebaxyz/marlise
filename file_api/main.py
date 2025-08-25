# app.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
# --- Configuration ---
# You must define the base directory where your user files are stored.
# For example: USER_FILES_DIR = "/path/to/your/user/files"
if "USER_FILES_DIR" not in os.environ:
    raise EnvironmentError("The USER_FILES_DIR environment variable is not set.")
USER_FILES_DIR = os.environ["USER_FILES_DIR"]


# --- File Type Definitions (moved from class to global scope) ---

COMPLETE_AUDIOFILE_EXTS = (
    # through libsndfile
    ".aif", ".aifc", ".aiff", ".au", ".bwf", ".flac", ".htk", ".iff", ".mat4", ".mat5", ".oga", ".ogg", ".opus",
    ".paf", ".pvf", ".pvf5", ".sd2", ".sf", ".snd", ".svx", ".vcc", ".w64", ".wav", ".xi",
    # extra through ffmpeg
    ".3g2", ".3gp", ".aac", ".ac3", ".amr", ".ape", ".mp2", ".mp3", ".mpc", ".wma",
)

HQ_AUDIOFILE_EXTS = (
    ".aif", ".aifc", ".aiff", ".flac", ".w64", ".wav",
)

# --- Helper Function (replaces the class method) ---

def get_dir_and_extensions_for_filetype(filetype):
    """
    Maps a filetype string to its corresponding directory and allowed extensions.
    """
    filetype_map = {
        "audioloop": ("Audio Loops", COMPLETE_AUDIOFILE_EXTS),
        "audiorecording": ("Audio Recordings", COMPLETE_AUDIOFILE_EXTS),
        "audiosample": ("Audio Samples", COMPLETE_AUDIOFILE_EXTS),
        "audiotrack": ("Audio Tracks", COMPLETE_AUDIOFILE_EXTS),
        "cabsim": ("Speaker Cabinets IRs", HQ_AUDIOFILE_EXTS),
        "h2drumkit": ("Hydrogen Drumkits", (".h2drumkit",)),
        "ir": ("Reverb IRs", HQ_AUDIOFILE_EXTS),
        "midiclip": ("MIDI Clips", (".mid", ".midi")),
        "midisong": ("MIDI Songs", (".mid", ".midi")),
        "sf2": ("SF2 Instruments", (".sf2", ".sf3")),
        "sfz": ("SFZ Instruments", (".sfz",)),
        "aidadspmodel": ("Aida DSP Models", (".aidax", ".json")),
        "nammodel": ("NAM Models", (".nam",)),
    }
    return filetype_map.get(filetype, (None, ()))


# --- Flask Route (replaces the Request Handler class) ---

@app.route('/files/list', strict_slashes=False)
def list_files():
    """
    Handles GET requests to list files based on specified types.
    """
    # 1. Get 'types' argument from the URL query string
    filetypes_str = request.args.get('types')
    if not filetypes_str:
        # Return a 400 Bad Request error if the parameter is missing
        error_response = {'ok': False, 'error': 'Missing required "types" parameter'}
        return jsonify(error_response), 400

    filetypes = filetypes_str.split(",")
    
    # Using a dictionary ensures that each file path is unique
    found_files = {}

    # 2. Walk directories and find matching files
    for filetype in filetypes:
        datadir, extensions = get_dir_and_extensions_for_filetype(filetype)
        if datadir is None:
            continue

        search_path = os.path.join(USER_FILES_DIR, datadir)
        if not os.path.isdir(search_path):
            # You might want to log a warning here if a directory is missing
            continue

        for root, dirs, files in os.walk(search_path):
            for name in files:
                if name.lower().endswith(extensions):
                    fullname = os.path.join(root, name)
                    found_files[fullname] = {
                        'fullname': fullname,
                        'basename': name,
                        'filetype': filetype,
                    }

    # 3. Sort the results alphabetically by full path
    sorted_fullnames = sorted(found_files.keys())
    sorted_files_list = [found_files[fn] for fn in sorted_fullnames]

    # 4. Return the successful JSON response
    return jsonify({
        'ok': True,
        'files': sorted_files_list,
    })

# --- Replicating TimelessRequestHandler Behavior ---

@app.after_request
def set_timeless_headers(response):
    """
    Modifies the response to disable caching, mimicking TimelessRequestHandler.
    """
    # Disable ETag generation
    response.add_etag = False
    # Set headers to prevent caching
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # The original code removed the 'Date' header, which is unusual but replicated here
    if 'Date' in response.headers:
        del response.headers['Date']
    return response

'''@app.after_request
def add_no_cache_headers(response):
    """
    Modifies the response to disable caching.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response'''

# --- To run this application ---
# 1. Set the environment variable:
#    export USER_FILES_DIR="/path/to/your/files"
# 2. Run the app:
#    flask --app app run
# 3. Access in your browser or with curl:
#    http://127.0.0.1:5000/files/list/?types=midiclip,sf2

if __name__ == '__main__':
    # This allows running the script directly with `python app.py` for development
    app.run(debug=True)