from tkinter import *
from PIL import Image, ImageTk
import os
from student import Student
from face_recognition import Face_Recognition
from reports_viewer import ReportsViewer

class Face_Recognition_System:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1366x768")
        self.root.title("Face Recognition System")
        self.root.configure(bg="#0B0F14")

        # Centre window on screen
        self.root.update_idletasks()
        w, h = 1366, 768
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Keep all icons alive — prevents garbage collection
        self.icons = []

        # PATHS
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.IMG_DIR  = os.path.join(self.BASE_DIR, "img")

        # HEADER
        header = Frame(self.root, bg="#0F172A", height=65)
        header.pack(fill=X)
        Label(
            header,
            text="SECURE PRE-EXAMINATION CANDIDATE AUTHENTICATION",
            font=("times new roman", 20, "bold"),
            bg="#0F172A",
            fg="white"
        ).pack(pady=15)

        # MAIN CONTENT — Row 1: 3 cards, Row 2: 2 cards centred
        content = Frame(self.root, bg="#0B0F14")
        content.pack(expand=True)

        row1 = Frame(content, bg="#0B0F14")
        row1.pack()
        row2 = Frame(content, bg="#0B0F14")
        row2.pack()

        self.create_card(row1, "register.png", "Exam Registration", self.exam_reg,  pack=True)
        self.create_card(row1, "detect.png",   "Face Recognition",  self.face_data, pack=True)
        self.create_card(row1, "dataset.png",  "Open Dataset",      self.open_img,  pack=True)
        self.create_card(row2, "report.jpg",   "View Reports",      self.view_reports, pack=True)
        self.create_card(row2, "exit.png",     "Exit System",       self.exit_app,  pack=True)

        # FOOTER
        Label(
            self.root,
            text="Developed for Secure Candidate Authentication",
            font=("times new roman", 10),
            bg="#0B0F14",
            fg="#9CA3AF"
        ).pack(pady=10)

    # ── LOAD IMAGE ───────────────────────────────────────────
    def load_image(self, name, size):
        path = os.path.join(self.IMG_DIR, name)
        if not os.path.exists(path):
            # Return a blank placeholder instead of crashing
            from PIL import Image as PILImage
            img = PILImage.new("RGBA", size, "#E2E8F0")
        else:
            img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    # ── ROUNDED RECTANGLE ────────────────────────────────────
    def rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    # ── CREATE CARD ──────────────────────────────────────────
    def create_card(self, parent, icon_name, text, command, pack=False, row=0, col=0):
        CARD_WIDTH  = 240
        CARD_HEIGHT = 190
        RADIUS      = 20

        card_canvas = Canvas(
            parent,
            width=CARD_WIDTH, height=CARD_HEIGHT,
            bg="#0B0F14", highlightthickness=0
        )

        if pack:
            card_canvas.pack(side=LEFT, padx=30, pady=30)
        else:
            card_canvas.grid(row=row, column=col, padx=60, pady=45)

        # Card shadow
        self.rounded_rect(
            card_canvas, 4, 4, CARD_WIDTH, CARD_HEIGHT, RADIUS,
            fill="#1E293B"
        )
        # Card face
        self.rounded_rect(
            card_canvas, 0, 0, CARD_WIDTH-4, CARD_HEIGHT-4, RADIUS,
            fill="#F8FAFC", outline="#CBD5E1"
        )

        # Icon
        icon = self.load_image(icon_name, (56, 56))
        self.icons.append(icon)
        card_canvas.create_image(CARD_WIDTH // 2 - 2, 62, image=icon)

        # Rounded button via canvas
        btn_canvas = Canvas(card_canvas, width=CARD_WIDTH - 50, height=36,
                            bg="#F8FAFC", highlightthickness=0)
        btn_rect = self.rounded_rect(btn_canvas, 0, 0, CARD_WIDTH - 50, 36,
                                     14, fill="#3B82F6")
        btn_canvas.create_text((CARD_WIDTH - 50) // 2, 18,
                               text=text, fill="white",
                               font=("times new roman", 12, "bold"))
        card_canvas.create_window(CARD_WIDTH // 2 - 2, 148, window=btn_canvas)

        def on_enter(e):
            btn_canvas.itemconfig(btn_rect, fill="#2563EB")
            btn_canvas.configure(cursor="hand2")

        def on_leave(e):
            btn_canvas.itemconfig(btn_rect, fill="#3B82F6")
            btn_canvas.configure(cursor="")

        btn_canvas.bind("<Enter>", on_enter)
        btn_canvas.bind("<Leave>", on_leave)
        btn_canvas.bind("<Button-1>", lambda e: command())

    # ── ACTIONS ──────────────────────────────────────────────
    def open_img(self):
        import subprocess, sys
        path = os.path.join(self.BASE_DIR, "dataset")
        os.makedirs(path, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def exam_reg(self):
        Student(Toplevel(self.root))

    def face_data(self):
        Face_Recognition(Toplevel(self.root))

    def view_reports(self):
        ReportsViewer(Toplevel(self.root))

    def exit_app(self):
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    Face_Recognition_System(root)
    root.mainloop()