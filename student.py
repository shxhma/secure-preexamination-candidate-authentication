from db_config import DB_CFG
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import mysql.connector
import cv2
import os
import pickle
import re
from insightface.app import FaceAnalysis
from PIL import Image, ImageTk
from photo_validator import PhotoValidator
import numpy as np
import datetime

class Student:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg="#0B0F14")
        self.root.state("zoomed")
        self.photo_path = None
        self.temp_photo_preview = None 
        self.photo_validator = PhotoValidator()

        self.dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")
        os.makedirs(self.dataset_dir, exist_ok=True)

        self.var_dep = StringVar()
        self.var_course = StringVar()
        self.var_exam_year = StringVar()
        self.var_exam_session = StringVar()
        self.var_candidate_id = StringVar()
        self.var_name = StringVar()
        self.var_email = StringVar()
        self.var_phone = StringVar()
        self.var_exam_center = StringVar()

        header = Frame(self.root, bg="#0F172A", height=65)
        header.pack(fill=X)

        Label(
            header,
            text="STUDENT EXAM REGISTRATION",
            font=("times new roman", 20, "bold"),
            bg="#0F172A",
            fg="white"
        ).pack(pady=15)

        main_frame = Frame(self.root, bg="#0B0F14")
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        left_frame = LabelFrame(
            main_frame,
            text="Candidate Details",
            font=("times new roman", 12, "bold"),
            bg="#F8FAFC",
            fg="black"
        )
        left_frame.place(x=10, y=10, width=720, height=680)

        exam_frame = LabelFrame(left_frame, text="Exam Information",
                                font=("times new roman", 12, "bold"), 
                                bg="white", fg="#1e3a8a", bd=2, relief=GROOVE)
        exam_frame.place(x=10, y=10, width=690, height=140)

        ttk.Label(exam_frame, text="Department").grid(row=0, column=0, padx=10, pady=8, sticky=W)
        ttk.Combobox(exam_frame, textvariable=self.var_dep,
                     values=["CSE", "CS", "IOT", "AIDS"],
                     state="readonly", width=18).grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(exam_frame, text="Course").grid(row=0, column=2, padx=10, pady=8, sticky=W)
        ttk.Combobox(exam_frame, textvariable=self.var_course,
                     values=["B.Tech", "M.Tech"],
                     state="readonly", width=18).grid(row=0, column=3, padx=10, pady=8)

        ttk.Label(exam_frame, text="Exam Year").grid(row=1, column=0, padx=10, pady=8, sticky=W)
        ttk.Combobox(exam_frame, textvariable=self.var_exam_year,
                     values=[str(datetime.date.today().year + i) for i in range(3)],
                     state="readonly", width=18).grid(row=1, column=1, padx=10, pady=8)

        ttk.Label(exam_frame, text="Session").grid(row=1, column=2, padx=10, pady=8, sticky=W)
        ttk.Combobox(exam_frame, textvariable=self.var_exam_session,
                     values=["Forenoon", "Afternoon"],
                     state="readonly", width=18).grid(row=1, column=3, padx=10, pady=8)

        info_frame = LabelFrame(left_frame, text="Candidate Identification",
                                font=("times new roman", 12, "bold"), 
                                bg="white", fg="#1e3a8a", bd=2, relief=GROOVE)
        info_frame.place(x=10, y=160, width=690, height=220)

        labels = ["Candidate ID", "Name", "Email", "Phone", "Exam Center"]
        vars_ = [self.var_candidate_id, self.var_name,
                 self.var_email, self.var_phone, self.var_exam_center]

        for i, (lbl, var) in enumerate(zip(labels, vars_)):
            ttk.Label(info_frame, text=lbl).grid(row=i, column=0, padx=10, pady=8, sticky=W)
            ttk.Entry(info_frame, textvariable=var, width=40).grid(row=i, column=1, padx=10, pady=8)

        photo_frame = LabelFrame(left_frame, text="Candidate Photo",
                                 font=("times new roman", 12, "bold"), 
                                 bg="white", fg="#1e3a8a", bd=2, relief=GROOVE)
        photo_frame.place(x=10, y=390, width=690, height=200)

        self.btn_upload = Button(
            photo_frame,
            text="Upload Photo",
            command=self.upload_photo,
            bg="#2ecc71",
            fg="white",
            font=("times new roman", 12, "bold"),
            cursor="hand2",
            relief=RAISED,
            bd=2
        )
        self.btn_upload.place(x=30, y=60, width=220, height=45)
        
        Label(
            photo_frame,
            text="📋 Photo must contain exactly ONE face",
            font=("times new roman", 9),
            bg="white",
            fg="#6b7280"
        ).place(x=30, y=115)

        self.preview_label = Label(
            photo_frame,
            bg="#f3f4f6",
            relief=SOLID,
            bd=2,
            text="No Photo",
            font=("times new roman", 10),
            fg="#9ca3af"
        )
        self.preview_label.place(x=300, y=20, width=150, height=150)

        btn_frame = Frame(left_frame, bg="white")
        btn_frame.place(x=10, y=610, width=690, height=60)

        btn_register = Button(
            btn_frame, text="Register", command=self.add_data,
            width=15, bg="#3B82F6", activebackground="#2563EB", fg="white",
            font=("times new roman", 11, "bold"), cursor="hand2",
            relief=RAISED, bd=2
        )
        btn_register.grid(row=0, column=0, padx=5, pady=10)
        btn_register.bind("<Enter>", lambda e: btn_register.config(bg="#2563EB"))
        btn_register.bind("<Leave>", lambda e: btn_register.config(bg="#3B82F6"))
        
        btn_update = Button(
            btn_frame, text="Update", command=self.update_data,
            width=15, bg="#3B82F6", activebackground="#2563EB", fg="white",
            font=("times new roman", 11, "bold"), cursor="hand2",
            relief=RAISED, bd=2
        )
        btn_update.grid(row=0, column=1, padx=5, pady=10)
        btn_update.bind("<Enter>", lambda e: btn_update.config(bg="#2563EB"))
        btn_update.bind("<Leave>", lambda e: btn_update.config(bg="#3B82F6"))
        
        btn_delete = Button(
            btn_frame, text="Delete", command=self.delete_data,
            width=15, bg="#dc3545", activebackground="#c82333", fg="white",
            font=("times new roman", 11, "bold"), cursor="hand2",
            relief=RAISED, bd=2
        )
        btn_delete.grid(row=0, column=2, padx=5, pady=10)
        btn_delete.bind("<Enter>", lambda e: btn_delete.config(bg="#c82333"))
        btn_delete.bind("<Leave>", lambda e: btn_delete.config(bg="#dc3545"))
        
        btn_clear = Button(
            btn_frame, text="Clear", command=self.clear_fields,
            width=15, bg="#6c757d", activebackground="#5a6268", fg="white",
            font=("times new roman", 11, "bold"), cursor="hand2",
            relief=RAISED, bd=2
        )
        btn_clear.grid(row=0, column=3, padx=5, pady=10)
        btn_clear.bind("<Enter>", lambda e: btn_clear.config(bg="#5a6268"))
        btn_clear.bind("<Leave>", lambda e: btn_clear.config(bg="#6c757d"))

        right_frame = LabelFrame(main_frame, text="Registered Candidates",
                                 font=("times new roman", 12, "bold"), bg="#F8FAFC")
        right_frame.place(x=750, y=10, width=730, height=680)

        table_frame = Frame(right_frame, bd=2, relief=RIDGE)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        scroll_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        scroll_y = ttk.Scrollbar(table_frame, orient=VERTICAL)

        self.student_table = ttk.Treeview(
            table_frame,
            columns=("id", "name", "dep", "course", "year",
                     "session", "email", "phone", "center", "photo"),
            show="headings",
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set
        )

        scroll_x.pack(side=BOTTOM, fill=X)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.config(command=self.student_table.xview)
        scroll_y.config(command=self.student_table.yview)

        headings = ["ID", "Name", "Dept", "Course", "Year",
                    "Session", "Email", "Phone", "Center", "Photo"]

        column_widths = {
            "id": 80,
            "name": 150,
            "dep": 60,
            "course": 70,
            "year": 50,
            "session": 90,
            "email": 180,
            "phone": 100,
            "center": 120,
            "photo": 80
        }

        for col, head in zip(self.student_table["columns"], headings):
            self.student_table.heading(col, text=head)
            self.student_table.column(col, anchor=CENTER, width=column_widths[col], stretch=True)

        self.student_table.pack(fill=BOTH, expand=1)
        self.student_table.bind("<ButtonRelease-1>", self.get_cursor)

        self.fetch_data()

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_phone(self, phone):
        """Validate phone number (10 digits)"""
        pattern = r'^\d{10}$'
        return re.match(pattern, phone) is not None

    def validate_fields(self):
        """Validate all input fields"""
        if not self.var_candidate_id.get().strip():
            raise ValueError("Candidate ID is required")
        
        if not self.var_name.get().strip():
            raise ValueError("Name is required")
        
        if not self.var_dep.get():
            raise ValueError("Please select a Department")
        
        if not self.var_course.get():
            raise ValueError("Please select a Course")
        
        if not self.var_exam_year.get():
            raise ValueError("Please select an Exam Year")
        
        if not self.var_exam_session.get():
            raise ValueError("Please select a Session")
        
        if not self.var_email.get().strip():
            raise ValueError("Email is required")
        
        if not self.var_phone.get().strip():
            raise ValueError("Phone number is required")
        
        if not self.var_exam_center.get().strip():
            raise ValueError("Exam Center is required")
        
        if not self.photo_path:
            raise ValueError("Please upload a photo")

        if not self.validate_email(self.var_email.get().strip()):
            raise ValueError("Invalid email format (e.g., example@domain.com)")
        
        if not self.validate_phone(self.var_phone.get().strip()):
            raise ValueError("Phone number must be exactly 10 digits")

        return True

    def upload_photo(self):
        """Upload and preview photo (not saved to dataset yet)"""
        path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if not path:
            return

        self.photo_path = path

        self.btn_upload.config(
            text="Photo Selected ✔",
            bg="#27ae60"
        )

        try:
            img = Image.open(self.photo_path)
            img = img.resize((140, 140))
            self.temp_photo_preview = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.temp_photo_preview, text="", bg="white")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.photo_path = None
            self.btn_upload.config(text="Upload Photo", bg="#2ecc71")

    def validate_and_save_photo(self, cid, ask_update=True):
        if not self.photo_path:
            raise ValueError("Please upload a photo")

        face = self.photo_validator.validate(self.photo_path)

        if self.check_duplicate_face(face.embedding, cid):
            raise ValueError("This face is already registered with another candidate.")

        img = cv2.imread(self.photo_path)
        save_path = os.path.abspath(os.path.join(self.dataset_dir, f"{cid}.jpg"))

        if os.path.exists(save_path) and ask_update:
            choice = messagebox.askyesno(
                "Photo Exists",
                f"Photo for Candidate {cid} already exists.\n\nDo you want to UPDATE it?"
            )
            if not choice:
                raise ValueError("Photo upload cancelled")

        cv2.imwrite(save_path, img)

        return save_path, pickle.dumps(face.embedding)

    def add_data(self):
        """Register a new candidate"""
        try:
            self.validate_fields()

            cid = self.var_candidate_id.get().strip()
            
            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT candidate_id FROM student WHERE candidate_id=%s", (cid,))
            if cur.fetchone():
                conn.close()
                raise ValueError(f"Candidate ID '{cid}' already exists. Please use a different ID.")

            photo_path, emb = self.validate_and_save_photo(cid)

            cur.execute("""
                INSERT INTO student 
                (candidate_id, name, department, course, exam_year, exam_session, 
                 email, phone, exam_center, photo_path, face_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cid, 
                self.var_name.get().strip(), 
                self.var_dep.get(), 
                self.var_course.get(),
                self.var_exam_year.get(), 
                self.var_exam_session.get(), 
                self.var_email.get().strip(),
                self.var_phone.get().strip(), 
                self.var_exam_center.get().strip(), 
                photo_path, 
                emb
            ))

            conn.commit()
            conn.close()
            
            self.fetch_data()
            self.clear_fields()
            messagebox.showinfo("Success", f"Candidate {cid} registered successfully!")

        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Database error: {str(db_err)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def update_data(self):
        """Update existing candidate data"""
        try:
            self.validate_fields()

            cid = self.var_candidate_id.get().strip()
            
            photo_path, emb = self.validate_and_save_photo(cid, ask_update=False)

            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("""
                UPDATE student SET
                name=%s, department=%s, course=%s, exam_year=%s,
                exam_session=%s, email=%s, phone=%s,
                exam_center=%s, photo_path=%s, face_embedding=%s
                WHERE candidate_id=%s
            """, (
                self.var_name.get().strip(), 
                self.var_dep.get(),
                self.var_course.get(), 
                self.var_exam_year.get(),
                self.var_exam_session.get(), 
                self.var_email.get().strip(),
                self.var_phone.get().strip(), 
                self.var_exam_center.get().strip(),
                photo_path, 
                emb, 
                cid
            ))
            
            if cur.rowcount == 0:
                conn.close()
                raise ValueError(f"Candidate ID '{cid}' not found in database")
            
            conn.commit()
            conn.close()
            
            self.fetch_data()
            self.clear_fields()
            messagebox.showinfo("Success", f"Candidate {cid} updated successfully!")

        except ValueError as ve:
            messagebox.showerror("Validation Error", str(ve))
        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Database error: {str(db_err)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def delete_data(self):
        """Delete a candidate"""
        try:
            cid = self.var_candidate_id.get().strip()

            if not cid:
                messagebox.showerror("Error", "Please select a candidate to delete")
                return

            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete Candidate {cid}?\n\nThis will also delete their photo from the dataset."
            )

            if not confirm:
                return

            photo_path = os.path.join(self.dataset_dir, f"{cid}.jpg")
            if os.path.exists(photo_path):
                os.remove(photo_path)

            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("DELETE FROM student WHERE candidate_id=%s", (cid,))
            
            if cur.rowcount == 0:
                conn.close()
                messagebox.showwarning("Warning", f"Candidate ID '{cid}' not found in database")
                return
            
            conn.commit()
            conn.close()

            self.fetch_data()
            self.clear_fields()

            messagebox.showinfo("Success", f"Candidate {cid} deleted successfully!")

        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Database error: {str(db_err)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def clear_fields(self):
        """Clear all input fields and reset form"""
        self.var_candidate_id.set("")
        self.var_name.set("")
        self.var_dep.set("")
        self.var_course.set("")
        self.var_exam_year.set("")
        self.var_exam_session.set("")
        self.var_email.set("")
        self.var_phone.set("")
        self.var_exam_center.set("")
        
        self.photo_path = None
        self.temp_photo_preview = None
        
        self.btn_upload.config(text="Upload Photo", bg="#2ecc71")
        self.preview_label.config(image="", text="No Photo", fg="#9ca3af", bg="#f3f4f6")

    def fetch_data(self):
        """Fetch all candidates from database"""
        try:
            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("""
                SELECT candidate_id, name, department, course, exam_year,
                       exam_session, email, phone, exam_center, photo_path
                FROM student
            """)
            rows = cur.fetchall()

            self.student_table.delete(*self.student_table.get_children())

            for row in rows:
                row_list = list(row)
                photo_path = row_list[9]  

                if photo_path and os.path.exists(photo_path):
                    row_list[9] = "✓ Uploaded"
                else:
                    row_list[9] = "✗ Missing"

                self.student_table.insert("", END, values=row_list)

            conn.close()
        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Failed to fetch data: {str(db_err)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def check_duplicate_face(self, new_embedding, current_cid=None):
        conn = mysql.connector.connect(**DB_CFG)
        cur = conn.cursor()
        if current_cid:
            cur.execute(
                "SELECT candidate_id, face_embedding FROM student WHERE candidate_id != %s",
                (current_cid,)
            )
        else:
            cur.execute("SELECT candidate_id, face_embedding FROM student")


        rows = cur.fetchall()
        conn.close()

        for row in rows:
            emb = row[1]
            if emb is None:
                continue

            stored_embedding = pickle.loads(emb)

            similarity = np.dot(new_embedding, stored_embedding) / (
                np.linalg.norm(new_embedding) * np.linalg.norm(stored_embedding)
            )

            if similarity > 0.75: 
                return True

        return False

    def get_cursor(self, event):
        """Load selected candidate data into form"""
        try:
            cursor_row = self.student_table.focus()
            if not cursor_row:
                return
            
            content = self.student_table.item(cursor_row)
            data = content["values"]
            
            if not data:
                return

            cid = data[0]
            
            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("""
                SELECT candidate_id, name, department, course, exam_year,
                    exam_session, email, phone, exam_center, photo_path
                FROM student WHERE candidate_id=%s
            """, (cid,))
            db_row = cur.fetchone()
            conn.close()
            
            if not db_row:
                return

            self.var_candidate_id.set(db_row[0])
            self.var_name.set(db_row[1])
            self.var_dep.set(db_row[2])
            self.var_course.set(db_row[3])
            self.var_exam_year.set(db_row[4])
            self.var_exam_session.set(db_row[5])
            self.var_email.set(db_row[6])
            self.var_phone.set(db_row[7])
            self.var_exam_center.set(db_row[8])
            
            photo_path = db_row[9]
            self.photo_path = photo_path
            
            self.btn_upload.config(text="Change Photo", bg="#f39c12")

            if photo_path and os.path.exists(photo_path):
                img = Image.open(photo_path)
                img = img.resize((140, 140))
                self.temp_photo_preview = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.temp_photo_preview, text="", bg="white")
            else:
                self.preview_label.config(image="", text="Photo Missing", fg="red", bg="#fee2e2")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load candidate data: {str(e)}")


if __name__ == "__main__":
    root = Tk()
    Student(root)
    root.mainloop()