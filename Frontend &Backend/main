from flask import Flask,render_template, request, flash, url_for, redirect, session
from flask_pymongo import PyMongo
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "21pa1a1286@2025"

myclient = MongoClient("mongodb+srv://21pa1a1286:charishma@cluster0.nsdecj7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# patientdb = myclient["MediFace"]
# patientcol = patientdb["patient-details"]

logindb = myclient["Authentication"]
logincol = logindb["User-details"]

@app.route("/",methods=['GET','POST'])
def lander():
    if request.method=='POST':
        user = request.form.get('username')
        password = request.form.get('pswd')
        # x = logincol.insert_one({'username':user_name,'password':password})

        if logincol.find_one({"username":user,"password":password}):
            session['user'] = user
            flash('Login Successful','success')
            return redirect(url_for('main'))
        else:
            flash('Invalid username or password','danger')
    return render_template("lander.html")

@app.route("/form",methods=['GET','POST'])
def form():
    # if request.method=='POST':
#     name = request.form.get("name")
#     age = request.form.get("age")
#     gender = request.form.get("gender")
#     place = request.form.get("place")
#     mobile_no = request.form.get("number")
#     symptoms = request.form.get("symptoms")
#     x = patientcol.insert_one({"_id" : id, "name": name, "age": age, "gender": gender, "place": place, "mobile_number": mobile_no, "symptoms": symptoms})
    
   
    return render_template("newform.html")

@app.route("/main",methods=['GET','POST'])
def main():
    if "user" in session:
        user = session['user']
        return render_template("home.html",name=user)
    else:
        flash("Please login",'danger')
        return redirect(url_for('lander'))
    
@app.route("/logout")
def logout():
    session.pop("user",None)
    flash("You have been logged out",'success')
    return redirect(url_for('lander'))


@app.route("/profile")
def profile():
    return render_template("profile.html")

# def retrieve(id):
#     x = patientcol.find({'_id':OjectId(id)})
#     return x

if __name__ == "__main__":
    app.run(debug=True)
