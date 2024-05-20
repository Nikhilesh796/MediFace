from flask import Flask,render_template, request, flash, url_for, redirect, session
from flask_pymongo import PyMongo
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import base64
import cv2
from PIL import Image
import numpy as np
import os
import random
import time

app = Flask(__name__)
app.secret_key = "21pa1a1286@2025"

myclient = MongoClient("mongodb+srv://21pa1a1286:charishma@cluster0.nsdecj7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

#Patient db
patientdb = myclient["MediFace"]
patientcol = patientdb["patient-details"]
medicinecol = patientdb["medicine_details"]
testreports_col = patientdb["test_reports"]

# Worker db
logindb = myclient["Authentication"]
receptionistcol = logindb["User-details"]
data_entry_op_col = logindb["Data-entry-op-details"]

# Data collector
def generate_dataset(id):
    face_classifier = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    def face_cropped(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return None
        for (x, y, w, h) in faces:
            cropped_face = img[y:y+h, x:x+w]
            return cropped_face

    cap = cv2.VideoCapture(0)
    img_id = 0

    while True:
        ret, frame = cap.read()
        if face_cropped(frame) is not None:
            img_id += 1
            face = cv2.resize(face_cropped(frame), (200, 200))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

            # Data augmentation: random flips
            if random.random() < 0.5:
                face = cv2.flip(face, 1)

            # Histogram equalization
            equalized_face = cv2.equalizeHist(face)
            cv2.imwrite(f"data/user.{id}.{img_id}.jpg", equalized_face)

            cv2.putText(face, str(img_id), (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Cropped face", face)

        if cv2.waitKey(1) == 13 or img_id == 200:
            break

    cap.release()
    cv2.destroyAllWindows()

    
    print("Dataset generation completed.")
    app.config['dataset_generated'] = True

# Training classifier
def train_classifier(data_dir):
    path = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    faces = []
    ids = []

    for image in path:
        img = Image.open(image).convert('L')
        imageNp = np.array(img, 'uint8')
        id_c = int(os.path.split(image)[1].split(".")[1])
        faces.append(imageNp)
        ids.append(id_c)

    ids = np.array(ids)

    # Train and save classifier
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.train(faces, ids)
    clf.write("classifier1.xml")
    print("Classifier training completed.")
    app.config['classifier_trained'] = True

# Evaluate accuracy
def evaluate_accuracy(data_dir, clf):
    path = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    faces = []
    actual_ids = []
    predicted_ids = []
    faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

    for image in path:
        img = Image.open(image).convert('L')
        image_np = np.array(img, 'uint8')
        id_c = int(os.path.split(image)[1].split(".")[1])

        faces.append(image_np)
        actual_ids.append(id_c)

        gray = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
        features = faceCascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in features:
            gray_roi = gray[y:y + h, x:x + w]
            gray_roi = cv2.cvtColor(gray_roi, cv2.COLOR_BGR2GRAY)
            id_p, confidence = clf.predict(gray_roi)
            predicted_ids.append(id_p)

    correct_predictions = sum(1 for actual, predicted in zip(actual_ids, predicted_ids) if actual == predicted)
    print(correct_predictions)
    accuracy = correct_predictions / len(actual_ids) * 100

    return accuracy

# Caller for accuracy function
def accuracy_caller():
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier1.xml")
    accuracy = evaluate_accuracy("data", clf)
    print(f"Accuracy: {accuracy:.2f}%")

# Detecting the faces
def draw_boundary(img, classifier, scaleFactor, minNeighbors, color, text, clf):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    features = classifier.detectMultiScale(gray_img, scaleFactor, minNeighbors)
    id_p = -1
    for (x, y, w, h) in features:
        cv2.rectangle(img, (x, y), (x+w, y+h), color, 2)
        id_p, pred = clf.predict(gray_img[y:y+h, x:x+w])
        #name = patientcol.find({"patient_id":id_p}).get("name")
        confidence = int(100 * (1 - pred / 300))

        if confidence > 75:
            cv2.putText(img, str(id_p), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1, cv2.LINE_AA)
        else:
            cv2.putText(img, "UNKNOWN", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
    

    return [img, id_p]


# Caller for face detection
def detect():
    faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read("classifier1.xml")
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, img = video_capture.read()
        l1 = draw_boundary(img, faceCascade, 1.3, 6, (255, 255, 255), "Face", clf)
        cv2.imshow("face Detection", l1[0])

        if cv2.waitKey(1) == 13:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    
   # return id_p  # Assuming id_p is the result of face detection
    return l1[1]


# detection_complete = False
# id_p = None  # Initialize id_p to None

# def detect():
#     global detection_complete, id_p

#     faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
#     clf = cv2.face.LBPHFaceRecognizer_create()
#     clf.read("classifier1.xml")
#     video_capture = cv2.VideoCapture(0)

#     while not detection_complete:
#         ret, img = video_capture.read()
#         l1 = draw_boundary(img, faceCascade, 1.3, 6, (255, 255, 255), "Face", clf)
#         cv2.imshow("face Detection", l1[0])

#         if l1[1] != -1:
#             id_p = l1[1]
#             detection_complete = True  # Set the flag to indicate detection is complete
#             break

#         if cv2.waitKey(1) == 13:
#             break

#     video_capture.release()
#     cv2.destroyAllWindows()


# Normal functionality
# while True:
#     print("1. Add face\n2. Train\n3. Detect face\n4. Exit")
#     x1 = int(input("Enter your choice: "))

#     if x1 == 1:
#         id += 1
#         generate_dataset(id)
#     elif x1 == 2:
        
#         print("Training done....")
#         accuracy_caller()
#     elif x1 == 3:
#         id_out = detect()
#         print(id_out)
#     else:
#         break



# d = list(patientcol.find().sort("date", pymongo.ASCENDING))
# print(d)

# Lander
@app.route("/",methods=['GET','POST'])
def lander():
    if request.method=='POST':
        user_name = request.form.get('username')
        password = request.form.get('pswd')
        login_type = request.form.get("flexRadioDefault")
        # x = logincol.insert_one({'username':user_name,'password':password})
        if login_type == "receptionist":
            if receptionistcol.find_one({"username":user_name,"password":password}):
                session['user'] = user_name
                flash('Login Successful','success')
                return redirect(url_for('wmain', username=user_name))
            else:
                flash('Invalid username or password','danger')
        elif login_type == "data_entry_operator":
            if data_entry_op_col.find_one({"username":user_name,"password":password}):
                session['user'] = user_name
                flash('Login Successful','success')
                return redirect(url_for('dmain', username=user_name))
            else:
                flash('Invalid username or password','danger')
    return render_template("lander.html")


@app.route("/plogin")
def plogin():
    id_p=detect()  # Start the detection process
    session['user'] = id_p
    return redirect(url_for('pmain', username=id_p))


# Worker Page
@app.route("/wmain/<username>",methods=['GET','POST'])
def wmain(username):
    if "user" in session:
        return render_template("home_worker.html",name=username)
    else:
        flash("Please login",'danger')
        return redirect(url_for('lander'))
    

 # Patient Page   
@app.route("/pmain/<username>",methods=['GET','POST'])
def pmain(username):
    if "user" in session:
        name = patientcol.find_one({'patient_id':username})["name"]
        return render_template("home_patient.html",name=name)
    else:
        flash("Please login",'danger')
        return redirect(url_for('lander'))

    
# Data entry operator page
@app.route("/dmain/<username>", methods=['GET','POST'])
def dmain(username):
    if "user" in session:
        return render_template("home_dataeop.html", name=username)
    else:
        flash("Please login", 'danger')
        return redirect(url_for('lander'))
    
# New Scan
@app.route("/newscan")
def scan():
    n = len(list(patientcol.find()))
    app.config['dataset_generated'] = False
    app.config['classifier_trained'] = False

    generate_dataset(n)
    while not app.config['dataset_generated']:
        pass  # Wait for dataset generation to complete

    train_classifier("data")
    while not app.config['classifier_trained']:
        pass  # Wait for classifier training to complete

    return render_template("form_new.html", u_id=n)


# New Form
@app.route("/form",methods=['GET','POST'])
def form():
    if request.method=='POST':
        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        place = request.form.get("place")
        mobile_no = request.form.get("number")
        symptoms = request.form.get("symptoms")
        doctor = request.form.get('doctor')
        status = request.form.get('status')
        patient_id = request.form.get("u_id")
        x = patientcol.insert_one({"patient_id":patient_id,"name": name, "age": age, "gender": gender, "status":status, "place": place, "mobile_number": mobile_no, "appointment":{"0":[str(datetime.now())[:10],str(datetime.now())[11:16],symptoms,doctor]}})
        flash("Appointment Booked","success")
        return redirect(url_for("wmain",username=session.get('user')))
    return render_template("form_new.html")


# @app.route("/existingscan")
# def existingscan():
    

#     id_p = detect()
 

#     return render_template("form_existing.html", u_id=id_p
@app.route("/existingscan")
def existingscan():
    id_p=detect()  # Start the detection process
    return render_template("form_existing.html", u_id=id_p)

# Existing Form
@app.route("/eform",methods=["GET","POST"])
def eform():
    if request.method=='POST':
        health_condition = request.form.get("symptoms")
        doctor = request.form.get("doctor")
        id = request.form.get("u_id")
        patient_details_cursor = patientcol.find({"patient_id": id})
        for patient_detail in patient_details_cursor:
            appointments = patient_detail.get("appointment", [])

            appointments[str(len(appointments))]=[str(datetime.now())[:10],str(datetime.now())[11:16], health_condition, doctor]
            patientcol.update_one({"_id": patient_detail["_id"]}, {"$set": {"appointment": appointments}})
        flash("Appointment Booked","success")
        return redirect(url_for("wmain",username=session.get('user')))
    return render_template("form_existing.html")

# Medicine Form
@app.route("/mform",methods=["GET","POST"])
def mform():
    if request.method=='POST':

        medicine = request.form.get("medicine")
        patient_id = request.form.get("id")
        med = medicinecol.insert_one({"patient_id":patient_id,'prescription':medicine})
        flash("Prescription Uploaded","success")
        return redirect(url_for("dmain",username=session.get('user')))
    return render_template("form_medicine.html")


# Test reports form
@app.route('/tform')
def tform():
    return render_template('form_testreports.html')

def b64encode_filter(content):
    return base64.b64encode(content).decode('utf-8')
app.jinja_env.filters['b64encode'] = b64encode_filter


# Test Reports Upload
@app.route('/upload', methods=['POST'])
def upload_file():
    patient_id = request.form.get('patient_id')
    if 'file' not in request.files:
        return 'No file part in the request'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        # Read the file content
        file_content = file.read()
        # Encode the file content as Base64
        encoded_content = base64.b64encode(file_content)
        # Insert the encoded content into MongoDB
        testreports_col.insert_one({'patient_id': patient_id,'filename': file.filename, 'content': encoded_content})
        flash("Test Reports Uploaded","success")
        return redirect(url_for("dmain",username=session.get('user')))


# Test Reports Retrieval
@app.route('/reports')
def list_files():
    files = testreports_col.find()
    decoded_files = []
    for file in files:
        decoded_content = base64.b64decode(file['content'])
        decoded_files.append({'filename': file['filename'], 'content': decoded_content})
    # Pass the decoded files to the HTML template
    return render_template('testreports.html', files=decoded_files)

# Logout
@app.route("/logout")
def logout():
    session.pop("user",None)
    flash("You have been logged out",'danger')
    return redirect(url_for('lander'))


# Profile
@app.route("/profile")
def profile():
    patient_profile = list(patientcol.find({"patient_id":str(session.get('user'))}))
    print(patient_profile)
    return render_template('profile.html',patient_profile=patient_profile)
    
    

# Prescription
@app.route("/prescription")
def prescription():
    medicine_details = medicinecol.find_one({"patient_id":str(session.get('user'))})
    return render_template("prescription.html",medicine_details=medicine_details)

# Medical History
@app.route("/history")
def medical_history():
    patient_profile = patientcol.find_one({"patient_id":str(session.get('user'))})
    print(patient_profile)
    return render_template('medical_history.html',patient_profile=patient_profile)
    


# def retrieve(id):
#     x = patientcol.find({'_id':OjectId(id)})
#     return x

if __name__ == "__main__":
    app.run(debug=True)