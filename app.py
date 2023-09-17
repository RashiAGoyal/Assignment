import os
from flask import Flask, render_template, request, redirect, url_for
from flask_restful import Api, Resource
from flask_jwt import JWT, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Configure image upload directory
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure JWT
def authenticate(username, password):
    # Implement your authentication logic here
    # Example: Check if username and password are valid
    if username == 'user' and password == 'password':
        return username

def identity(payload):
    # Implement your identity logic here
    # Example: Return the user based on the payload
    user_id = payload['identity']
    return {'user_id': user_id}

jwt = JWT(app, authenticate, identity)

# Configure rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["5 per minute"]
)

# Simple home page to upload an image
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'image' not in request.files:
            return redirect(request.url)
        image = request.files['image']
        if image.filename == '':
            return redirect(request.url)

        if image:
            # Ensure the filename is safe
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            # Display the result page with the image name
            return redirect(url_for('result', image_name=filename))

    return render_template('index.html')

# Result page to display the uploaded image name
@app.route('/result/<string:image_name>')
def result(image_name):
    return render_template('result.html', image_name=image_name)

# Protected API endpoint
class ProtectedResource(Resource):
    @jwt_required()
    @limiter.limit("5 per minute")
    def get(self):
        return {'message': 'Protected API endpoint'}

api = Api(app)
api.add_resource(ProtectedResource, '/api')

# API endpoint to upload captured photos
@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_photo():
    try:
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'error': 'Image data not found'}), 400

        # Generate a unique filename
        filename = secure_filename(f"user_{current_identity}_photo.jpg")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Decode and save the image
        image_data = data['image'].split(',')[1]
        image_data = base64.b64decode(image_data)
        with open(image_path, 'wb') as f:
            f.write(image_data)

        return jsonify({'image_name': filename}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

