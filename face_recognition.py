import os 
import threading
from db_config import DB_CFG
from tkinter import *
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import mysql.connector
import pickle
from insightface.app import FaceAnalysis
from numpy.linalg import norm
import time
from spoof_detection import SpoofDetector
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


class Face_Recognition:

    def __init__(self, root):

        self.root = root
        self.root.state("zoomed")
        self.root.configure(bg="#0B0F14")

        header = Frame(root, bg="#0F172A", height=60)
        header.pack(fill=X)

        Label(header,
              text="AI FACE AUTHENTICATION",
              font=("Times New Roman", 20, "bold"),
              bg="#0F172A",
              fg="white").pack(pady=15)

        main = Frame(root, bg="#0B0F14")
        main.pack(expand=True)

        self.create_ui(main)

        self.app = FaceAnalysis(name="buffalo_l")
        self.app.prepare(ctx_id=-1, det_size=(640, 640))

        self.THRESHOLD = 0.55

        self.cap = None
        self.current_frame = None
        self.running = False

        self.ai_thread = None
        self.ai_frame_counter = 0
        self.ai_detect_interval = 5

        self.last_detection_time = 0
        self.detection_timeout = 2

        self.known_faces = []
        self.face_boxes = []

        self.spoof_detector = SpoofDetector()

        self.real_frame_streak = 0
        self.required_streak   = 3

        self.failed_attempts = 0
        self.max_attempts = 3

        # ── Smile liveness check ──────────────────────────────────────────
        self.smile_timer_started = False
        self.smile_start_time    = 0
        self.smile_hold_seconds  = 2        # how long the user must hold the smile

    def rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
                x2, y2-r*1.4, x2, y2, x2-r*1.4, y2,
                x1+r, y2, x1, y2, x1, y2-r,
                x1, y1+r, x1, y1]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def create_ui(self, parent):

        cam_canvas = Canvas(parent, width=700, height=520,
                            bg="#0B0F14", highlightthickness=0)
        cam_canvas.pack(side=LEFT, padx=40)
        self.rounded_rect(cam_canvas, 0, 0, 700, 520, 40, fill="#111827")
        self.camera_label = Label(cam_canvas, bg="#111827")
        cam_canvas.create_window(350, 260, window=self.camera_label)

        card_canvas = Canvas(parent, width=350, height=500,
                             bg="#0B0F14", highlightthickness=0)
        card_canvas.pack(side=RIGHT, padx=40)
        self.rounded_rect(card_canvas, 8, 10, 358, 510, 30, fill="#CBD5E1")
        self.rounded_rect(card_canvas, 0, 0, 350, 500, 30, fill="#F8FAFC")

        main_font = ("Times New Roman", 16, "bold")

        name_canvas = Canvas(card_canvas, width=300, height=40,
                             bg="#F8FAFC", highlightthickness=0)
        self.rounded_rect(name_canvas, 0, 0, 300, 40, 15, fill="#E2E8F0")
        self.name_label = Label(name_canvas, text="Name: -",
                                font=main_font, bg="#E2E8F0")
        name_canvas.create_window(150, 20, window=self.name_label)
        card_canvas.create_window(175, 80, window=name_canvas)

        id_canvas = Canvas(card_canvas, width=300, height=40,
                           bg="#F8FAFC", highlightthickness=0)
        self.rounded_rect(id_canvas, 0, 0, 300, 40, 15, fill="#E2E8F0")
        self.id_label = Label(id_canvas, text="Candidate ID: -",
                              font=main_font, bg="#E2E8F0")
        id_canvas.create_window(150, 20, window=self.id_label)
        card_canvas.create_window(175, 135, window=id_canvas)

        status_canvas = Canvas(card_canvas, width=240, height=50,
                               bg="#F8FAFC", highlightthickness=0)
        self.status_bg = self.rounded_rect(status_canvas, 0, 0, 240, 50, 20, fill="#DCFCE7")
        self.status_label = Label(status_canvas,
                                  text="Look at camera",
                                  font=("Times New Roman", 14, "bold"),
                                  bg="#DCFCE7", fg="#166534")
        status_canvas.create_window(120, 25, window=self.status_label)
        card_canvas.create_window(175, 210, window=status_canvas)
        self.status_canvas = status_canvas

        attempt_canvas = Canvas(card_canvas, width=240, height=35,
                                bg="#F8FAFC", highlightthickness=0)
        self.attempt_bg = self.rounded_rect(attempt_canvas, 0, 0, 240, 35, 15, fill="#F1F5F9")
        self.attempt_label = Label(attempt_canvas,
                                   text="Attempts: 0 / 3",
                                   font=("Times New Roman", 12, "bold"),
                                   bg="#F1F5F9", fg="#64748B")
        attempt_canvas.create_window(120, 17, window=self.attempt_label)
        card_canvas.create_window(175, 270, window=attempt_canvas)
        self.attempt_canvas = attempt_canvas

        def create_rounded_button(text, y, color, command):
            btn_canvas = Canvas(card_canvas, width=260, height=45,
                                bg="#F8FAFC", highlightthickness=0)

            rect = self.rounded_rect(btn_canvas, 0, 0, 260, 45, 20, fill=color)
            btn_canvas.create_text(130, 22, text=text, fill="white",
                                   font=("Times New Roman", 14, "bold"))

            hover_color = {
                "#3B82F6": "#2563EB",
                "#EF4444": "#DC2626",
            }.get(color, color)

            def on_enter(e):
                btn_canvas.itemconfig(rect, fill=hover_color)
                btn_canvas.configure(cursor="hand2")

            def on_leave(e):
                btn_canvas.itemconfig(rect, fill=color)
                btn_canvas.configure(cursor="")

            btn_canvas.bind("<Enter>", on_enter)
            btn_canvas.bind("<Leave>", on_leave)
            btn_canvas.bind("<Button-1>", lambda e: command())

            card_canvas.create_window(175, y, window=btn_canvas)

        create_rounded_button("START AUTHENTICATION", 350, "#3B82F6", self.start_camera)
        create_rounded_button("STOP AUTHENTICATION",  415, "#EF4444", self.stop_camera)

    def clear_identity(self):
        self.name_label.config(text="Name: -")
        self.id_label.config(text="Candidate ID: -")
        self.last_detection_time = 0

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (norm(a) * norm(b))

    def load_db(self):
        try:
            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()
            cur.execute("SELECT candidate_id, name, phone, email, face_embedding FROM student")
            rows = cur.fetchall()
            conn.close()
            faces = []
            for cid, name, phone, email, emb in rows:
                if emb:
                    faces.append({
                        "id": cid,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "embedding": pickle.loads(emb)
                    })
            print(f"Loaded {len(faces)} face(s) from database")
            return faces
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            self.root.after(0, self.update_status, f"DB Error: {e}", True, False)
            return []

    def log_verification(self, candidate_id, name, status):
        """Write a verification result to the verification_log table (non-blocking)."""
        def _write():
            try:
                conn = mysql.connector.connect(**DB_CFG)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO verification_log (candidate_id, name, status) VALUES (%s, %s, %s)",
                    (candidate_id, name, status)
                )
                conn.commit()
                conn.close()
                print(f"Verification logged: {candidate_id} | {name} | {status}")
            except mysql.connector.Error as e:
                print(f"Verification log error: {e}")
        threading.Thread(target=_write, daemon=True).start()

    def generate_reports(self):
        threading.Thread(target=self._build_reports, daemon=True).start()

    def _build_reports(self):
        try:
            style = getSampleStyleSheet()

            conn = mysql.connector.connect(**DB_CFG)
            cur = conn.cursor()

            # ── Fetch ALL verified sessions (not just latest per candidate) ──
            cur.execute("""
                SELECT v.candidate_id, v.name, v.timestamp
                FROM verification_log v
                WHERE v.status = 'VERIFIED'
                ORDER BY v.timestamp DESC
            """)
            verified_rows = cur.fetchall()
            extras = {}
            if verified_rows:
                cids = list({r[0] for r in verified_rows})
                fmt  = ",".join(["%s"] * len(cids))
                cur.execute(
                    f"SELECT candidate_id, phone, email FROM student WHERE candidate_id IN ({fmt})",
                    cids
                )
                extras = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

            # ── Fetch ALL declined sessions ──────────────────────────────────
            cur.execute("""
                SELECT candidate_id, name, timestamp
                FROM verification_log
                WHERE status = 'DECLINED'
                ORDER BY timestamp DESC
            """)
            declined_rows = cur.fetchall()
            conn.close()

            # ── Authenticated Report ─────────────────────────────────────────
            doc = SimpleDocTemplate("authenticated_report.pdf", pagesize=A4)
            elements = []
            elements.append(Paragraph("<b>Authenticated Candidates</b>", style["Title"]))
            elements.append(Spacer(1, 20))

            data = [["Name", "Candidate ID", "Phone", "Email", "Time Authenticated"]]
            for cid, name, ts in verified_rows:
                phone, email = extras.get(cid, ("-", "-"))
                # Format timestamp nicely e.g. "24 Feb 2026, 08:45:12"
                ts_str = ts.strftime("%d %b %Y, %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
                data.append([name, str(cid), str(phone or "-"), email or "-", ts_str])

            col_widths = [110, 100, 80, 130, 110]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
                ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS',(0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F1F5F9")])
            ]))
            elements.append(table)
            doc.build(elements)

            # ── Declined Report ──────────────────────────────────────────────
            doc2 = SimpleDocTemplate("declined_report.pdf", pagesize=A4)
            elements2 = []
            elements2.append(Paragraph("<b>Declined / Locked Candidates</b>", style["Title"]))
            elements2.append(Spacer(1, 20))
            if declined_rows:
                data2 = [["Name / Note", "Candidate ID", "Declined At"]]
                for cid, name, ts in declined_rows:
                    ts_str = ts.strftime("%d %b %Y, %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
                    data2.append([name, str(cid), ts_str])

                col_widths2 = [180, 120, 150]
                table2 = Table(data2, colWidths=col_widths2)
                table2.setStyle(TableStyle([
                    ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor("#7F1D1D")),
                    ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
                    ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE',      (0, 0), (-1, -1), 9),
                    ('GRID',          (0, 0), (-1, -1), 1, colors.HexColor("#FECACA")),
                    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS',(0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#FEF2F2")])
                ]))
                elements2.append(table2)
            else:
                elements2.append(Paragraph("No declined records.", style["Normal"]))
            doc2.build(elements2)

            print("Reports updated: authenticated_report.pdf, declined_report.pdf")
        except Exception as e:
            print(f"Report generation error: {e}")

    def start_camera(self):
        if self.running:
            return

        self.known_faces = self.load_db()
        if not self.known_faces:
            self.update_status("No faces in database", error=True)
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.update_status("Camera not available", error=True)
            return

        self.running = True
        self.failed_attempts = 0
        self.real_frame_streak = 0
        self.last_detection_time = 0
        self.face_boxes = []

        # Reset smile state on every fresh start
        self.smile_timer_started = False
        self.smile_start_time    = 0

        self._update_attempt_label()

        if self.ai_thread is None or not self.ai_thread.is_alive():
            self.ai_thread = threading.Thread(target=self.ai_loop, daemon=True)
            self.ai_thread.start()

        self.update_camera()

    def stop_camera(self):
        self.running = False
        self.real_frame_streak  = 0
        self.smile_timer_started = False

        if self.cap:
            self.cap.release()
            self.cap = None

        self.camera_label.config(image="")
        self.camera_label.imgtk = None
        self.name_label.config(text="Name: -")
        self.id_label.config(text="Candidate ID: -")

        self.status_canvas.itemconfig(self.status_bg, fill="#DCFCE7")
        self.status_label.config(text="Look at camera", bg="#DCFCE7", fg="#166534")

        self.attempt_label.config(text="Attempts: 0 / 3")
        self.attempt_canvas.itemconfig(self.attempt_bg, fill="#F1F5F9")
        self.attempt_label.config(bg="#F1F5F9", fg="#64748B")

        self.current_frame = None
        self.ai_thread = None
        self.face_boxes = []

    def update_camera(self):
        if self.running and self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                display_frame = frame.copy()

                for box_data in self.face_boxes:
                    x1, y1, x2, y2, color = box_data
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 3)

                rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)

                if self.last_detection_time > 0:
                    if time.time() - self.last_detection_time > self.detection_timeout:
                        self.update_status("Scanning...", scanning=True)
                        self.last_detection_time = 0

            self.root.after(20, self.update_camera)

    def _update_attempt_label(self):
        self.attempt_label.config(
            text=f"Attempts: {self.failed_attempts} / {self.max_attempts}"
        )
        if self.failed_attempts == 0:
            self.attempt_canvas.itemconfig(self.attempt_bg, fill="#F1F5F9")
            self.attempt_label.config(bg="#F1F5F9", fg="#64748B")
        elif self.failed_attempts == 1:
            self.attempt_canvas.itemconfig(self.attempt_bg, fill="#FEF3C7")
            self.attempt_label.config(bg="#FEF3C7", fg="#92400E")
        else:
            self.attempt_canvas.itemconfig(self.attempt_bg, fill="#FEE2E2")
            self.attempt_label.config(bg="#FEE2E2", fg="#991B1B")

    def ai_loop(self):
        while self.running:

            if self.current_frame is None:
                time.sleep(0.05)
                continue

            self.ai_frame_counter += 1
            if self.ai_frame_counter % self.ai_detect_interval != 0:
                time.sleep(0.05)
                continue

            try:
                orig_height, orig_width = self.current_frame.shape[:2]
                detection_frame = cv2.resize(self.current_frame, (400, 300))
                detect_height, detect_width = detection_frame.shape[:2]

                faces = self.app.get(detection_frame)

                # ── No face ──────────────────────────────────────────────────
                if len(faces) == 0:
                    self.face_boxes = []
                    self.smile_timer_started = False
                    self.root.after(0, self.update_status, "No face detected", False, True)
                    time.sleep(0.05)
                    continue

                # ── Multiple faces ───────────────────────────────────────────
                if len(faces) > 1:
                    boxes = []
                    for f in faces:
                        b = f.bbox.astype(int)
                        bx1 = int(b[0] * orig_width  / detect_width)
                        by1 = int(b[1] * orig_height / detect_height)
                        bx2 = int(b[2] * orig_width  / detect_width)
                        by2 = int(b[3] * orig_height / detect_height)
                        boxes.append((bx1, by1, bx2, by2, (0, 0, 255)))
                    self.face_boxes = boxes
                    self.real_frame_streak   = 0
                    self.smile_timer_started = False
                    self.root.after(0, self.update_status,
                                    f"⚠ {len(faces)} faces detected — 1 person only!",
                                    True, False)
                    self.root.after(0, self.clear_identity)
                    time.sleep(0.05)
                    continue

                face = faces[0]

                # ── Scale bbox to full-resolution ────────────────────────────
                bbox = face.bbox.astype(int)
                scale_x = orig_width  / detect_width
                scale_y = orig_height / detect_height
                x1 = int(bbox[0] * scale_x)
                y1 = int(bbox[1] * scale_y)
                x2 = int(bbox[2] * scale_x)
                y2 = int(bbox[3] * scale_y)

                # ── SMILE LIVENESS CHECK ─────────────────────────────────────
                # Step 1: prompt the user to smile and start the timer
                if not self.smile_timer_started:
                    self.smile_timer_started = True
                    self.smile_start_time    = time.time()
                    self.face_boxes = [(x1, y1, x2, y2, (0, 165, 255))]
                    self.root.after(0, self.update_status,
                                    "😊 Please smile for sometime",
                                    False, True)
                    time.sleep(0.05)
                    continue

                # Step 2: keep waiting until the smile window has elapsed
                elapsed = time.time() - self.smile_start_time
                if elapsed < self.smile_hold_seconds:
                    remaining = int(self.smile_hold_seconds - elapsed) + 1
                    self.face_boxes = [(x1, y1, x2, y2, (0, 165, 255))]
                    self.root.after(0, self.update_status,
                                    f"😊 Hold your smile… {remaining}s",
                                    False, True)
                    time.sleep(0.05)
                    continue

                # Smile window passed — reset for the next attempt
                self.smile_timer_started = False

                # ── Spoof check on full-resolution frame ─────────────────────
                try:
                    is_real = self.spoof_detector.check(
                        self.current_frame, (x1, y1, x2, y2)
                    )
                except RuntimeError as e:
                    print(f"Spoof detection error: {e}")
                    self.face_boxes = [(x1, y1, x2, y2, (0, 0, 255))]
                    self.root.after(0, self.update_status, "⚠ Spoof check failed", True, False)
                    time.sleep(0.05)
                    continue

                if not is_real:
                    self.real_frame_streak = 0
                    self.face_boxes = [(x1, y1, x2, y2, (0, 0, 255))]
                    self.root.after(0, self.update_status, "⚠ Spoof Detected", True, False)
                    self.root.after(0, self.clear_identity)
                    time.sleep(0.05)
                    continue

                # ── Real-frame streak ────────────────────────────────────────
                self.real_frame_streak += 1
                if self.real_frame_streak < self.required_streak:
                    self.face_boxes = [(x1, y1, x2, y2, (0, 165, 255))]
                    self.root.after(0, self.update_status,
                                    f"Verifying… ({self.real_frame_streak}/{self.required_streak})",
                                    False, True)
                    time.sleep(0.05)
                    continue

                self.real_frame_streak = 0

                # ── High-quality embedding from full-res crop ─────────────────
                MARGIN   = 0.2
                crop_x1  = max(0, int(x1 - (x2 - x1) * MARGIN))
                crop_y1  = max(0, int(y1 - (y2 - y1) * MARGIN))
                crop_x2  = min(orig_width,  int(x2 + (x2 - x1) * MARGIN))
                crop_y2  = min(orig_height, int(y2 + (y2 - y1) * MARGIN))
                full_res_crop = self.current_frame[crop_y1:crop_y2, crop_x1:crop_x2]

                hq_faces = self.app.get(full_res_crop)
                hq_embedding = hq_faces[0].embedding if len(hq_faces) > 0 else face.embedding

                # ── Cosine matching ──────────────────────────────────────────
                best       = None
                best_score = 0

                for ref in self.known_faces:
                    score = self.cosine_similarity(ref["embedding"], hq_embedding)
                    if score > best_score:
                        best_score = score
                        best = ref

                if best_score >= self.THRESHOLD:
                    self.face_boxes = [(x1, y1, x2, y2, (0, 255, 0))]
                    self.root.after(0, self.update_ui, best['name'], best['id'], True)
                    self.last_detection_time = time.time()

                    captured_frame = self.current_frame.copy()
                    self.log_verification(best['id'], best['name'], "VERIFIED")
                    self.generate_reports()
                    self.root.after(0, self._handle_success, best, captured_frame)
                    return

                else:
                    self.face_boxes = [(x1, y1, x2, y2, (0, 0, 255))]
                    attempts = self.failed_attempts + 1
                    self.failed_attempts = attempts
                    self.root.after(0, self._update_attempt_label)

                    if attempts >= self.max_attempts:
                        self.log_verification("UNKNOWN", "Unknown", "DECLINED")
                        self.generate_reports()
                        self.root.after(0, self._handle_denied)
                        return
                    else:
                        self.root.after(0, self.update_status,
                                        f"Unknown ({attempts}/{self.max_attempts})",
                                        True, False)

            except Exception as e:
                print(f"AI detection error: {e}")
                self.face_boxes = []

            time.sleep(0.05)

    def _handle_success(self, candidate, captured_frame):
        self.stop_camera()
        self.show_success_screen(candidate["name"], candidate["id"], captured_frame)

    def _handle_denied(self):
        self.stop_camera()
        self.show_access_denied()

    def update_ui(self, name, cid, verified):
        if verified:
            self.name_label.config(text=f"Name: {name}")
            self.id_label.config(text=f"Candidate ID: {cid}")
            self.status_canvas.itemconfig(self.status_bg, fill="#DCFCE7")
            self.status_label.config(text="✔ VERIFIED", bg="#DCFCE7", fg="#166534")
        else:
            self.name_label.config(text="Name: -")
            self.id_label.config(text="Candidate ID: -")

    def update_status(self, text, error=False, scanning=False):
        if error:
            bg_color = "#FEE2E2"
            fg_color = "#991B1B"
        elif scanning:
            bg_color = "#FEF3C7"
            fg_color = "#92400E"
        else:
            bg_color = "#DCFCE7"
            fg_color = "#166534"

        self.status_canvas.itemconfig(self.status_bg, fill=bg_color)
        self.status_label.config(text=text, bg=bg_color, fg=fg_color)

    def show_access_denied(self):
        denied = Toplevel(self.root)
        denied.state("zoomed")
        denied.configure(bg="#0B1120")

        Label(denied,
              text="ACCESS DENIED",
              font=("Times New Roman", 48, "bold"),
              fg="#EF4444",
              bg="#0B1120").pack(pady=120)

        Label(denied,
              text="❌  Maximum attempts reached",
              font=("Times New Roman", 22),
              fg="#CBD5E1",
              bg="#0B1120").pack(pady=10)

        Label(denied,
              text="A report has been generated.",
              font=("Times New Roman", 16),
              fg="#64748B",
              bg="#0B1120").pack(pady=10)

        btn_canvas = Canvas(denied, width=220, height=50,
                            bg="#0B1120", highlightthickness=0)
        btn_canvas.pack(pady=40)
        rect = self.rounded_rect(btn_canvas, 0, 0, 220, 50, 20, fill="#EF4444")
        btn_canvas.create_text(110, 25, text="CLOSE", fill="white",
                               font=("Times New Roman", 16, "bold"))

        def on_enter(e):
            btn_canvas.itemconfig(rect, fill="#DC2626")
            btn_canvas.configure(cursor="hand2")

        def on_leave(e):
            btn_canvas.itemconfig(rect, fill="#EF4444")
            btn_canvas.configure(cursor="")

        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        btn_canvas.bind("<Button-1>", lambda e: denied.destroy())

    def _make_circular(self, image, size=220):
        image = image.resize((size, size))
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        circular = Image.new("RGBA", (size, size))
        circular.paste(image, (0, 0), mask=mask)
        return circular

    def show_success_screen(self, name, cid, captured_frame):
        success = Toplevel(self.root)
        success.state("zoomed")
        success.configure(bg="#0B0F14")

        header = Frame(success, bg="#0F172A", height=60)
        header.pack(fill=X)
        Label(header,
              text="AI FACE AUTHENTICATION",
              font=("Times New Roman", 20, "bold"),
              bg="#0F172A", fg="white").pack(pady=15)

        centre = Frame(success, bg="#0B0F14")
        centre.pack(expand=True)

        photo_card = Canvas(centre, width=360, height=420,
                            bg="#0B0F14", highlightthickness=0)
        photo_card.pack(side=LEFT, padx=40, pady=30)
        self.rounded_rect(photo_card, 8, 10, 368, 430, 35, fill="#1E293B")
        self.rounded_rect(photo_card, 0, 0, 360, 420, 35, fill="#111827")

        photo_card.create_text(180, 38,
                               text="IDENTITY VERIFIED  ✓",
                               font=("Times New Roman", 17, "bold"),
                               fill="#4ADE80")

        rgb = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        circular_img = self._make_circular(img, size=220)
        imgtk = ImageTk.PhotoImage(circular_img)

        photo_card.create_oval(60, 68, 300, 308,
                            outline="#3B82F6", width=6)
        photo_card.create_oval(66, 74, 294, 302,
                            outline="#1E3A5F", width=3)
        photo_card.create_image(180, 188, image=imgtk)
        photo_card.image = imgtk

        photo_card.create_line(40, 328, 320, 328,
                               fill="#1E293B", width=2)

        self.rounded_rect(photo_card, 90, 345, 270, 385, 20, fill="#052E16")
        photo_card.create_text(180, 365,
                               text="✔  AUTHENTICATED",
                               font=("Times New Roman", 13, "bold"),
                               fill="#4ADE80")

        info_card = Canvas(centre, width=380, height=420,
                           bg="#0B0F14", highlightthickness=0)
        info_card.pack(side=RIGHT, padx=40, pady=30)
        self.rounded_rect(info_card, 8, 10, 388, 430, 35, fill="#1E293B")
        self.rounded_rect(info_card, 0, 0, 380, 420, 35, fill="#F8FAFC")

        info_card.create_text(190, 42,
                              text="CANDIDATE DETAILS",
                              font=("Times New Roman", 15, "bold"),
                              fill="#64748B")

        info_card.create_line(40, 65, 340, 65, fill="#E2E8F0", width=2)

        def info_row(canvas, y, label, value, label_color, value_color):
            self.rounded_rect(canvas, 30, y, 350, y + 52, 18, fill="#E2E8F0")
            canvas.create_text(65, y + 16,
                               text=label,
                               font=("Times New Roman", 11, "bold"),
                               fill=label_color, anchor="w")
            canvas.create_text(65, y + 34,
                               text=value,
                               font=("Times New Roman", 14, "bold"),
                               fill=value_color, anchor="w")

        info_row(info_card, 85,  "FULL NAME",     name, "#94A3B8", "#1E293B")
        info_row(info_card, 155, "CANDIDATE ID",  str(cid), "#94A3B8", "#1E293B")

        self.rounded_rect(info_card, 230, 235, 150, 278, 20, fill="#DCFCE7")
        info_card.create_text(90, 256,
                              text="✔  Verified",
                              font=("Times New Roman", 13, "bold"),
                              fill="#166534")

        self.rounded_rect(info_card, 160, 235, 350, 278, 20, fill="#EFF6FF")
        info_card.create_text(255, 256,
                              text="📄  Report Saved",
                              font=("Times New Roman", 13, "bold"),
                              fill="#1D4ED8")

        info_card.create_line(40, 300, 340, 300, fill="#E2E8F0", width=2)

        btn_inner = Canvas(info_card, width=300, height=55,
                           bg="#F8FAFC", highlightthickness=0)
        rect = self.rounded_rect(btn_inner, 0, 0, 300, 55, 22, fill="#2563EB")
        btn_inner.create_text(150, 27,
                              text="➜   PROCEED TO EXAM",
                              fill="white",
                              font=("Times New Roman", 16, "bold"))
        info_card.create_window(190, 360, window=btn_inner)

        def on_enter(e):
            btn_inner.itemconfig(rect, fill="#1E40AF")
            btn_inner.configure(cursor="hand2")

        def on_leave(e):
            btn_inner.itemconfig(rect, fill="#2563EB")
            btn_inner.configure(cursor="")

        def proceed():
            success.destroy()
            self.root.destroy()

        btn_inner.bind("<Enter>", on_enter)
        btn_inner.bind("<Leave>", on_leave)
        btn_inner.bind("<Button-1>", lambda e: proceed())


if __name__ == "__main__":
    root = Tk()
    Face_Recognition(root)
    root.mainloop()