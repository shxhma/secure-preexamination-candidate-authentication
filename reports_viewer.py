from db_config import DB_CFG
from tkinter import *
from tkinter import ttk, messagebox
import mysql.connector
import subprocess
import os
import sys

class ReportsViewer:

    def __init__(self, root):
        self.root = root
        self.root.state("zoomed")
        self.root.configure(bg="#0B0F14")

        header = Frame(self.root, bg="#0F172A", height=65)
        header.pack(fill=X)
        Label(header,
              text="AUTHENTICATION REPORTS",
              font=("Times New Roman", 20, "bold"),
              bg="#0F172A", fg="white").pack(pady=15)

        self.summary_frame = Frame(self.root, bg="#0B0F14")
        self.summary_frame.pack(fill=X, padx=40, pady=(20, 0))

        self.total_lbl  = self._summary_pill(self.summary_frame, "Total Sessions", "0", "#1E293B", "#94A3B8")
        self.pass_lbl   = self._summary_pill(self.summary_frame, "Verified",       "0", "#052E16", "#4ADE80")
        self.fail_lbl   = self._summary_pill(self.summary_frame, "Declined",       "0", "#450A0A", "#F87171")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TNotebook",
                        background="#0B0F14", borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background="#1E293B", foreground="#94A3B8",
                        font=("Times New Roman", 12, "bold"),
                        padding=[20, 8])
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", "#3B82F6")],
                  foreground=[("selected", "white")])

        nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        nb.pack(fill=BOTH, expand=True, padx=40, pady=20)

        all_frame = Frame(nb, bg="#111827")
        nb.add(all_frame, text="  📋  All Sessions  ")

        pass_frame = Frame(nb, bg="#111827")
        nb.add(pass_frame, text="  ✔  Verified  ")

        fail_frame = Frame(nb, bg="#111827")
        nb.add(fail_frame, text="  ✘  Declined  ")

        cols_all  = ("id", "candidate_id", "name", "status", "timestamp")
        heads_all = ("Log ID", "Candidate ID", "Name", "Status", "Timestamp")
        widths_all = (60, 130, 200, 100, 180)

        cols_pass  = ("id", "candidate_id", "name", "timestamp")
        heads_pass = ("Log ID", "Candidate ID", "Name", "Timestamp")
        widths_pass = (60, 130, 220, 200)

        cols_fail  = ("id", "candidate_id", "name", "timestamp")
        heads_fail = ("Log ID", "Candidate ID", "Name/Note", "Timestamp")
        widths_fail = (60, 130, 220, 200)

        self.tree_all  = self._build_table(all_frame,  cols_all,  heads_all,  widths_all)
        self.tree_pass = self._build_table(pass_frame, cols_pass, heads_pass, widths_pass)
        self.tree_fail = self._build_table(fail_frame, cols_fail, heads_fail, widths_fail)

        btn_bar = Frame(self.root, bg="#0B0F14")
        btn_bar.pack(fill=X, padx=40, pady=(0, 20))

        self._rounded_btn(btn_bar, "🔄  Refresh",        "#3B82F6", "#2563EB", self.load_data,        side=LEFT)
        self._rounded_btn(btn_bar, "📄  Open Auth PDF",  "#059669", "#047857", self._open_auth_pdf,   side=LEFT)
        self._rounded_btn(btn_bar, "📄  Open Declined PDF", "#7C3AED", "#6D28D9", self._open_declined_pdf, side=LEFT)
        self._rounded_btn(btn_bar, "🗑  Clear All Logs", "#EF4444", "#DC2626", self._clear_logs,      side=RIGHT)

        self.load_data()

    def rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
                  x2, y2-r*1.4, x2, y2, x2-r*1.4, y2,
                  x1+r, y2, x1, y2, x1, y2-r,
                  x1, y1+r, x1, y1]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _summary_pill(self, parent, label, value, bg, fg):
        c = Canvas(parent, width=200, height=70,
                   bg="#0B0F14", highlightthickness=0)
        c.pack(side=LEFT, padx=10)
        self.rounded_rect(c, 0, 0, 200, 70, 18, fill=bg)
        c.create_text(100, 22, text=label,
                      font=("Times New Roman", 11), fill="#64748B")
        val_id = c.create_text(100, 48, text=value,
                               font=("Times New Roman", 22, "bold"), fill=fg)
        return (c, val_id)

    def _update_pill(self, pill, value):
        canvas, item_id = pill
        canvas.itemconfig(item_id, text=str(value))

    def _build_table(self, parent, cols, heads, widths):
        style = ttk.Style()
        style.configure("Dark.Treeview",
                        background="#1E293B",
                        foreground="#CBD5E1",
                        fieldbackground="#1E293B",
                        rowheight=32,
                        font=("Times New Roman", 12))
        style.configure("Dark.Treeview.Heading",
                        background="#0F172A",
                        foreground="white",
                        font=("Times New Roman", 12, "bold"))
        style.map("Dark.Treeview",
                  background=[("selected", "#3B82F6")],
                  foreground=[("selected", "white")])

        frame = Frame(parent, bg="#111827")
        frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

        sy = ttk.Scrollbar(frame, orient=VERTICAL)
        sx = ttk.Scrollbar(frame, orient=HORIZONTAL)

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            style="Dark.Treeview",
                            yscrollcommand=sy.set,
                            xscrollcommand=sx.set)

        sy.config(command=tree.yview)
        sx.config(command=tree.xview)
        sy.pack(side=RIGHT, fill=Y)
        sx.pack(side=BOTTOM, fill=X)
        tree.pack(fill=BOTH, expand=True)

        for col, head, w in zip(cols, heads, widths):
            tree.heading(col, text=head)
            tree.column(col, anchor=CENTER, width=w, stretch=True)

        tree.tag_configure("even", background="#1E293B")
        tree.tag_configure("odd",  background="#0F172A")
        tree.tag_configure("verified", foreground="#4ADE80")
        tree.tag_configure("declined", foreground="#F87171")

        return tree

    def _rounded_btn(self, parent, text, color, hover, command, side=LEFT):
        c = Canvas(parent, width=200, height=42,
                   bg="#0B0F14", highlightthickness=0)
        c.pack(side=side, padx=8)
        rect = self.rounded_rect(c, 0, 0, 200, 42, 18, fill=color)
        c.create_text(100, 21, text=text, fill="white",
                      font=("Times New Roman", 12, "bold"))

        def on_enter(e):
            c.itemconfig(rect, fill=hover)
            c.configure(cursor="hand2")

        def on_leave(e):
            c.itemconfig(rect, fill=color)
            c.configure(cursor="")

        c.bind("<Enter>", on_enter)
        c.bind("<Leave>", on_leave)
        c.bind("<Button-1>", lambda e: command())

    def load_data(self):
        try:
            conn = mysql.connector.connect(**DB_CFG)
            cur  = conn.cursor()
            cur.execute("""
                SELECT id, candidate_id, name, status, timestamp
                FROM verification_log
                ORDER BY timestamp DESC
            """)
            rows = cur.fetchall()
            conn.close()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", str(e))
            return

        # Rows are already sorted by timestamp DESC, so the first occurrence
        # of each candidate_id is their most recent session — keep that only.
        seen = set()
        unique_rows = []
        for row in rows:
            log_id, cid, name, status, ts = row
            if cid not in seen:
                seen.add(cid)
                unique_rows.append(row)

        for tree in (self.tree_all, self.tree_pass, self.tree_fail):
            tree.delete(*tree.get_children())

        total = len(unique_rows)
        verified_count = 0
        declined_count = 0

        for i, row in enumerate(unique_rows):
            log_id, cid, name, status, ts = row
            tag = "even" if i % 2 == 0 else "odd"
            status_tag = "verified" if status == "VERIFIED" else "declined"

            self.tree_all.insert("", END,
                                 values=(log_id, cid, name, status, ts),
                                 tags=(tag, status_tag))

            if status == "VERIFIED":
                verified_count += 1
                self.tree_pass.insert("", END,
                                      values=(log_id, cid, name, ts),
                                      tags=(tag, "verified"))
            else:
                declined_count += 1
                self.tree_fail.insert("", END,
                                      values=(log_id, cid, name, ts),
                                      tags=(tag, "declined"))

        self._update_pill(self.total_lbl, total)
        self._update_pill(self.pass_lbl,  verified_count)
        self._update_pill(self.fail_lbl,  declined_count)

    def generate_reports(self):
        """Called externally (e.g. from face_recognition.py) to rebuild PDFs
        from the same data the table shows — most recent session per candidate."""
        import threading
        threading.Thread(target=self._build_reports, daemon=True).start()

    def _build_reports(self):
        """Builds both PDFs using exactly the same query + dedup logic as
        load_data(), so the PDF always matches what the table displays."""
        try:
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import A4

            style = getSampleStyleSheet()

            # ── Fetch rows — same query as load_data ─────────────────────────
            conn = mysql.connector.connect(**DB_CFG)
            cur  = conn.cursor()
            cur.execute("""
                SELECT id, candidate_id, name, status, timestamp
                FROM verification_log
                ORDER BY timestamp DESC
            """)
            rows = cur.fetchall()

            # ── Deduplicate: keep only most recent session per candidate ──────
            seen = set()
            unique_rows = []
            for row in rows:
                log_id, cid, name, status, ts = row
                if cid not in seen:
                    seen.add(cid)
                    unique_rows.append(row)

            # ── Pull phone + email for verified candidates from student table ─
            verified_cids = [r[1] for r in unique_rows if r[3] == "VERIFIED"]
            extras = {}
            if verified_cids:
                fmt = ",".join(["%s"] * len(verified_cids))
                cur.execute(
                    f"SELECT candidate_id, phone, email FROM student WHERE candidate_id IN ({fmt})",
                    verified_cids
                )
                extras = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
            conn.close()

            base_dir = os.path.dirname(os.path.abspath(__file__))

            # ── Authenticated PDF ────────────────────────────────────────────
            verified_rows = [r for r in unique_rows if r[3] == "VERIFIED"]
            doc = SimpleDocTemplate(os.path.join(base_dir, "authenticated_report.pdf"), pagesize=A4)
            elements = [
                Paragraph("<b>Authenticated Candidates</b>", style["Title"]),
                Spacer(1, 20)
            ]
            if verified_rows:
                data = [["Name", "Candidate ID", "Phone", "Email"]]
                for log_id, cid, name, status, ts in verified_rows:
                    phone, email = extras.get(cid, ("-", "-"))
                    data.append([name, str(cid), str(phone or "-"), email or "-"])
                tbl = Table(data, colWidths=[130, 120, 100, 160])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND',     (0, 0), (-1, 0), rl_colors.HexColor("#1E293B")),
                    ('TEXTCOLOR',      (0, 0), (-1, 0), rl_colors.white),
                    ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE',       (0, 0), (-1, -1), 8),
                    ('GRID',           (0, 0), (-1, -1), 1, rl_colors.HexColor("#CBD5E1")),
                    ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [rl_colors.white, rl_colors.HexColor("#F1F5F9")])
                ]))
                elements.append(tbl)
            else:
                elements.append(Paragraph("No authenticated records.", style["Normal"]))
            doc.build(elements)

            # ── Declined PDF ─────────────────────────────────────────────────
            declined_rows = [r for r in unique_rows if r[3] != "VERIFIED"]
            doc2 = SimpleDocTemplate(os.path.join(base_dir, "declined_report.pdf"), pagesize=A4)
            elements2 = [
                Paragraph("<b>Declined / Locked Candidates</b>", style["Title"]),
                Spacer(1, 20)
            ]
            if declined_rows:
                data2 = [["Name", "Candidate ID"]]
                for log_id, cid, name, status, ts in declined_rows:
                    data2.append([name, str(cid)])
                tbl2 = Table(data2, colWidths=[250, 160])
                tbl2.setStyle(TableStyle([
                    ('BACKGROUND',     (0, 0), (-1, 0), rl_colors.HexColor("#7F1D1D")),
                    ('TEXTCOLOR',      (0, 0), (-1, 0), rl_colors.white),
                    ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE',       (0, 0), (-1, -1), 9),
                    ('GRID',           (0, 0), (-1, -1), 1, rl_colors.HexColor("#FECACA")),
                    ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [rl_colors.white, rl_colors.HexColor("#FEF2F2")])
                ]))
                elements2.append(tbl2)
            else:
                elements2.append(Paragraph("No declined records.", style["Normal"]))
            doc2.build(elements2)

            print("Reports updated: authenticated_report.pdf, declined_report.pdf")
        except Exception as e:
            print(f"Report generation error: {e}")

    def _open_pdf(self, filename):
        path = os.path.abspath(filename)
        if not os.path.exists(path):
            messagebox.showwarning("Not Found",
                                   f"'{filename}' not found.\n\nRun an authentication session first to generate it.")
            return
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_auth_pdf(self):
        self._open_pdf("authenticated_report.pdf")

    def _open_declined_pdf(self):
        self._open_pdf("declined_report.pdf")

    def _clear_logs(self):
        confirm = messagebox.askyesno(
            "Clear All Logs",
            "Are you sure you want to permanently delete ALL verification logs and reports?\n\nThis cannot be undone."
        )
        if not confirm:
            return
        try:
            conn = mysql.connector.connect(**DB_CFG)
            cur  = conn.cursor()
            cur.execute("TRUNCATE TABLE verification_log")
            conn.commit()
            conn.close()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", str(e))
            return

        # Clear the PDF reports by regenerating them as empty
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import A4

            style = getSampleStyleSheet()

            doc1 = SimpleDocTemplate("authenticated_report.pdf", pagesize=A4)
            doc1.build([
                Paragraph("<b>Authenticated Candidates</b>", style["Title"]),
                Spacer(1, 20),
                Paragraph("No records.", style["Normal"])
            ])

            doc2 = SimpleDocTemplate("declined_report.pdf", pagesize=A4)
            doc2.build([
                Paragraph("<b>Declined / Locked Candidates</b>", style["Title"]),
                Spacer(1, 20),
                Paragraph("No records.", style["Normal"])
            ])
        except Exception as e:
            messagebox.showwarning("Report Warning", f"Logs cleared but could not reset PDFs:\n{e}")

        self.load_data()
        messagebox.showinfo("Done", "All verification logs and reports cleared.")


if __name__ == "__main__":
    root = Tk()
    ReportsViewer(root)
    root.mainloop()
